import uuid
import json
from typing import List
from ninja import Router
from users.models import User
from utils.ai import ai_analysis
from ninja.errors import HttpError
from ai.models import ModelAnalysisResult
from django.shortcuts import get_object_or_404
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
    response=dict,
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

        if Answer.objects.filter(question=question, user=user).exists():
            Answer.objects.filter(question=question, user=user).first().delete()

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

        questions = Question.objects.filter(quiz=quiz)

        response_data = {
            "quiz_id": quiz.id,
            "quiz_title": quiz.title,
            "questions": [],
        }

        for question in questions:
            answer = Answer.objects.filter(question=question, user=user).first()

            user_answer = None

            if answer:
                if question.question_type == Question.MULTIPLE_CHOICE:
                    multiple_choice_answer = MultipleChoiceAnswer.objects.filter(
                        answer=answer
                    ).first()
                    if multiple_choice_answer:
                        user_answer = [multiple_choice_answer.selected_option.text]
                elif question.question_type == Question.RATING_SCALE:
                    rating_scale_answer = RatingScaleAnswer.objects.filter(
                        answer=answer
                    ).first()
                    user_answer = (
                        rating_scale_answer.rating if rating_scale_answer else None
                    )
                elif question.question_type == Question.OPEN_ENDED:
                    open_ended_answer = OpenEndedAnswer.objects.filter(
                        answer=answer
                    ).first()
                    user_answer = (
                        open_ended_answer.response if open_ended_answer else None
                    )
                elif question.question_type == Question.YES_NO:
                    yes_no_answer = YesNoAnswer.objects.filter(answer=answer).first()
                    user_answer = yes_no_answer.response if yes_no_answer else None

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
