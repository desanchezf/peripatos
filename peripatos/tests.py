from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient, APITestCase


# Caché en memoria: el límite de intentos de login no debe arrastrarse entre ejecuciones
@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class AuthApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user("ana", password="clave-segura-1")

    def test_me_without_session_is_401(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_login_and_me(self):
        response = self.client.post("/api/auth/login/", {"username": "ana", "password": "clave-segura-1"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").data["username"], "ana")

    def test_wrong_password_is_rejected(self):
        response = self.client.post("/api/auth/login/", {"username": "ana", "password": "mala"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_login_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        response = client.post("/api/auth/login/", {"username": "ana", "password": "clave-segura-1"}, format="json")
        self.assertEqual(response.status_code, 403)


class BackendThemeTests(TestCase):
    def test_theme_files_exist(self):
        # Con el almacenamiento de producción, un {% static %} sin fichero rompe la página con un 500
        for path in ["nt/tokens.css", "peripatos-admin/admin.css", "peripatos-admin/admin.js", "peripatos-admin/api.css", "logo/peripatos.svg"]:
            self.assertIsNotNone(finders.find(path), path)

    def test_login_uses_theme(self):
        response = self.client.get("/admin/login/")
        self.assertContains(response, "nt/tokens.css")
        self.assertContains(response, "peripatos-admin/admin.css")

    def test_admin_uses_theme(self):
        self.client.force_login(get_user_model().objects.create_superuser("ana", password="clave-segura-1"))
        response = self.client.get("/admin/")
        self.assertContains(response, "nt/tokens.css")
        self.assertContains(response, "peripatos-admin/admin.css")

    def test_browsable_api_uses_theme(self):
        self.client.force_login(get_user_model().objects.create_user("ana", password="clave-segura-1"))
        response = self.client.get("/api/auth/me/", headers={"accept": "text/html"})
        self.assertContains(response, "nt/tokens.css")
        self.assertContains(response, "peripatos-admin/api.css")
