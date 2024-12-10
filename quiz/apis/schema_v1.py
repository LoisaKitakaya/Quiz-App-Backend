import uuid
from ..models import Quiz
from ninja import Schema, ModelSchema
from typing import Optional, Union, List


class OptionSchema(Schema):
    id: uuid.UUID
    option: str


class QuestionSchema(Schema):
    id: uuid.UUID
    question: str
    question_type: str
    options: Optional[list[OptionSchema]] = None
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
    selected_option: Optional[Union[str, List[str]]] = None
    text: Optional[str] = None


class AnswerSchema(Schema):
    question_id: uuid.UUID
    question_text: str
    question_type: str
    answer: Union[None, str, int, List[str]]


class QuizResponseSchema(Schema):
    quiz_id: uuid.UUID
    quiz_title: str
    questions: List[AnswerSchema]


class UserQuizInputSchema(Schema):
    username: str
    quiz_id: uuid.UUID
