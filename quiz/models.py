import uuid
from django.db import models
from users.models import User
from django.core.exceptions import ValidationError


class Category(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Quiz(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return self.title


class Question(models.Model):
    MULTIPLE_CHOICE = "multiple_choice"
    RATING_SCALE = "rating_scale"
    OPEN_ENDED = "open_ended"
    YES_NO = "yes_no"

    QUESTION_TYPES = (
        (MULTIPLE_CHOICE, "Multiple Choice"),
        (RATING_SCALE, "Rating Scale"),
        (OPEN_ENDED, "Open-Ended"),
        (YES_NO, "Yes/No"),
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
    text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default=MULTIPLE_CHOICE,
    )
    rating_min = models.IntegerField(
        blank=True,
        null=True,
        help_text="Minimum value for rating scale questions (e.g., 1 for Strongly Disagree)",
    )
    rating_max = models.IntegerField(
        blank=True,
        null=True,
        help_text="Maximum value for rating scale questions (e.g., 5 for Strongly Agree)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return self.text

    def clean(self):
        if self.question_type == Question.RATING_SCALE and (
            self.rating_min is None or self.rating_max is None
        ):
            raise ValidationError(
                "Rating scale questions must have rating_min and rating_max defined."
            )


class MultipleChoiceOption(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
        limit_choices_to={"question_type": Question.MULTIPLE_CHOICE},
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Multiple Choice Option"
        verbose_name_plural = "Multiple Choice Options"

    def __str__(self):
        return f"{self.text}"


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
        related_name="answers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Answer"
        verbose_name_plural = "Answers"

    def __str__(self):
        return f"Answer to '{self.question.text}' by {self.user}"

    def clean(self):
        valid_types = {
            Question.MULTIPLE_CHOICE: hasattr(self, "multiple_choice"),
            Question.RATING_SCALE: hasattr(self, "rating_scale"),
            Question.OPEN_ENDED: hasattr(self, "open_ended"),
            Question.YES_NO: hasattr(self, "yes_no"),
        }
        if not valid_types.get(self.question.question_type, False):
            raise ValidationError(
                f"Invalid answer type for question: {self.question.text}"
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
        related_name="multiple_choice",
    )
    selected_option = models.ForeignKey(
        MultipleChoiceOption,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Multiple Choice Answer"
        verbose_name_plural = "Multiple Choice Answers"

    def __str__(self):
        return f"Multiple Choice Answer: {self.selected_option.text}"

    def clean(self):
        if self.answer.question.question_type != Question.MULTIPLE_CHOICE:
            raise ValidationError("Invalid question type for Multiple Choice Answer.")


class RatingScaleAnswer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    answer = models.OneToOneField(
        Answer,
        on_delete=models.CASCADE,
        related_name="rating_scale",
    )
    rating = models.IntegerField()

    class Meta:
        verbose_name = "Rating Scale Answer"
        verbose_name_plural = "Rating Scale Answers"

    def __str__(self):
        return f"Rating: {self.rating}"

    def clean(self):
        if self.answer.question.question_type != Question.RATING_SCALE:
            raise ValidationError("Invalid question type for Rating Scale Answer.")

        if not (
            self.answer.question.rating_min
            <= self.rating
            <= self.answer.question.rating_max
        ):
            raise ValidationError("Rating must be within the question's defined range.")


class OpenEndedAnswer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    answer = models.OneToOneField(
        Answer,
        on_delete=models.CASCADE,
        related_name="open_ended",
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


class YesNoAnswer(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    answer = models.OneToOneField(
        Answer,
        on_delete=models.CASCADE,
        related_name="yes_no",
    )
    response = models.BooleanField()

    class Meta:
        verbose_name = "Yes/No Answer"
        verbose_name_plural = "Yes/No Answers"

    def __str__(self):
        return f"Yes/No Answer: {'Yes' if self.response else 'No'}"

    def clean(self):
        if self.answer.question.question_type != Question.YES_NO:
            raise ValidationError("Invalid question type for Yes/No Answer.")
