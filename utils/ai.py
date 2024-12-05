import json
import uuid
import openai
from users.models import User
from django.conf import settings
from quiz.apis.schema_v1 import QuizResponseSchema

openai.api_key = settings.OPENAI_API_KEY

client = openai.OpenAI()


def uuid_to_string(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def ai_analysis(quiz_results: QuizResponseSchema, user: User):
    formatted_results = json.dumps(quiz_results, default=uuid_to_string, indent=2)

    user_data = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "username": user.username,
    }

    formatted_user_profile = json.dumps(user_data, indent=2)

    json_structure = {
        "type": "object",  # Define the root type
        "properties": {
            "user_profile": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "email": {"type": "string"},
                    "username": {"type": "string"},
                },
                "required": ["first_name", "last_name", "email", "username"],
            },
            "challenge_summary": {"type": "string"},
            "professional_feedback": {"type": "string"},
            "next_steps": {
                "type": "object",
                "properties": {
                    "resources": {
                        "type": "object",
                        "properties": {
                            "books": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "author": {"type": "string"},
                                        "url": {"type": "string"},
                                    },
                                    "required": [
                                        "title",
                                        "description",
                                        "author",
                                        "url",
                                    ],
                                },
                            },
                            "blogs_and_articles": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "author": {"type": "string"},
                                        "url": {"type": "string"},
                                    },
                                    "required": [
                                        "title",
                                        "description",
                                        "author",
                                        "url",
                                    ],
                                },
                            },
                        },
                        "required": ["books", "blogs_and_articles"],
                    },
                },
                "required": ["resources"],
            },
        },
        "required": [
            "user_profile",
            "challenge_summary",
            "professional_feedback",
            "next_steps",
        ],
    }

    system = f"""
    You are a highly skilled marriage counselor with years of experience helping individuals make informed decisions about their relationships. A user has completed a quiz designed to help them assess whether they should consider divorce or work on improving their marriage.
    
    Your job is to:
        1. Analyze the user’s answers with empathy and professionalism.
        2. Identify key themes or patterns in their responses (e.g., lack of communication, trust issues, personal growth challenges).
        3. Provide personalized insights tailored to the user’s unique situation.
        4. Offer actionable suggestions for their next steps, such as seeking counseling, improving communication, or evaluating their personal needs.
        5. Maintain a neutral tone, avoiding direct advice to divorce or stay, while focusing on empowerment and clarity.
    """

    prompt = f"""
    Here is the user’s profile:
    {formatted_user_profile}
    
    Here are the user’s quiz responses:
    {formatted_results}
    
    Based on this information, provide the following insights in JSON format:
        1. A brief summary of the user’s key challenges in their marriage.
        2. Personalized feedback addressing their concerns.
        3. Suggested next steps or resources they can explore to gain further clarity or improve their situation.
        
    NOTE: Respond in a clear, empathetic, and professional tone.
    """

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "analysis_schema",
                "schema": json_structure,
            },
        },
    )

    return completion.choices[0].message.content
