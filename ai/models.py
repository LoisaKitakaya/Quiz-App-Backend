import uuid
from django.db import models
from quiz.models import Quiz
from users.models import User
from django.core.serializers.json import DjangoJSONEncoder


class ModelAnalysisResult(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_analysis",
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="quiz_analysis",
    )
    analysis = models.JSONField(
        encoder=DjangoJSONEncoder,
        help_text="JSON field storing the analysis result.",
        null=False,
        blank=False,
    )
    metadata = models.JSONField(
        encoder=DjangoJSONEncoder,
        help_text="Optional metadata about the analysis.",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Model Analysis Result"
        verbose_name_plural = "Model Analysis Results"
        indexes = [
            models.Index(fields=["user"], name="idx_user"),
        ]

    def __str__(self):
        return f"AI analysis results for {self.user.username}"
