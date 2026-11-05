from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        created_superuser, error_superuser = self.create_superuser()
        # created_groups, error_groups = self.create_groups_and_permissions()

        if not error_superuser:
            self.stdout.write(self.style.SUCCESS("Superuser created successfully ✅"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser already exists ❌ ({error_superuser})"))

        # if not error_groups:
        #     self.stdout.write(self.style.SUCCESS("Groups created successfully ✅"))
        # else:
        #     self.stdout.write(self.style.WARNING(f"Groups already exist ❌ ({error_groups})"))

    def create_superuser(self):
        try:
            User = get_user_model()
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser(
                    "admin",  # USERNAME
                    "admin@sanbox.org",  # MAIL
                    "admin",  # PASS
                )
                return True, None
            return False, "Usuario ya existe"
        except Exception as e:
            return False, str(e)

    def create_groups_and_permissions(self):
        try:
            for group in settings.ADMIN_GROUPS:
                Group.objects.get_or_create(name=group)

            role_permissions = settings.ROLE_PERMISSIONS

            for role_permission, permissions in role_permissions.items():
                role, created = Group.objects.get_or_create(name=role_permission)
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
            role.save()
            return True, None
        except Exception as e:
            return False, str(e)
