from django.urls import path
from . import views

app_name = "userprofile"

urlpatterns = [
    path("", views.login_user, name="default"),
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("profile/", views.profile_user, name="profile"),
    path("admin-portal/", views.admin_portal_user, name="admin_portal"),
    path("no-access/", views.no_access_user, name="no_access"), 
]
