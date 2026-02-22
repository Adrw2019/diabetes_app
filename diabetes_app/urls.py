from django.urls import path

from . import views

app_name = "diabetes_app"

urlpatterns = [
    path("", views.root, name="root"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("predict/", views.predict, name="predict"),
]
