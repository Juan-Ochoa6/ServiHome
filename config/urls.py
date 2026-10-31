from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),

    # Aplicaciones
    path('api/usuarios/', include('usuarios.urls')),
    path('api/', include('servicios.urls')),

    # JWT
    path(
        'api/usuarios/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),

    # Documentación API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
]