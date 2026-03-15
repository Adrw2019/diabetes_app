from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "diabetes_app"

urlpatterns = [
    path("", views.root, name="root"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("predict/", views.predict, name="predict"),
    path(
        "password-reset/",
        views.CustomPasswordResetView.as_view(
            template_name="diabetes_app/password_reset_form.html",
            email_template_name="diabetes_app/emails/password_reset_email.txt",
            html_email_template_name="diabetes_app/emails/password_reset_email.html",
            subject_template_name="diabetes_app/emails/password_reset_subject.txt",
            success_url=reverse_lazy("diabetes_app:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="diabetes_app/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="diabetes_app/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="diabetes_app/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
