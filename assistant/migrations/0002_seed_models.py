from django.db import migrations

MODELS = [
    ("claude-opus-5-5", "Claude Opus 5.5"),
    ("claude-sonnet-5-5", "Claude Sonnet 5.5"),
    ("claude-haiku-5-5", "Claude Haiku 5.5"),
]


def seed(apps, schema_editor):
    LLMModel = apps.get_model("assistant", "LLMModel")
    for position, (name, display_name) in enumerate(MODELS):
        LLMModel.objects.get_or_create(provider="anthropic", name=name, defaults={"display_name": display_name, "position": position})


class Migration(migrations.Migration):
    dependencies = [("assistant", "0001_initial")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
