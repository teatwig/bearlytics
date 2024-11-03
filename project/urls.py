from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('mothership/', admin.site.urls),
    path('', views.projects, name='projects'),
    path('<project>/dashboard/', views.dashboard, name='dashboard'),
    path('all-hits/', views.all_hits, name='all_hits'),
    path('hit', views.hit, name='hit'),
]
