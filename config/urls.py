from django.contrib import admin
from django.urls import path
from diabetes_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.predict_form, name='home'),
]
