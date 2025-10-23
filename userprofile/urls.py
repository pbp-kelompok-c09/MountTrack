from django.urls import path, include
from . import views

app_name = "userprofile"

urlpatterns = [
    path("", views.login_user, name="default"),
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("my-profile/", views.profile_user, name="my-profile"),
    path("admin-portal/", views.admin_portal_user, name="admin_portal"),
    path("no-access/", views.no_access_user, name="no_access"), 
    path("admin-portal/add-user/", views.add_user_ajax, name="add_user_ajax"),
    path("admin-portal/get-users/", views.get_users_json, name="get_users_json"),
    path("profile/<str:username>/", views.public_profile_view, name="public_profile"),
]
