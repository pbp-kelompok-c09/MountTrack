from django.contrib import admin
from .models import Mountain

@admin.register(Mountain)
class MountainAdmin(admin.ModelAdmin):
    list_display = ('name', 'height_mdpl', 'province', 'slug')
    list_filter = ('province',)
    search_fields = ('name', 'province', 'description')
    prepopulated_fields = {'slug': ('name',)}
