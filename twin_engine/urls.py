from django.urls import path
from . import views

urlpatterns = [
    path('', views.twin_dashboard, name='twin_dashboard'),
    
    path('register/', views.register, name='register'),
]