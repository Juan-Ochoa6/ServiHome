from django.contrib import admin
from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'telefono', 'direccion', 'fecha_creacion')
    list_filter = ('rol',)
    search_fields = ('usuario__username', 'telefono')