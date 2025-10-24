from django.urls import path


from . import views

app_name = "community"

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("create/", views.event_create, name="event_create"),
    path("<int:pk>/", views.event_detail, name="event_detail"),
    path("<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("<int:pk>/cancel/", views.event_cancel, name="event_cancel"),
    path("<int:pk>/join/", views.event_join, name="event_join"),
    path("<int:pk>/leave/", views.event_leave, name="event_leave"),
]