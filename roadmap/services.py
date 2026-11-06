from labs.models import Submission
from quizzes.models import Attempt
from theory.models import ReadingProgress

from .models import Training


def build_roadmaps(user):
    """Formaciones con sus pasos y el avance del usuario, calculado de lo que ha hecho."""
    read = set(ReadingProgress.objects.filter(user=user, finished_at__isnull=False).values_list("material_id", flat=True))
    attempted = set(Attempt.objects.filter(user=user).values_list("quiz_id", flat=True))
    submitted = set(Submission.objects.filter(user=user).values_list("lab_id", flat=True))

    roadmaps = []
    trainings = Training.objects.prefetch_related("steps__material", "steps__quiz", "steps__lab")
    for training in trainings:
        steps = []
        for step in training.steps.all():
            if step.material_id:
                item = {"type": "reading", "item_id": step.material_id, "title": step.material.title, "done": step.material_id in read}
            elif step.quiz_id:
                item = {"type": "quiz", "item_id": step.quiz_id, "title": step.quiz.title, "done": step.quiz_id in attempted}
            else:
                item = {"type": "lab", "item_id": step.lab_id, "title": step.lab.title, "done": step.lab_id in submitted}
            steps.append({"id": step.id, **item})

        done = sum(step["done"] for step in steps)
        roadmaps.append(
            {
                "id": training.id,
                "title": training.title,
                "description": training.description,
                "target_date": training.target_date,
                "steps": steps,
                "done_steps": done,
                "total_steps": len(steps),
                "percent": round(100 * done / len(steps)) if steps else 0,
                "completed": bool(steps) and done == len(steps),
            }
        )
    return roadmaps
