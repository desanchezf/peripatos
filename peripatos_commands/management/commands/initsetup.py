from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea los superusuarios y grupos base. Es idempotente."

    def handle(self, *args, **kwargs):
        self.create_superuser(settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, "ADMIN_PASSWORD", settings.ADMIN_EMAIL)
        self.create_superuser("david", settings.MAIN_USER_PASS, "MAIN_USER_PASS")
        self.create_groups_and_permissions()
        self.stdout.write(self.style.SUCCESS("Groups ready ✅"))
        self.add_to_admin_group(settings.ADMIN_USERNAME, "david")

    def add_to_admin_group(self, *usernames):
        users = get_user_model().objects.filter(username__in=usernames)
        Group.objects.get(name="admin").user_set.add(*users)
        self.stdout.write(self.style.SUCCESS(f"Added to group 'admin': {', '.join(usernames)} ✅"))

    def create_superuser(self, username, password, password_var, email=""):
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' already exists, skipping")
            return

        # Una contraseña vacía crearía una cuenta de superusuario sin protección real
        if not password:
            raise CommandError(f"{password_var} is not set: cannot create superuser '{username}'")

        User.objects.create_superuser(username, email, password)
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created ✅"))

    def create_groups_and_permissions(self):
        for group in settings.ADMIN_GROUPS:
            Group.objects.get_or_create(name=group)

        for role_name, permissions in settings.ROLE_PERMISSIONS.items():
            role, _ = Group.objects.get_or_create(name=role_name)
            for item in permissions:
                content_type = ContentType.objects.get(app_label=item["app_label"], model=item["model"])
                for permission in item["permissions"]:
                    # NOTE: If it exists, it is not added (there is no error)
                    role.permissions.add(
                        Permission.objects.get(
                            codename=f"{permission}_{item['model']}",
                            content_type=content_type,
                        )
                    )
