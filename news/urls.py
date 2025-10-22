from django.urls import path, include
from . import views

app_name = "news"

urlpatterns = [
    path('', views.show_main, name='page_news'),
    path('news/<uuid:news_id>/', views.show_news, name='show_news'),
    path('create_news', views.create_news, name='create_news'),
    path('news/delete/<uuid:news_id>/', views.delete_news, name='delete_news'),
    
]
