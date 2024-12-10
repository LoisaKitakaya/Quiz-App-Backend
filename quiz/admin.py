from django.contrib import admin
from .models import (
    Quiz,
    Question,
    MultipleChoiceOption,
    SingleChoiceOption,
    Answer,
    MultipleChoiceAnswer,
    SingleChoiceAnswer,
    OpenEndedAnswer,
)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "created_at", "updated_at")
    search_fields = ("title", "description")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "quiz", "question_type", "created_at")
    list_filter = ("question_type", "quiz")
    search_fields = ("question",)
    ordering = ("-created_at",)


@admin.register(MultipleChoiceOption)
class MultipleChoiceOptionAdmin(admin.ModelAdmin):
    list_display = ("option", "question", "created_at")
    search_fields = ("option", "question__question")
    list_filter = ("question__quiz",)
    ordering = ("-created_at",)


@admin.register(SingleChoiceOption)
class SingleChoiceOptionAdmin(admin.ModelAdmin):
    list_display = ("option", "question", "created_at")
    search_fields = ("option", "question__question")
    list_filter = ("question__quiz",)
    ordering = ("-created_at",)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "user", "created_at")
    search_fields = (
        "question__question",
        "user__username",
    )  # Adjust 'username' to match your User model
    list_filter = ("question__quiz",)
    ordering = ("-created_at",)


@admin.register(MultipleChoiceAnswer)
class MultipleChoiceAnswerAdmin(admin.ModelAdmin):
    list_display = ("answer",)
    search_fields = (
        "answer__question__question",
        "answer__user__username",
    )  # Adjust 'username' to match your User model
    list_filter = ("answer__question__quiz",)


@admin.register(SingleChoiceAnswer)
class SingleChoiceAnswerAdmin(admin.ModelAdmin):
    list_display = ("answer", "selected_option")
    search_fields = (
        "answer__question__question",
        "selected_option__option",
        "answer__user__username",
    )
    list_filter = ("answer__question__quiz",)


@admin.register(OpenEndedAnswer)
class OpenEndedAnswerAdmin(admin.ModelAdmin):
    list_display = ("answer", "response")
    search_fields = ("answer__question__question", "response", "answer__user__username")
    list_filter = ("answer__question__quiz",)
