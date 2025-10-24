from django.db import models
from django.utils.text import slugify

class Mountain(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=255)
    height_mdpl = models.PositiveIntegerField()
    province = models.CharField(max_length=100)
    image_url = models.URLField(max_length=255, blank=True, null=True)
    description = models.TextField()
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 1. Pastikan slug belum terisi (biasanya hanya saat objek dibuat pertama kali)
        if not self.slug:
            # 2. Buat slug dari nama gunung (misalnya, "Anak Krakatau" -> "anak-krakatau")
            self.slug = slugify(self.name)
        
        # 3. Panggil method save bawaan untuk menyimpan data ke database
        super().save(*args, **kwargs)
