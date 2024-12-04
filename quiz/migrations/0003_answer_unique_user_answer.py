# Generated by Django 5.1.3 on 2024-12-04 15:11

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0002_alter_multiplechoiceoption_text"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="answer",
            constraint=models.UniqueConstraint(
                fields=("question", "user"), name="unique_user_answer"
            ),
        ),
    ]
