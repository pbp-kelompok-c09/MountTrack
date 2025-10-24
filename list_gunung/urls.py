from django.urls import path
from . import views

urlpatterns = [
    path('', views.mountain_list, name='mountain_list'),
    path('<str:name>/', views.mountain_detail, name='mountain_detail'),
]