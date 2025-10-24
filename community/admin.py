from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CommunityEvent, EventJoin, Comment

@admin.register(CommunityEvent)
class CommunityEventAdmin(admin.ModelAdmin):
    list_display = ("title", "mountain_name", "start_at", "capacity", "status", "organizer")
    list_filter = ("status", "difficulty", "start_at")
    search_fields = ("title", "mountain_name", "organizer__username", "description")

@admin.register(EventJoin)
class EventJoinAdmin(admin.ModelAdmin):
    list_display = ("event", "user", "status", "joined_at")
    list_filter = ("status",)
    search_fields = ("event__title", "user__username")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("event", "user", "created_at")
    search_fields = ("event__title", "user__username", "body")