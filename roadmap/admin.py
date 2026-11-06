from django.contrib import admin

from .models import CareerPath, PathNode, PathStage, Training, TrainingStep


class TrainingStepInline(admin.TabularInline):
    model = TrainingStep
    extra = 1


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ["title", "target_date", "order"]
    search_fields = ["title", "description"]
    inlines = [TrainingStepInline]


class PathStageInline(admin.TabularInline):
    model = PathStage
    extra = 1
    fields = ["title", "order"]
    show_change_link = True


@admin.register(CareerPath)
class CareerPathAdmin(admin.ModelAdmin):
    list_display = ["title", "published", "order"]
    list_filter = ["published"]
    search_fields = ["title", "summary"]
    inlines = [PathStageInline]


class PathNodeInline(admin.StackedInline):
    model = PathNode
    extra = 1


@admin.register(PathStage)
class PathStageAdmin(admin.ModelAdmin):
    list_display = ["title", "path", "order"]
    list_filter = ["path"]
    inlines = [PathNodeInline]
