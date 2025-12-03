from django.urls import path
from . import views

urlpatterns = [
    # HTML views
    path('', views.mountain_list, name='mountain_list'),
    path('create/', views.mountain_create, name='mountain_create'),
    path('edit/<int:mountain_id>/', views.mountain_edit, name='mountain_edit'),
    path('delete/<int:mountain_id>/', views.mountain_delete, name='mountain_delete'),
    
    # JSON API endpoints
    path('api/mountains/', views.mountain_list_json, name='mountain_list_json'),
    path('api/mountains/<int:mountain_id>/', views.mountain_detail_json, name='mountain_detail_json'),
    
    # AJAX endpoints
    path('api/create/', views.mountain_create_ajax, name='mountain_create_ajax'),
    path('api/delete/<int:mountain_id>/', views.mountain_delete_ajax, name='mountain_delete_ajax'),
    
    # Detail view (must be last to avoid conflicts)
    path('<str:name>/', views.mountain_detail, name='mountain_detail'),
]