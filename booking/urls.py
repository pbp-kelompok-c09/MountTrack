from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [

    path('book/', views.booking_view, name='booking_view'),
    path('summary/<int:booking_id>/', views.booking_summary, name='booking_summary'),
    path('', views.home, name='home'),
    path('edit/<int:booking_id>/', views.edit_booking, name='edit_booking'),
    path('all-bookings/', views.all_bookings, name='all_bookings'),

    path('payment/<int:booking_id>/', views.payment_view, name='payment'),
    path('api/booking/<int:booking_id>/pay/', views.booking_api_pay, name='booking_api_pay'),
    path('api/book/', views.booking_api_create, name='booking_api_create'),
    path('api/<int:booking_id>/', views.booking_api_detail, name='booking_api_detail'),
    path('api/<int:booking_id>/edit/', views.booking_api_update, name='booking_api_update'),
    path('api/history/', views.booking_api_history, name='booking_api_history'),
    path('api/pay/<int:booking_id>/', views.booking_api_pay, name='booking_api_pay'),
    path('api/profiles/', views.profiles_api_list, name='booking_profiles'),
    path('history/', views.booking_history_list_plain, name='booking_history_plain'),
    path('api/delete/<int:booking_id>/', views.booking_api_delete, name='booking_api_delete'),
]