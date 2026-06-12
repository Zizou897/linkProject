from django.contrib import admin
from .models import VozaviForm, Question, VozaviResponse, ContactMessage


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


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'category', 'is_read', 'created_at')
    list_filter = ('is_read', 'category')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'category', 'message', 'created_at')
    list_editable = ('is_read',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
