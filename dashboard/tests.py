from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from labs.models import Lab
from quizzes.models import Attempt, Choice, Question, Quiz
from roadmap.models import Training, TrainingStep
from theory.models import Material, ReadingProgress

from .models import Notice


class DashboardApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.ana = User.objects.create_user("ana")
        self.luis = User.objects.create_user("luis")
        self.client.force_authenticate(self.ana)

    def get(self):
        return self.client.get("/api/dashboard/").data

    def test_empty_platform(self):
        data = self.get()
        self.assertEqual(data["metrics"]["readings"]["pending"], 0)
        self.assertEqual(data["metrics"]["trainings"]["percent"], 0)
        self.assertIsNone(data["metrics"]["average_score"])
        self.assertEqual(data["notices"], [])

    def test_pending_readings_put_started_first_and_skip_finished(self):
        Material.objects.create(title="A nueva")
        started = Material.objects.create(title="B empezada")
        finished = Material.objects.create(title="C leída")
        ReadingProgress.objects.create(user=self.ana, material=started, percent=30)
        ReadingProgress.objects.create(user=self.ana, material=finished, percent=100, finished_at=timezone.now())

        data = self.get()
        self.assertEqual([item["title"] for item in data["pending_readings"]], ["B empezada", "A nueva"])
        self.assertEqual(data["metrics"]["readings"], {"pending": 2, "in_progress": 1, "finished": 1, "total": 3})

    def test_pending_quizzes_and_average_are_per_user(self):
        quiz = Quiz.objects.create(title="Con preguntas")
        Choice.objects.create(question=Question.objects.create(quiz=quiz, text="?"), text="a", is_correct=True)
        Quiz.objects.create(title="Vacío")
        Attempt.objects.create(user=self.luis, quiz=quiz, score=1, total=1)
        self.assertEqual([item["title"] for item in self.get()["pending_quizzes"]], ["Con preguntas"])

        Attempt.objects.create(user=self.ana, quiz=quiz, score=1, total=4)
        data = self.get()
        self.assertEqual(data["pending_quizzes"], [])
        self.assertEqual(data["metrics"]["average_score"], 25)

    def test_overdue_training_and_due_lab_raise_notices(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        training = Training.objects.create(title="Backend", target_date=yesterday)
        TrainingStep.objects.create(training=training, material=Material.objects.create(title="L"))
        Lab.objects.create(title="Lab", due_date=timezone.localdate() + timedelta(days=2))
        Lab.objects.create(title="Lejano", due_date=timezone.localdate() + timedelta(days=60))
        links = [notice["link"] for notice in self.get()["notices"]]
        self.assertIn(f"/roadmap/{training.id}", links)
        self.assertEqual(len(links), 2)

    def test_dismissal_only_affects_the_user(self):
        notice = Notice.objects.create(title="Hola")
        self.assertEqual(self.client.post(f"/api/dashboard/notices/{notice.id}/dismiss/").status_code, 204)
        self.assertEqual(self.get()["notices"], [])
        self.client.force_authenticate(self.luis)
        self.assertEqual(len(self.get()["notices"]), 1)
