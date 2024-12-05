from django.contrib import admin
from .models import ModelAnalysisResult


@admin.register(ModelAnalysisResult)
class ModelAnalysisResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "created_at",
        "updated_at",
        "metadata",
    )
    list_filter = (
        "user",
        "created_at",
    )
    search_fields = (
        "user__username",
        "analysis",
    )
    list_per_page = 20
    list_editable = ("metadata",)
    fields = (
        "user",
        "analysis",
        "metadata",
    )
