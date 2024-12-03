from ninja import Router
from ninja.errors import HttpError
from .schema_v1 import QuestionSchema
from ..models import Question, MultipleChoiceOption

router = Router()


@router.get(
    "/questions/{quiz_id}/",
    response=QuestionSchema,
    description="Fetch a question by quiz ID and index.",
)
def get_question(request, quiz_id: int, question_index: int = 0):
    try:
        questions_count = Question.objects.filter(quiz_id=quiz_id).count()

        if question_index >= questions_count or question_index < 0:
            raise HttpError(404, "No more questions")

        question = Question.objects.filter(quiz_id=quiz_id).order_by("id")[
            question_index
        ]

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

        return {
            "id": question.id,
            "text": question.text,
            "question_type": question.question_type,
            "options": options,
            "rating_min": rating_min,
            "rating_max": rating_max,
            "next_index": next_index,
            "previous_index": previous_index,
        }

    except IndexError:
        raise HttpError(404, "No more questions")
    except Question.DoesNotExist:
        raise HttpError(404, "Quiz or Question not found")
    except Exception as e:
        raise HttpError(500, f"Unexpected error: {str(e)}")