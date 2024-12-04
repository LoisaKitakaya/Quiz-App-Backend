import uuid
from typing import List
from ninja import Router
from users.models import User
from ninja.errors import HttpError
from django.http import HttpResponse
from .schema_v1 import QuestionSchema, QuizSchema, AnswerInputSchema
from ..models import (
    Quiz,
    Answer,
    Question,
    YesNoAnswer,
    OpenEndedAnswer,
    RatingScaleAnswer,
    MultipleChoiceAnswer,
    MultipleChoiceOption,
)

router = Router()


@router.get(
    "/questions/{str:quiz_id}",
    response=QuestionSchema,
    description="Fetch a question by quiz ID and index.",
)
def get_question(request, quiz_id: str, question_index: int = 0):
    try:
        quiz_id = uuid.UUID(quiz_id)

        questions_count = Question.objects.filter(quiz__id=quiz_id).count()

        if question_index > questions_count or question_index < 0:
            raise HttpError(404, "No more questions")

        question = Question.objects.filter(
            quiz__id=quiz_id, quiz__is_active=True
        ).order_by("id")[question_index]

        options = (
            [
                {"id": option.id, "text": option.text}
                for option in MultipleChoiceOption.objects.filter(question=question)
            ]
            if question.question_type == "multiple_choice"
            else None
        )

        rating_min = (
            question.rating_min
            if question.question_type == Question.RATING_SCALE
            else None
        )

        rating_max = (
            question.rating_max
            if question.question_type == Question.RATING_SCALE
            else None
        )

        next_index = (
            question_index + 1 if question_index + 1 < questions_count else None
        )
        previous_index = question_index - 1 if question_index > 0 else None

        has_next = next_index is not None
        has_previous = previous_index is not None

        return {
            "id": question.id,
            "text": question.text,
            "question_type": question.question_type,
            "options": options,
            "rating_min": rating_min,
            "rating_max": rating_max,
            "next_index": next_index,
            "previous_index": previous_index,
            "has_next": has_next,
            "has_previous": has_previous,
        }

    except IndexError:
        raise HttpError(404, "No more questions")
    except Exception as e:
        raise HttpError(500, str(e))


@router.get(
    "",
    response=List[QuizSchema],
    description="Fetch all available quizzes.",
)
def get_quizzes(request):
    try:
        return list(Quiz.objects.filter(is_active=True))
    except Exception as e:
        raise HttpError(500, str(e))


def save_multiple_choice_answer(answer: Answer, selected_option: uuid.UUID):
    try:
        multiple_choice_option = MultipleChoiceOption.objects.get(id=selected_option)

        MultipleChoiceAnswer.objects.create(
            answer=answer,
            selected_option=multiple_choice_option,
        )
    except Exception as e:
        raise HttpError(500, str(e))


def save_rating_scale_answer(answer: Answer, rating: int):
    try:
        RatingScaleAnswer.objects.create(
            answer=answer,
            rating=rating,
        )
    except Exception as e:
        raise HttpError(500, str(e))


def save_open_ended_answer(answer: Answer, text: str):
    try:
        OpenEndedAnswer.objects.create(
            answer=answer,
            response=text,
        )
    except Exception as e:
        raise HttpError(500, str(e))


def save_yes_no_answer(answer: Answer, choice: bool):
    try:
        YesNoAnswer.objects.create(
            answer=answer,
            response=choice,
        )
    except Exception as e:
        raise HttpError(500, str(e))


@router.post(
    "/submit-answer",
    # response=HttpResponse,
    description="Submit an answer",
)
def submit_answer(request, data: AnswerInputSchema):
    try:
        question_id = uuid.UUID(data.question_id)
        
        selected_option = (
            uuid.UUID(data.selected_option) if data.selected_option else None
        )

        user = User.objects.get(username=data.username)

        question = Question.objects.get(id=question_id)

        answer = Answer.objects.create(
            question=question,
            user=user,
        )

        if question.question_type == Question.MULTIPLE_CHOICE:
            save_multiple_choice_answer(answer, selected_option)
        elif question.question_type == Question.RATING_SCALE:
            save_rating_scale_answer(answer, data.rating)
        elif question.question_type == Question.OPEN_ENDED:
            save_open_ended_answer(answer, data.text)
        elif question.question_type == Question.YES_NO:
            save_yes_no_answer(answer, data.choice)

        return HttpResponse("Ok", status=200)

    except Exception as e:
        raise HttpError(500, str(e))
