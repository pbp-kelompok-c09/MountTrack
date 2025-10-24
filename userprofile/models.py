from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class UserProfile(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama = models.CharField(max_length=100)
    umur = models.PositiveIntegerField(null=True, blank=True)
    nomor_telepon = models.CharField(max_length=20, null=True, blank=True)
    # email udah attribute bawaan Django

    EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    category_experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='beginner')

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    jenis_kelamin = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    # history gunung yang lama (menggunakan textfield)
    # history_gunung = models.TextField(blank=True)
    
    history_gunung = models.ManyToManyField(
        "list_gunung.Mountain",
        blank=True,
        related_name="pendaki"
    )

    def add_history(self, mountain):
        """Menambahkan gunung ke riwayat pendakian user."""
        self.history_gunung.add(mountain)

    def __str__(self):
        return self.username
