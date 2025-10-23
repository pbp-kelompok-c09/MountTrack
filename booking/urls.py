from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('<int:gunung_id>/', views.booking_view, name='booking_view'),  
]
