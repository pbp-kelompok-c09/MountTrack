from django import forms
from .models import CommunityEvent, Comment

class EventForm(forms.ModelForm):
    class Meta:
        model = CommunityEvent
        fields = [
            "title", "mountain_name", "start_at", "end_at",
            "capacity", "price", "difficulty",
            "meeting_point", "contact_person", "description",
            "status",
        ]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3, "placeholder": "Tulis komentar..."}),
        }
        labels = {"body": ""}
