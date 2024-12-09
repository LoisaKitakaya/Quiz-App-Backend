import uuid
import json
from typing import List
from ninja import Router
from users.models import User
from utils.ai import ai_analysis
from django.db import transaction
from ninja.errors import HttpError
from ai.models import ModelAnalysisResult
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .schema_v1 import (
    QuizSchema,
    QuestionSchema,
    AnswerInputSchema,
    UserQuizInputSchema,
)
from ..models import (
    Quiz,
    Answer,
    Question,
    OpenEndedAnswer,
    SingleChoiceAnswer,
    SingleChoiceOption,
    MultipleChoiceAnswer,
    MultipleChoiceOption,
)

router = Router()


@router.get(
    "",
    response=QuizSchema,
    description="Fetch main quiz.",
)
def get_quiz(request):
    try:
        return Quiz.objects.filter(is_active=True).first()
    except Exception as e:
        raise HttpError(500, str(e))


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

        question = Question.objects.filter(quiz__id=quiz_id).order_by("id")[
            question_index
        ]

        options = (
            [
                {"id": option.id, "text": option.option}
                for option in MultipleChoiceOption.objects.filter(question=question)
            ]
            if question.question_type == Question.MULTIPLE_CHOICE
            else (
                [
                    {"id": option.id, "text": option.option}
                    for option in SingleChoiceOption.objects.filter(question=question)
                ]
                if question.question_type == Question.SINGLE_CHOICE
                else None
            )
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
            "next_index": next_index,
            "previous_index": previous_index,
            "has_next": has_next,
            "has_previous": has_previous,
        }

    except IndexError:
        raise HttpError(404, "No more questions")
    except Exception as e:
        raise HttpError(500, str(e))


def save_multiple_choice_answer(answer: Answer, selected_option: List[uuid.UUID]):
    try:
        question = answer.question

        options = MultipleChoiceOption.objects.filter(id__in=selected_option)

        for option in options:
            if option.question != question:
                raise ValidationError(
                    f"Option {option.id} does not belong to question {question.id}."
                )

        with transaction.atomic():
            multiple_choice_answer = MultipleChoiceAnswer.objects.create(
                answer=answer,
            )
            multiple_choice_answer.selected_option.add(*options)

    except Exception as e:
        raise HttpError(500, str(e))


def save_single_choice_answer(answer: Answer, selected_option: uuid.UUID):
    try:
        single_choice_option = SingleChoiceOption.objects.get(id=selected_option)

        if single_choice_option.question != answer.question:
            raise ValidationError(
                f"Option {single_choice_option.id} does not belong to question {answer.question.id}."
            )

        with transaction.atomic():
            SingleChoiceAnswer.objects.create(
                answer=answer,
                selected_option=single_choice_option,
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


@router.post(
    "/submit-answer",
    response=dict,
    description="Submit an answer",
)
def submit_answer(request, data: AnswerInputSchema):
    try:
        question_id = uuid.UUID(data.question_id)

        question = Question.objects.get(id=question_id)
        user = User.objects.get(username=data.username)

        if data.selected_option:
            if isinstance(data.selected_option, str):
                selected_option = uuid.UUID(data.selected_option)
            elif isinstance(data.selected_option, list):
                selected_option = [uuid.UUID(option) for option in data.selected_option]
            else:
                raise ValueError(
                    "Invalid format for selected_option. Must be a string or a list of strings."
                )
        else:
            selected_option = None

        existing_answer = Answer.objects.filter(question=question, user=user).first()

        if existing_answer:
            existing_answer.delete()

        answer = Answer.objects.create(
            question=question,
            user=user,
        )

        if question.question_type == Question.MULTIPLE_CHOICE:
            if not isinstance(selected_option, list):
                raise ValueError(
                    "Multiple choice answers require a list of selected options."
                )

            save_multiple_choice_answer(answer, selected_option)
        elif question.question_type == Question.SINGLE_CHOICE:
            if not isinstance(selected_option, uuid.UUID):
                raise ValueError(
                    "Single choice answers require a single selected option."
                )

            save_single_choice_answer(answer, selected_option)
        elif question.question_type == Question.OPEN_ENDED:
            if not data.text:
                raise ValueError("Open-ended answers require text.")

            save_open_ended_answer(answer, data.text)

        return {"message": "Answer submitted successfully"}

    except Exception as e:
        raise HttpError(500, str(e))


@router.post(
    "/quiz-ai-analysis",
    response=dict,
    description="Fetch all questions and answers for a user in a specific quiz and get AI analysis o",
)
def quiz_ai_analysis(request, data: UserQuizInputSchema):
    try:
        user = get_object_or_404(User, username=data.username)
        quiz = get_object_or_404(Quiz, id=data.quiz_id)

        questions = Question.objects.filter(quiz=quiz).prefetch_related(
            "answers",
            "answers__multiple_choice_answer__selected_option",
            "answers__single_choice_answer__selected_option",
            "answers__open_ended_answer",
        )

        response_data = {
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,
            "questions": [],
        }

        for question in questions:
            answer = question.answers.filter(user=user).first()
            user_answer = None

            if answer:
                if question.question_type == Question.MULTIPLE_CHOICE:
                    multiple_choice_answer = getattr(
                        answer, "multiple_choice_answer", None
                    )
                    if multiple_choice_answer:
                        user_answer = [
                            option.option
                            for option in multiple_choice_answer.selected_option.all()
                        ]
                elif question.question_type == Question.SINGLE_CHOICE:
                    single_choice_answer = getattr(answer, "single_choice_answer", None)
                    user_answer = (
                        single_choice_answer.selected_option.option
                        if single_choice_answer
                        else None
                    )
                elif question.question_type == Question.OPEN_ENDED:
                    open_ended_answer = getattr(answer, "open_ended_answer", None)
                    user_answer = (
                        open_ended_answer.response if open_ended_answer else None
                    )

            response_data["questions"].append(
                {
                    "question_id": question.id,
                    "question_text": question.text,
                    "question_type": question.get_question_type_display(),
                    "answer": user_answer,
                }
            )

        analysis = json.loads(ai_analysis(response_data, user))

        ModelAnalysisResult.objects.filter(user=user, quiz=quiz).delete()

        ModelAnalysisResult.objects.create(user=user, quiz=quiz, analysis=analysis)

        return {"message": "AI analysis completed successfully"}

    except Exception as e:
        raise HttpError(500, str(e))


@router.get(
    "fetch-quiz-analysis",
    response=dict,
    description="Fetch the analysis saved in the database",
)
def fetch_quiz_analysis(request, username: str = "", quiz_id: str = ""):
    try:
        saved_data = ModelAnalysisResult.objects.get(
            user__username=username, quiz__id=uuid.UUID(quiz_id)
        )

        return saved_data.analysis
    except Exception as e:
        raise HttpError(500, str(e))
