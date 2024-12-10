import uuid
from django.db import models
from users.models import User
from django.core.exceptions import ValidationError


class Quiz(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title


class Question(models.Model):
    MULTIPLE_CHOICE = "multiple_choice"  # Render checkbox in frontend
    SINGLE_CHOICE = "single_choice"  # Render radiobox in frontend
    OPEN_ENDED = "open_ended"

    QUESTION_TYPES = (
        (MULTIPLE_CHOICE, "Multiple Choice"),  # Render checkbox in frontend
        (SINGLE_CHOICE, "Single Choice"),  # Render radiobox in frontend
        (OPEN_ENDED, "Open-Ended"),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default=MULTIPLE_CHOICE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return self.question


class MultipleChoiceOption(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="multiple_choice_options",
        limit_choices_to={"question_type": Question.MULTIPLE_CHOICE},
    )
    option = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Multiple Choice Option"
        verbose_name_plural = "Multiple Choice Options"

    def __str__(self):
        return f"{self.option}"


class SingleChoiceOption(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="single_choice_options",
        limit_choices_to={"question_type": Question.SINGLE_CHOICE},
    )
    option = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Single Choice Option"
        verbose_name_plural = "Single Choice Options"

    def __str__(self):
        return f"{self.option}"


class Answer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_answers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        constraints = [
            models.UniqueConstraint(
                fields=["question", "user"], name="unique_user_answer"
            )
        ]
        indexes = [
            models.Index(fields=["question", "user"]),
        ]

    def __str__(self):
        return f"Answer to '{self.question.question}' by {self.user}"

    def clean(self):
        valid_types = {
            Question.MULTIPLE_CHOICE: hasattr(self, "multiple_choice"),
            Question.SINGLE_CHOICE: hasattr(self, "single_choice"),
            Question.OPEN_ENDED: hasattr(self, "open_ended"),
        }

        if not valid_types.get(self.question.question_type, False):
            raise ValidationError(
                f"Invalid answer type for question: {self.question.question}"
            )

        answer_types = {
            Question.MULTIPLE_CHOICE: self.multiple_choice,
            Question.SINGLE_CHOICE: self.single_choice,
            Question.OPEN_ENDED: self.open_ended,
        }

        if not answer_types.get(self.question.question_type):
            raise ValidationError(
                f"Invalid answer type for question: {self.question.question}"
            )


class MultipleChoiceAnswer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    answer = models.OneToOneField(
        Answer,
        on_delete=models.CASCADE,
        related_name="multiple_choice_answer",
    )
    selected_option = models.ManyToManyField(
        MultipleChoiceOption,
        blank=True,
    )

    class Meta:
        verbose_name = "Multiple Choice Answer"
        verbose_name_plural = "Multiple Choice Answers"

    def __str__(self):
        return f"Multiple Choice Answer: {self.selected_option}"

    def clean(self):
        if self.answer.question.question_type != Question.MULTIPLE_CHOICE:
            raise ValidationError("Invalid question type for Multiple Choice Answer.")


class SingleChoiceAnswer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    answer = models.OneToOneField(
        Answer,
        on_delete=models.CASCADE,
        related_name="single_choice_answer",
    )
    selected_option = models.ForeignKey(
        SingleChoiceOption,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Single Choice Answer"
        verbose_name_plural = "Single Choice Answers"

    def __str__(self):
        return f"Single Choice Answer: {self.selected_option.question}"

    def clean(self):
        if self.answer.question.question_type != Question.SINGLE_CHOICE:
            raise ValidationError("Invalid question type for Single Choice Answer.")


class OpenEndedAnswer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    answer = models.OneToOneField(
        Answer,
        on_delete=models.CASCADE,
        related_name="open_ended_answer",
    )
    response = models.TextField()

    class Meta:
        verbose_name = "Open Ended Answer"
        verbose_name_plural = "Open Ended Answers"

    def __str__(self):
        return f"Open-Ended Answer: {self.response}"

    def clean(self):
        if self.answer.question.question_type != Question.OPEN_ENDED:
            raise ValidationError("Invalid question type for Open Ended Answer.")
