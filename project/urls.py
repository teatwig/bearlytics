from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('mothership/', admin.site.urls),
    path('', views.websites, name='websites'),
    path('<website_id>/dashboard/', views.dashboard, name='dashboard'),
    path('script.js', TemplateView.as_view(template_name='script.js', content_type='application/javascript'), name="script"),
    path('all-hits/', views.all_hits, name='all_hits'),
    path('<website_id>/hit', views.hit, name='hit'),
]
