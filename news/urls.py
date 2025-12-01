from django.urls import path, include
from . import views

app_name = "news"

urlpatterns = [
    path('', views.show_main, name='page_news'),
    path('news/<uuid:news_id>/', views.show_news, name='show_news'),
    path('create_news', views.create_news, name='create_news'),
    path('delete/<uuid:news_id>/', views.delete_news, name='delete_news'),
    path('edit/<uuid:news_id>/', views.edit_news, name='edit_news'),
    path('search/', views.search_news, name='search_news'),
    path('like/<uuid:news_id>/', views.like_news, name='like_news'),
    path('json/', views.show_json, name='show_json'),
    
    
]
