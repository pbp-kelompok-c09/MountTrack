from django.db import models
from django.utils.text import slugify


class Mountain(models.Model):
    """Model for mountains in Indonesia"""
    name = models.CharField(max_length=200)
    url = models.URLField(blank=True, null=True)
    height_mdpl = models.IntegerField(null=True, blank=True)
    province = models.CharField(max_length=100, default='Unknown')
    image_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-height_mdpl']
        verbose_name = 'Mountain'
        verbose_name_plural = 'Mountains'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name