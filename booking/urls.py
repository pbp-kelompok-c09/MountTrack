from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # web views (existing)
    path('book/', views.booking_view, name='booking_view'),
    path('summary/<int:booking_id>/', views.booking_summary, name='booking_summary'),
    path('', views.home, name='home'),
    path('edit/<int:booking_id>/', views.edit_booking, name='edit_booking'),
    path('all-bookings/', views.all_bookings, name='all_bookings'),

    # API endpoints for Flutter (JSON)
    path('api/book/', views.booking_api_create, name='booking_api_create'),
    path('api/<int:booking_id>/', views.booking_api_detail, name='booking_api_detail'),
    path('api/<int:booking_id>/edit/', views.booking_api_update, name='booking_api_update'),
    path('api/history/', views.booking_api_history, name='booking_api_history'),
]