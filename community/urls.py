from django.urls import path
from . import views

app_name = "community"

urlpatterns = [
    # HTML views (for web interface)
    path("", views.event_list, name="event_list"),
    path("create/", views.event_create, name="event_create"),
    path("<int:pk>/", views.event_detail, name="event_detail"),
    path("<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("<int:pk>/cancel/", views.event_cancel, name="event_cancel"),
    path("<int:pk>/join/", views.event_join, name="event_join"),
    path("<int:pk>/leave/", views.event_leave, name="event_leave"),
    
    # API views (for Flutter - JSON responses)
    path("api/", views.api_event_list, name="api_event_list"),
    path("api/create/", views.api_event_create, name="api_event_create"),
    path("api/<int:pk>/", views.api_event_detail, name="api_event_detail"),
    path("api/<int:pk>/edit/", views.api_event_edit, name="api_event_edit"),
    path("api/<int:pk>/cancel/", views.api_event_cancel, name="api_event_cancel"),
    path("api/<int:pk>/join/", views.api_event_join, name="api_event_join"),
    path("api/<int:pk>/leave/", views.api_event_leave, name="api_event_leave"),
]
