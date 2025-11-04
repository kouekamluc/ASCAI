"""
URL configuration for accounts app.
"""

from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("change-password/", views.change_password_view, name="change_password"),
    path(
        "activate/<uidb64>/<token>/",
        views.activate_account,
        name="activate",
    ),
]






