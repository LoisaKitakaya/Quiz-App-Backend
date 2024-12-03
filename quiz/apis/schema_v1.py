import uuid
from ninja import Schema
from typing import Optional


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
