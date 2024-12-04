import uuid
from ..models import Quiz
from typing import Optional
from ninja import Schema, ModelSchema


class OptionSchema(Schema):
    id: uuid.UUID
    text: str


class QuestionSchema(Schema):
    id: uuid.UUID
    text: str
    question_type: str
    options: Optional[list[OptionSchema]] = None
    rating_min: Optional[int] = None
    rating_max: Optional[int] = None
    next_index: Optional[int] = None
    previous_index: Optional[int] = None
    has_next: bool
    has_previous: bool


class QuizSchema(ModelSchema):
    class Meta:
        model = Quiz
        exclude = [
            "created_at",
            "updated_at",
        ]


class AnswerInputSchema(Schema):
    username: str
    question_id: str
    selected_option: Optional[str] = None
    rating: Optional[int] = None
    text: Optional[str] = None
    choice: Optional[bool] = None
