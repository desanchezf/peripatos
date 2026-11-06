from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from peripatos.test_utils import TemporaryPrivateStorage

from .models import Lab, Submission


class LabApiTests(TemporaryPrivateStorage, APITestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.ana = User.objects.create_user("ana")
        self.luis = User.objects.create_user("luis")
        self.lab = Lab.objects.create(title="Lab 1", statement="Haz X", theory="Porque Y")
        self.client.force_authenticate(self.ana)

    def upload(self, name="solucion.py", content=b"print(1)"):
        return self.client.post(
            "/api/labs/submissions/",
            {"lab": self.lab.id, "file": SimpleUploadedFile(name, content), "comment": "hecho"},
            format="multipart",
        )

    def test_lab_exposes_statement_and_theory(self):
        data = self.client.get(f"/api/labs/labs/{self.lab.id}/").data
        self.assertEqual((data["statement"], data["theory"], data["submissions"]), ("Haz X", "Porque Y", []))

    def test_upload_belongs_to_the_session_user(self):
        response = self.upload()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["file_name"], "solucion.py")
        self.assertEqual(response.data["status"], "submitted")
        self.assertEqual(Submission.objects.get().user, self.ana)

    def test_student_cannot_set_review_fields(self):
        response = self.client.post(
            "/api/labs/submissions/",
            {"lab": self.lab.id, "file": SimpleUploadedFile("a.py", b"x"), "status": "reviewed", "feedback": "10"},
            format="multipart",
        )
        self.assertEqual((response.data["status"], response.data["feedback"]), ("submitted", ""))

    def test_oversized_solution_is_rejected(self):
        with mock.patch("labs.models.MAX_SOLUTION_SIZE", 4):
            self.assertEqual(self.upload(content=b"12345").status_code, 400)
        self.assertFalse(Submission.objects.exists())

    def test_submission_of_another_user_is_hidden(self):
        submission_id = self.upload().data["id"]
        self.client.force_authenticate(self.luis)
        self.assertEqual(self.client.get("/api/labs/submissions/").data, [])
        self.assertEqual(self.client.get(f"/api/labs/submissions/{submission_id}/file/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/labs/labs/{self.lab.id}/").data["submissions"], [])

    def test_solution_downloads_as_attachment(self):
        submission_id = self.upload(name="pagina.html", content=b"<script>").data["id"]
        response = self.client.get(f"/api/labs/submissions/{submission_id}/file/")
        self.assertIn("attachment", response["Content-Disposition"])
        b"".join(response.streaming_content)
