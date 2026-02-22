from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('diabetes_app.urls', 'diabetes_app'), namespace='diabetes_app')),
]
