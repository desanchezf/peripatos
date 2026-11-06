from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Attempt, Choice, Question, Quiz, Topic


class QuizApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ana")
        self.client.force_authenticate(self.user)
        self.topic = Topic.objects.create(name="Redes")
        self.quiz = Quiz.objects.create(title="TCP", topic=self.topic)
        self.q1 = Question.objects.create(quiz=self.quiz, text="¿Puerto de HTTPS?", explanation="443", order=1)
        self.right = Choice.objects.create(question=self.q1, text="443", is_correct=True)
        self.wrong = Choice.objects.create(question=self.q1, text="80")
        self.q2 = Question.objects.create(quiz=self.quiz, text="¿Capa de TCP?", order=2)
        self.q2_right = Choice.objects.create(question=self.q2, text="Transporte", is_correct=True)
        self.url = f"/api/quizzes/quizzes/{self.quiz.id}/"

    def test_list_includes_topic(self):
        item = self.client.get("/api/quizzes/quizzes/").data[0]
        self.assertEqual(item["topic"]["name"], "Redes")
        self.assertEqual(item["question_count"], 2)
        self.assertIsNone(item["best_percent"])

    def test_detail_does_not_leak_solutions(self):
        response = self.client.get(self.url)
        self.assertEqual(set(response.data["questions"][0]["choices"][0]), {"id", "text"})
        self.assertNotIn("explanation", response.data["questions"][0])

    def test_submit_scores_on_the_server(self):
        answers = {str(self.q1.id): self.right.id}  # q2 sin responder cuenta como fallo
        response = self.client.post(f"{self.url}submit/", {"answers": answers}, format="json")
        self.assertEqual((response.data["score"], response.data["total"], response.data["percent"]), (1, 2, 50))
        self.assertEqual(response.data["results"][0]["correct_choices"], [self.right.id])
        self.assertEqual(Attempt.objects.get().user, self.user)
        self.assertEqual(self.client.get("/api/quizzes/quizzes/").data[0]["best_percent"], 50)

    def test_choice_of_another_question_is_rejected(self):
        answers = {str(self.q1.id): self.q2_right.id}
        response = self.client.post(f"{self.url}submit/", {"answers": answers}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Attempt.objects.exists())

    def test_quiz_without_questions_cannot_be_submitted(self):
        empty = Quiz.objects.create(title="Vacío")
        response = self.client.post(f"/api/quizzes/quizzes/{empty.id}/submit/", {"answers": {}}, format="json")
        self.assertEqual(response.status_code, 400)
