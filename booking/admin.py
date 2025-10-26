from django.contrib import admin
from .models import Booking, BookingMember
from list_gunung.models import Mountain  

class BookingMemberInline(admin.TabularInline):
    model = BookingMember
    extra = 1 
    fields = ('name', 'age', 'gender', 'level') 


class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'gunung', 'pax', 'porter_required', 'created_at')
    search_fields = ('user__username', 'gunung__name')
    list_filter = ('porter_required', 'created_at')
    ordering = ('-created_at',)
    inlines = [BookingMemberInline]  

   
    fieldsets = (
        (None, {
            'fields': ('user', 'gunung', 'pax', 'porter_required')
        }),
        ('Additional Information', {
            'fields': ('levels',),
            'classes': ('collapse',),
        }),
    )

class BookingMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'gender', 'level', 'booking')
    search_fields = ('name', 'booking__id')
    list_filter = ('gender', 'level')
    ordering = ('booking',)

admin.site.register(Booking, BookingAdmin)
admin.site.register(BookingMember, BookingMemberAdmin)
