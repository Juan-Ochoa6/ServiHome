from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from usuarios.models import Perfil
from servicios.models import (
    Categoria,
    Servicio,
    ServicioProfesional,
    SolicitudServicio,
    PropuestaPrecio,
    Resena,
    Pago,
    Incidente,
)


class DryRunRollback(Exception):
    pass


class Command(BaseCommand):
    help = "Crea datos ficticios de demostración para ServiHome."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula la carga sin guardar los cambios.",
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.crear_datos()

                if options["dry_run"]:
                    raise DryRunRollback()

        except DryRunRollback:
            self.stdout.write(
                self.style.WARNING(
                    "Simulación terminada. No se guardó ningún registro."
                )
            )

    def crear_datos(self):
        User = get_user_model()
        ahora = timezone.now()

        creados = {
            "Usuarios": 0,
            "Categorías": 0,
            "Servicios": 0,
            "Ofertas": 0,
            "Trabajos": 0,
            "Propuestas": 0,
            "Reseñas": 0,
            "Pagos": 0,
            "Incidentes": 0,
        }

        clientes = []
        profesionales = []

        # -------------------------------------------------
        # 1. CREAR 50 CLIENTES Y 50 PROFESIONALES
        # -------------------------------------------------

        for i in range(1, 51):
            for rol, lista, prefijo in [
                ("cliente", clientes, "demo_cliente"),
                ("profesional", profesionales, "demo_profesional"),
            ]:
                username = f"{prefijo}_{i:03d}"

                user, creado = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": f"{username}@example.com",
                        "first_name": f"{rol.capitalize()}",
                        "last_name": f"Demostracion {i}",
                    },
                )

                if creado:
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                    creados["Usuarios"] += 1

                perfil = Perfil.objects.get(usuario=user)

                if perfil.rol != rol and not creado:
                    raise CommandError(
                        f"El usuario {username} ya existe con otro rol. "
                        "No se modificó."
                    )

                if creado:
                    perfil.rol = rol
                    perfil.telefono = f"300{(1000000 + i):07d}"[-10:]
                    perfil.direccion = (
                        f"Dirección ficticia de demostración {i}"
                    )

                    if rol == "profesional":
                        perfil.estado_verificacion = "aprobado"
                        perfil.estado_identidad = "aprobado"
                        perfil.descripcion_profesional = (
                            "Profesional de demostración ServiHome."
                        )
                        perfil.experiencia_anos = (i % 10) + 1
                        perfil.disponible = True

                    perfil.save()

                lista.append(perfil)

        # -------------------------------------------------
        # 2. CATEGORÍAS
        # -------------------------------------------------

        categorias_datos = [
            ("Plomeria", "Servicios de plomería."),
            ("Electricidad", "Instalaciones y reparaciones eléctricas."),
            ("Carpinteria", "Trabajos de carpintería."),
            ("Pintura", "Pintura y mantenimiento de paredes."),
            ("Cerrajeria", "Servicios de cerrajería."),
            ("Limpieza", "Servicios de limpieza del hogar."),
        ]

        categorias = {}

        for nombre, descripcion in categorias_datos:
            categoria, creado = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "descripcion": descripcion,
                    "activa": True,
                },
            )

            creados["Categorías"] += int(creado)
            categorias[nombre] = categoria

        # -------------------------------------------------
        # 3. SERVICIOS
        # -------------------------------------------------

        servicios_datos = {
            "Plomeria": [
                "Reparación de fugas",
                "Instalación de grifería",
                "Mantenimiento de tuberías",
            ],
            "Electricidad": [
                "Instalación de luminarias",
                "Revisión de conexiones",
                "Cambio de tomacorrientes",
            ],
            "Carpinteria": [
                "Reparación de puertas",
                "Instalación de estanterías",
                "Ajuste de muebles",
            ],
            "Pintura": [
                "Pintura de habitaciones",
                "Pintura de fachadas",
                "Resane de paredes",
            ],
            "Cerrajeria": [
                "Apertura de cerraduras",
                "Cambio de cerraduras",
                "Instalación de chapas",
            ],
            "Limpieza": [
                "Limpieza profunda",
                "Limpieza de cocina",
                "Limpieza de baños",
            ],
        }

        servicios = []

        for nombre_categoria, nombres in servicios_datos.items():
            for j, nombre in enumerate(nombres):
                servicio, creado = Servicio.objects.get_or_create(
                    categoria=categorias[nombre_categoria],
                    nombre=nombre,
                    defaults={
                        "descripcion": (
                            f"Servicio de demostración: {nombre}."
                        ),
                        "precio_base": Decimal("80000") + Decimal(j * 15000),
                        "activo": True,
                    },
                )

                creados["Servicios"] += int(creado)
                servicios.append(servicio)

        # -------------------------------------------------
        # 4. OFERTAS DE PROFESIONALES
        # -------------------------------------------------

        ofertas = []

        for i in range(16):
            profesional = profesionales[i % 50]
            servicio = servicios[(i * 3) % len(servicios)]

            oferta, creado = ServicioProfesional.objects.get_or_create(
                servicio=servicio,
                profesional=profesional,
                defaults={
                    "precio": Decimal("70000") + Decimal(i * 5000),
                    "estado_aprobacion": (
                        "pendiente" if i % 4 == 0 else "aprobado"
                    ),
                },
            )

            creados["Ofertas"] += int(creado)
            ofertas.append(oferta)

        ofertas_aprobadas = [
            oferta
            for oferta in ServicioProfesional.objects.select_related(
                "servicio", "profesional"
            ).filter(
                estado_aprobacion="aprobado",
                profesional__in=profesionales,
            )
        ]

        if not ofertas_aprobadas:
            raise CommandError(
                "No hay ofertas aprobadas para crear los trabajos."
            )

        # -------------------------------------------------
        # 5. CREAR 30 TRABAJOS
        # -------------------------------------------------

        estados = (
            ["pendiente"] * 5
            + ["aceptada"] * 5
            + ["en_proceso"] * 5
            + ["completada"] * 10
            + ["rechazada"] * 3
            + ["cancelada"] * 2
        )

        trabajos = []

        for i, estado in enumerate(estados, start=1):
            oferta = ofertas_aprobadas[(i - 1) % len(ofertas_aprobadas)]
            cliente = clientes[(i - 1) % len(clientes)]

            precio = Decimal("90000") + Decimal(i * 7000)

            datos = {
                "cliente": cliente,
                "profesional": oferta.profesional,
                "servicio": oferta.servicio,
                "descripcion": (
                    f"[DEMO-SERVIHOME] Trabajo de prueba {i:02d}"
                ),
                "direccion_servicio": (
                    f"Dirección ficticia de prueba {i:02d}, Bogotá"
                ),
                "fecha_solicitada": ahora + timedelta(days=(i % 15) - 7),
                "estado": estado,
            }

            if estado in ("aceptada", "en_proceso", "completada"):
                datos["precio_acordado"] = precio
                datos["codigo_inicio"] = f"{100000 + i:06d}"

            if estado in ("en_proceso", "completada"):
                datos["codigo_finalizacion"] = f"{200000 + i:06d}"

            solicitud, creado = SolicitudServicio.objects.get_or_create(
                descripcion=datos["descripcion"],
                defaults=datos,
            )

            creados["Trabajos"] += int(creado)
            trabajos.append(solicitud)

        # -------------------------------------------------
        # 6. PROPUESTAS DE PRECIO
        # -------------------------------------------------

        propuestas = []

        trabajos_completados = [
            t for t in trabajos if t.estado == "completada"
        ]

        trabajos_pendientes = [
            t for t in trabajos if t.estado == "pendiente"
        ]

        for i, solicitud in enumerate(trabajos_completados[:6], start=1):
            propuesta, creado = PropuestaPrecio.objects.get_or_create(
                solicitud=solicitud,
                proponente=solicitud.profesional,
                precio=solicitud.precio_acordado,
                defaults={
                    "estado": "aceptada",
                },
            )

            creados["Propuestas"] += int(creado)
            propuestas.append(propuesta)

        for i, solicitud in enumerate(trabajos_pendientes[:4], start=1):
            propuesta, creado = PropuestaPrecio.objects.get_or_create(
                solicitud=solicitud,
                proponente=solicitud.profesional,
                precio=Decimal("100000") + Decimal(i * 10000),
                defaults={
                    "estado": "pendiente",
                },
            )

            creados["Propuestas"] += int(creado)
            propuestas.append(propuesta)

        # -------------------------------------------------
        # 7. RESEÑAS DE TRABAJOS COMPLETADOS
        # -------------------------------------------------

        for i, solicitud in enumerate(trabajos_completados, start=1):
            resena, creado = Resena.objects.get_or_create(
                solicitud=solicitud,
                defaults={
                    "calificacion": (i % 5) + 1,
                    "comentario": (
                        f"[DEMO] Reseña de prueba número {i}."
                    ),
                },
            )

            creados["Reseñas"] += int(creado)

        # -------------------------------------------------
        # 8. PAGOS
        # -------------------------------------------------

        trabajos_para_pago = trabajos_completados[:8]

        for i, solicitud in enumerate(trabajos_para_pago, start=1):
            estado_pago = "pagado" if i <= 6 else "pendiente"

            pago, creado = Pago.objects.get_or_create(
                solicitud=solicitud,
                defaults={
                    "monto_total": solicitud.precio_acordado,
                    "porcentaje_comision": Decimal("10.00"),
                    "metodo": (
                        "transferencia" if i % 2 == 0 else "efectivo"
                    ),
                    "estado": estado_pago,
                    "referencia": f"DEMO-PAGO-{i:03d}",
                    "fecha_pago": (
                        ahora - timedelta(days=i)
                        if estado_pago == "pagado"
                        else None
                    ),
                },
            )

            creados["Pagos"] += int(creado)

        # -------------------------------------------------
        # 9. INCIDENTES
        # -------------------------------------------------

        tipos_incidente = [
            "danos_materiales",
            "incumplimiento",
            "comportamiento",
            "cobro_indebido",
            "otro",
        ]

        estados_incidente = [
            "pendiente",
            "en_revision",
            "resuelto",
            "rechazado",
            "pendiente",
        ]

        for i in range(5):
            solicitud = trabajos_completados[i]
            incidente, creado = Incidente.objects.get_or_create(
                solicitud=solicitud,
                tipo=tipos_incidente[i],
                defaults={
                    "reportado_por": solicitud.cliente,
                    "descripcion": (
                        f"[DEMO] Incidente de prueba número {i + 1}."
                    ),
                    "estado": estados_incidente[i],
                    "respuesta_administrador": (
                        "Caso revisado por administración."
                        if estados_incidente[i] in ("resuelto", "rechazado")
                        else ""
                    ),
                },
            )

            creados["Incidentes"] += int(creado)

        # -------------------------------------------------
        # 10. RESUMEN
        # -------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("RESUMEN DE DATOS DE DEMOSTRACIÓN")
        )

        for nombre, cantidad in creados.items():
            self.stdout.write(f"{nombre}: {cantidad} nuevos")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Proceso de creación finalizado."
            )
        )