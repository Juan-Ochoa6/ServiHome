
from django.urls import path
from . import views

urlpatterns = [
    path('mfa/configurar/', views.configurar_mfa, name='configurar_mfa'),
    path('mfa/verificar/', views.verificar_mfa, name='verificar_mfa'),
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('login/mfa/', views.verificar_codigo_login, name='verificar_codigo_login'),
]
