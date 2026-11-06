from datetime import timedelta

from django.db.models import Avg, Count, F, FloatField
from django.db.models.functions import Cast
from django.utils import timezone

from labs.models import Lab, Submission
from quizzes.models import Attempt, Quiz
from roadmap.services import build_roadmaps
from theory.models import Material, ReadingProgress

from .models import Notice

DUE_SOON_DAYS = 7
RECENT_REVIEW_DAYS = 14


def _notices(user, roadmaps, submitted_labs):
    today = timezone.localdate()
    notices = [
        {"id": f"notice-{n.id}", "notice_id": n.id, "title": n.title, "body": n.body, "level": n.level, "link": None}
        for n in Notice.objects.filter(active=True).exclude(dismissed_by=user)
    ]
    for roadmap in roadmaps:
        target = roadmap["target_date"]
        if target and target < today and not roadmap["completed"]:
            notices.append(
                {
                    "id": f"training-{roadmap['id']}",
                    "notice_id": None,
                    "title": f"Formación fuera de plazo: {roadmap['title']}",
                    "body": f"La fecha objetivo era el {target:%d/%m/%Y}.",
                    "level": "warning",
                    "link": f"/roadmap/{roadmap['id']}",
                }
            )
    labs = Lab.objects.filter(due_date__lte=today + timedelta(days=DUE_SOON_DAYS)).exclude(id__in=submitted_labs)
    for lab in labs:
        late = lab.due_date < today
        notices.append(
            {
                "id": f"lab-{lab.id}",
                "notice_id": None,
                "title": f"Laboratorio {'fuera de plazo' if late else 'por entregar'}: {lab.title}",
                "body": f"Fecha límite: {lab.due_date:%d/%m/%Y}.",
                "level": "warning",
                "link": f"/labs/{lab.id}",
            }
        )
    reviewed = Submission.objects.filter(
        user=user, status=Submission.Status.REVIEWED, reviewed_at__gte=timezone.now() - timedelta(days=RECENT_REVIEW_DAYS)
    ).select_related("lab")
    for submission in reviewed:
        notices.append(
            {
                "id": f"submission-{submission.id}",
                "notice_id": None,
                "title": f"Entrega revisada: {submission.lab.title}",
                "body": "",
                "level": "info",
                "link": f"/labs/{submission.lab_id}",
            }
        )
    return notices


def build_dashboard(user):
    roadmaps = build_roadmaps(user)
    pending_trainings = [roadmap for roadmap in roadmaps if not roadmap["completed"]]

    materials = list(Material.objects.all())
    progress = {p.material_id: p for p in ReadingProgress.objects.filter(user=user)}
    pending_readings = [m for m in materials if m.id not in progress or progress[m.id].finished_at is None]
    # Primero lo empezado, y lo último que se leyó antes
    pending_readings.sort(key=lambda m: (progress[m.id].updated_at.timestamp() * -1 if m.id in progress else 0, m.title))

    quizzes = Quiz.objects.select_related("topic").annotate(question_count=Count("questions")).filter(question_count__gt=0)
    attempted = set(Attempt.objects.filter(user=user).values_list("quiz_id", flat=True))
    pending_quizzes = [quiz for quiz in quizzes if quiz.id not in attempted]
    average = Attempt.objects.filter(user=user, total__gt=0).aggregate(
        value=Avg(Cast(F("score"), FloatField()) * 100 / F("total"))
    )["value"]

    submitted_labs = set(Submission.objects.filter(user=user).values_list("lab_id", flat=True))
    total_labs = Lab.objects.count()  # una entrega cuenta aunque se reenvíe varias veces

    finished = len(materials) - len(pending_readings)
    in_progress = sum(1 for m in pending_readings if m.id in progress and progress[m.id].percent > 0)
    total_steps = sum(roadmap["total_steps"] for roadmap in roadmaps)
    done_steps = sum(roadmap["done_steps"] for roadmap in roadmaps)

    return {
        "metrics": {
            "readings": {"pending": len(pending_readings), "in_progress": in_progress, "finished": finished, "total": len(materials)},
            "trainings": {"pending": len(pending_trainings), "total": len(roadmaps), "percent": round(100 * done_steps / total_steps) if total_steps else 0},
            "quizzes": {"pending": len(pending_quizzes), "total": len(quizzes)},
            "labs": {"pending": total_labs - len(submitted_labs), "total": total_labs},
            "average_score": round(average) if average is not None else None,
        },
        "notices": _notices(user, roadmaps, submitted_labs),
        "pending_quizzes": [
            {"id": quiz.id, "title": quiz.title, "topic": quiz.topic.name if quiz.topic else None, "question_count": quiz.question_count}
            for quiz in pending_quizzes
        ],
        "pending_readings": [
            {"id": m.id, "title": m.title, "kind_label": m.get_kind_display(), "format": m.format, "percent": progress[m.id].percent if m.id in progress else 0}
            for m in pending_readings
        ],
    }
