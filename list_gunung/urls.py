from django.urls import path
from . import views

urlpatterns = [
    path('', views.mount, name='mount'),
]