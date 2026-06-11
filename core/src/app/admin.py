from django.contrib import admin
from .models import VozaviForm, Question, VozaviResponse


@admin.register(VozaviForm)
class VozaviFormAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'brand_name')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('label', 'form', 'type', 'required', 'position')
    list_filter = ('type',)


@admin.register(VozaviResponse)
class VozaviResponseAdmin(admin.ModelAdmin):
    list_display = ('form', 'created_at')
