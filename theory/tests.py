from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from peripatos.test_utils import TemporaryPrivateStorage

from .models import Material, Note


class TheoryApiTests(TemporaryPrivateStorage, APITestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.ana = User.objects.create_user("ana")
        self.luis = User.objects.create_user("luis")
        self.material = Material.objects.create(title="Libro", kind="reading")
        self.client.force_authenticate(self.ana)
        self.url = f"/api/theory/materials/{self.material.id}/"

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/theory/materials/").status_code, 403)

    def test_progress_is_saved_per_user(self):
        response = self.client.patch(f"{self.url}progress/", {"location": "12", "percent": 40}, format="json")
        self.assertEqual(response.data["progress"]["location"], "12")
        self.assertFalse(response.data["progress"]["finished"])

        self.client.force_authenticate(self.luis)
        self.assertEqual(self.client.get(self.url).data["progress"]["location"], "")

    def test_reaching_the_end_finishes_and_can_be_undone(self):
        response = self.client.patch(f"{self.url}progress/", {"percent": 100}, format="json")
        self.assertTrue(response.data["progress"]["finished"])
        response = self.client.patch(f"{self.url}progress/", {"finished": False}, format="json")
        self.assertFalse(response.data["progress"]["finished"])

    def test_percent_out_of_range_is_rejected(self):
        response = self.client.patch(f"{self.url}progress/", {"percent": 101}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_notes_of_other_users_are_not_accessible(self):
        note = Note.objects.create(user=self.luis, material=self.material, text="privada")
        self.assertEqual(self.client.get("/api/theory/notes/").data, [])
        self.assertEqual(self.client.delete(f"/api/theory/notes/{note.id}/").status_code, 404)

    def test_note_is_created_for_the_session_user(self):
        response = self.client.post("/api/theory/notes/", {"material": self.material.id, "text": "idea", "location": "3"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Note.objects.get(id=response.data["id"]).user, self.ana)

    def test_only_pdf_and_epub_files_are_valid(self):
        material = Material(title="Malo", file=SimpleUploadedFile("malo.html", b"<script>"))
        with self.assertRaises(ValidationError):
            material.full_clean()

    def test_file_is_served_to_authenticated_users_only(self):
        self.material.file.save("libro.pdf", ContentFile(b"%PDF-1.4"))

        response = self.client.get(f"{self.url}file/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        b"".join(response.streaming_content)

        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f"{self.url}file/").status_code, 403)
