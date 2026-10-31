from django.db import migrations


def inicializar_estados(apps, schema_editor):
    Perfil = apps.get_model('usuarios', 'Perfil')
    ServicioProfesional = apps.get_model(
        'servicios',
        'ServicioProfesional'
    )

    # Los clientes no necesitan verificación profesional.
    Perfil.objects.filter(rol='cliente').update(
        estado_verificacion='no_aplica'
    )

    # Los profesionales existentes deben pasar por aprobación.
    Perfil.objects.filter(rol='profesional').update(
        estado_verificacion='pendiente',
        disponible=False
    )

    # Ninguna oferta de servicio queda aprobada automáticamente.
    ServicioProfesional.objects.all().update(
        estado_aprobacion='pendiente'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0009_perfil_estado_verificacion'),
        ('servicios', '0004_servicioprofesional_estado_aprobacion'),
    ]

    operations = [
        migrations.RunPython(
            inicializar_estados,
            migrations.RunPython.noop
        ),
    ]