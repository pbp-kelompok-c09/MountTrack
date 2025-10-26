
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('book/', views.booking_view, name='booking_view'),
    path('summary/<int:booking_id>/', views.booking_summary, name='booking_summary'),
    path('', views.home, name='home'),
    path('edit/<int:booking_id>/', views.edit_booking, name='edit_booking'),
    path('all-bookings/', views.all_bookings, name='all_bookings'),
]
