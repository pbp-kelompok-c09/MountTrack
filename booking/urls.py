
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('<slug:gunung_slug>/', views.booking_view, name='booking_view'),
    path('summary/<int:booking_id>/', views.booking_summary, name='booking_summary'),
]
