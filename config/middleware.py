from django.shortcuts import redirect
from django.contrib.auth import logout


class AdminMFAMiddleware:
    """Exige MFA antes de permitir el acceso a Django Admin."""

    RUTAS_PERMITIDAS = {
        '/admin/acceso/',
        '/admin/acceso/mfa/',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ruta = request.path

        if ruta.startswith('/admin/') and ruta not in self.RUTAS_PERMITIDAS:
            usuario = request.user

            if not usuario.is_authenticated:
                return redirect('/admin/acceso/')

            if not (usuario.is_staff or usuario.is_superuser):
                logout(request)
                return redirect('/admin/acceso/')

            mfa_verificado = (
                request.session.get('admin_mfa_verified_user_id')
                == usuario.pk
            )

            if not mfa_verificado:
                logout(request)
                return redirect('/admin/acceso/')

        return self.get_response(request)