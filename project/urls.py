from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path('mothership/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
]
