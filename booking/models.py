from django.db import models
from django.conf import settings

class Gunung(models.Model):
    nama = models.CharField(max_length=100)
    lokasi = models.CharField(max_length=100)
    cuaca = models.CharField(max_length=50)
    ketersediaan = models.BooleanField(default=True)  
    level_difficulty = models.CharField(max_length=50)  

    def __str__(self):
        return self.nama

class Booking(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gunung = models.ForeignKey(Gunung, on_delete=models.CASCADE)
    pax = models.IntegerField()  
    levels = models.JSONField()  
    porter_required = models.BooleanField(default=False)
    
    def check_porter(self):
        if all(level == 'beginner' for level in self.levels):
            return True
        return False

    def __str__(self):
        return f"Booking for {self.user.username} at {self.gunung.nama}"
