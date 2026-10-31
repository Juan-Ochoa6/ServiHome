
from django.contrib import admin
from .models import (
    Categoria,
    Servicio,
    ServicioProfesional,
    SolicitudServicio,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa')
    search_fields = ('nombre',)
    list_filter = ('activa',)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_base', 'activo')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('categoria', 'activo')


@admin.register(ServicioProfesional)
class ServicioProfesionalAdmin(admin.ModelAdmin):
    list_display = ('servicio', 'profesional', 'precio')
    list_filter = ('servicio',)
    search_fields = (
        'servicio__nombre',
        'profesional__usuario__username',
    )


@admin.register(SolicitudServicio)
class SolicitudServicioAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cliente',
        'profesional',
        'servicio',
        'fecha_solicitada',
        'estado',
    )
    list_filter = ('estado', 'fecha_creacion')
    search_fields = (
        'cliente__usuario__username',
        'profesional__usuario__username',
        'servicio__nombre',
    )
