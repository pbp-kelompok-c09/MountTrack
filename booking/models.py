from django.db import models
from django.conf import settings
from django.utils import timezone

# coba import Mountain dari app list_gunung
try:
    from list_gunung.models import Mountain
except Exception:
    Mountain = None

class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gunung = models.ForeignKey('list_gunung.Mountain', on_delete=models.SET_NULL, null=True, blank=True)
    pax = models.PositiveIntegerField(default=1)
    # levels per anggota (optional redundan), simpan juga detail anggota di BookingMember
    levels = models.JSONField(default=list, blank=True)
    porter_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        gunung_n = getattr(self.gunung, 'nama', None) or (str(self.gunung) if self.gunung else 'Unknown')
        return f'Booking #{self.id} - {self.user.username} -> {gunung_n}'

    def summary(self):
        """Return dict summary suitable to store in userprofile.history_entries."""
        anggota = [m.as_dict() for m in self.members.all()]
        return {
            'booking_id': self.id,
            'gunung_id': getattr(self.gunung, 'id', None),
            'gunung_nama': getattr(self.gunung, 'nama', str(self.gunung) if self.gunung else None),
            'pax': self.pax,
            'anggota': anggota,
            'levels': self.levels,
            'porter_required': self.porter_required,
            'created_at': self.created_at.isoformat(),
        }

class BookingMember(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    booking = models.ForeignKey(Booking, related_name='members', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)

    def __str__(self):
        return f'{self.name} ({self.level})'

    def as_dict(self):
        return {
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'level': self.level,
        }