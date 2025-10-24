from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CommunityEvent(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Open"
        FULL = "FULL", "Full"
        CANCELLED = "CANCELLED", "Cancelled"

    class Difficulty(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"

    title = models.CharField(max_length=140)
    mountain_name = models.CharField(max_length=140)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)

    capacity = models.PositiveIntegerField(default=10)
    price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)

    difficulty = models.CharField(
        max_length=12,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER,
    )

    meeting_point = models.CharField(max_length=160, blank=True)
    contact_person = models.CharField(max_length=100, help_text="WA/Telp")

    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")

    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_at", "title"]

    def __str__(self):
        return f"{self.title} • {self.mountain_name}"

    # ---- Helpers yang dipakai di views ----
    def confirmed_count(self) -> int:
        return self.joins.filter(status=EventJoin.Status.CONFIRMED).count()

    def waitlist_count(self) -> int:
        return self.joins.filter(status=EventJoin.Status.WAITLIST).count()

    def is_full(self) -> bool:
        return self.confirmed_count() >= self.capacity

    def date_range_display(self) -> str:
        if self.end_at and self.end_at.date() != self.start_at.date():
            return f"{self.start_at:%d %b %Y %H:%M} – {self.end_at:%d %b %Y %H:%M}"
        return f"{self.start_at:%d %b %Y %H:%M}"


class EventJoin(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"       # status default (belum diproses)
        CONFIRMED = "CONFIRMED", "Confirmed" # peserta masuk kuota
        WAITLIST = "WAITLIST", "Waitlist"    # nunggu kuota
        CANCELLED = "CANCELLED", "Cancelled" # peserta batal

    event = models.ForeignKey(CommunityEvent, on_delete=models.CASCADE, related_name="joins")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event_joins")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "user")
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user} → {self.event} ({self.status})"


class Comment(models.Model):
    event = models.ForeignKey(CommunityEvent, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment({self.user} on {self.event})"
