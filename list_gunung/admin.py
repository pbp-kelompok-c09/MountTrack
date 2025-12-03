from django.contrib import admin
from .models import Mountain

@admin.register(Mountain)
class MountainAdmin(admin.ModelAdmin):
    list_display = ('name', 'height_mdpl', 'province', 'availability', 'min_book', 'experience_required', 'slug')
    list_filter = ('province', 'availability', 'experience_required')
    search_fields = ('name', 'province', 'description')
    prepopulated_fields = {'slug': ('name',)}
