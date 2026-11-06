from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from quizzes.models import Attempt, Quiz
from theory.models import Material, ReadingProgress

from .models import CareerPath, PathNode, PathStage, Training, TrainingStep


class RoadmapApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.ana = User.objects.create_user("ana")
        self.luis = User.objects.create_user("luis")
        self.client.force_authenticate(self.ana)
        self.material = Material.objects.create(title="Libro")
        self.quiz = Quiz.objects.create(title="Test")
        self.training = Training.objects.create(title="Backend")
        TrainingStep.objects.create(training=self.training, order=1, material=self.material)
        TrainingStep.objects.create(training=self.training, order=2, quiz=self.quiz)
        self.other = Training.objects.create(title="Frontend")

    def test_each_training_has_its_own_ordered_steps(self):
        data = self.client.get(f"/api/roadmap/trainings/{self.training.id}/").data
        self.assertEqual([step["title"] for step in data["steps"]], ["Libro", "Test"])
        self.assertEqual(self.client.get(f"/api/roadmap/trainings/{self.other.id}/").data["steps"], [])

    def test_progress_is_computed_per_user(self):
        ReadingProgress.objects.create(user=self.ana, material=self.material, finished_at=timezone.now())
        data = self.client.get(f"/api/roadmap/trainings/{self.training.id}/").data
        self.assertEqual((data["done_steps"], data["percent"], data["completed"]), (1, 50, False))

        Attempt.objects.create(user=self.ana, quiz=self.quiz, score=0, total=1)
        self.assertTrue(self.client.get(f"/api/roadmap/trainings/{self.training.id}/").data["completed"])

        self.client.force_authenticate(self.luis)
        self.assertEqual(self.client.get(f"/api/roadmap/trainings/{self.training.id}/").data["done_steps"], 0)

    def test_unknown_training_is_404(self):
        self.assertEqual(self.client.get("/api/roadmap/trainings/999999/").status_code, 404)

    def test_step_must_link_exactly_one_item(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            TrainingStep.objects.create(training=self.training)
        with self.assertRaises(IntegrityError), transaction.atomic():
            TrainingStep.objects.create(training=self.training, material=self.material, quiz=self.quiz)


class CareerPathApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.ana = User.objects.create_user("ana")
        self.luis = User.objects.create_user("luis")
        self.client.force_authenticate(self.ana)
        self.path = CareerPath.objects.create(title="Backend")
        stage = PathStage.objects.create(path=self.path, title="Fundamentos")
        self.node = PathNode.objects.create(stage=stage, title="Python", material=Material.objects.create(title="Libro"))
        self.alternative = PathNode.objects.create(stage=stage, title="Go", kind="alternative")
        self.url = f"/api/roadmap/paths/{self.path.id}/"

    def set_status(self, node, value):
        return self.client.put(f"/api/roadmap/nodes/{node.id}/progress/", {"status": value}, format="json")

    def test_unpublished_paths_are_hidden(self):
        hidden = CareerPath.objects.create(title="Borrador", published=False)
        self.assertEqual([p["title"] for p in self.client.get("/api/roadmap/paths/").data], ["Backend"])
        self.assertEqual(self.client.get(f"/api/roadmap/paths/{hidden.id}/").status_code, 404)

    def test_choosing_and_leaving_a_path_is_per_user(self):
        self.assertTrue(self.client.post(f"{self.url}enrollment/").data["enrolled"])
        self.client.force_authenticate(self.luis)
        self.assertFalse(self.client.get(self.url).data["enrolled"])
        self.client.force_authenticate(self.ana)
        self.assertFalse(self.client.delete(f"{self.url}enrollment/").data["enrolled"])

    def test_progress_requires_choosing_the_path(self):
        self.assertEqual(self.set_status(self.node, "done").status_code, 400)

    def test_skipped_alternative_does_not_block_completion(self):
        self.client.post(f"{self.url}enrollment/")
        self.assertEqual(self.set_status(self.node, "done").status_code, 200)
        self.assertEqual(self.client.get(self.url).data["percent"], 50)
        self.set_status(self.alternative, "skipped")
        data = self.client.get(self.url).data
        self.assertEqual(data["percent"], 100)
        self.assertEqual(data["stages"][0]["nodes"][0]["links"][0]["to"], f"/readings/{self.node.material_id}")

    def test_invalid_status_is_rejected(self):
        self.client.post(f"{self.url}enrollment/")
        self.assertEqual(self.set_status(self.node, "regular").status_code, 400)

    def test_progress_survives_leaving_the_path(self):
        self.client.post(f"{self.url}enrollment/")
        self.set_status(self.node, "done")
        self.client.delete(f"{self.url}enrollment/")
        self.client.post(f"{self.url}enrollment/")
        self.assertEqual(self.client.get(self.url).data["done_nodes"], 1)
