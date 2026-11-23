from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from django.conf import settings
from django.conf.urls.static import static
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/acceso/', usuarios_views.acceso_admin, name='admin_acceso'),
    path('admin/acceso/mfa/', usuarios_views.verificar_mfa_admin, name='admin_acceso_mfa'),
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

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )