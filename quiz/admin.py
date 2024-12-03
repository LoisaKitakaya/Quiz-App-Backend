from django.contrib import admin
from .models import (
    Category,
    Quiz,
    Question,
    MultipleChoiceOption,
    Answer,
    MultipleChoiceAnswer,
    RatingScaleAnswer,
    OpenEndedAnswer,
    YesNoAnswer,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("title", "description")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "question_type", "created_at")
    list_filter = ("question_type", "quiz")
    search_fields = ("text",)
    ordering = ("-created_at",)


@admin.register(MultipleChoiceOption)
class MultipleChoiceOptionAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "created_at")
    search_fields = ("text",)
    list_filter = ("question__quiz",)
    ordering = ("-created_at",)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "user", "created_at")
    search_fields = (
        "question__text",
        "user__username",
    )  # Replace `username` with the User model's identifier field
    list_filter = ("question__quiz",)


@admin.register(MultipleChoiceAnswer)
class MultipleChoiceAnswerAdmin(admin.ModelAdmin):
    list_display = ("answer", "selected_option")
    search_fields = ("answer__question__text", "selected_option__text")
    list_filter = ("answer__question__quiz",)


@admin.register(RatingScaleAnswer)
class RatingScaleAnswerAdmin(admin.ModelAdmin):
    list_display = ("answer", "rating")
    search_fields = ("answer__question__text",)
    list_filter = ("answer__question__quiz",)


@admin.register(OpenEndedAnswer)
class OpenEndedAnswerAdmin(admin.ModelAdmin):
    list_display = ("answer", "response")
    search_fields = ("answer__question__text", "response")
    list_filter = ("answer__question__quiz",)


@admin.register(YesNoAnswer)
class YesNoAnswerAdmin(admin.ModelAdmin):
    list_display = ("answer", "response")
    search_fields = ("answer__question__text",)
    list_filter = ("answer__question__quiz",)
