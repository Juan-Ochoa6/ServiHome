from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from usuarios.models import Perfil, DocumentoVerificacion
from servicios.models import (
    Categoria,
    Servicio,
    ServicioProfesional,
    TrabajoPortafolio,
    SolicitudServicio,
    PropuestaPrecio,
    Resena,
    Pago,
    Incidente,
)


class DryRunRollback(Exception):
    """Fuerza el rollback de la transacción durante --dry-run."""


class Command(BaseCommand):
    help = (
        "Crea datos ficticios realistas para demostrar los módulos "
        "de ServiHome."
    )

    PASSWORD_DEMO = "DemoServiHome2026*"

    NOMBRES = [
        ("Camila", "Rojas"),
        ("Andrés", "Martínez"),
        ("Valentina", "Gómez"),
        ("Santiago", "Torres"),
        ("Laura", "Castro"),
        ("Mateo", "Herrera"),
        ("Daniela", "Moreno"),
        ("Sebastián", "Ramírez"),
        ("Mariana", "Vargas"),
        ("Nicolás", "Jiménez"),
        ("Paula", "Cárdenas"),
        ("Felipe", "Navarro"),
        ("Isabella", "Mendoza"),
        ("David", "Restrepo"),
        ("Lucía", "Peña"),
        ("Samuel", "Ortiz"),
        ("Gabriela", "Silva"),
        ("Tomás", "Reyes"),
        ("Juliana", "Pardo"),
        ("Miguel", "Duarte"),
    ]

    PERFILES_PROFESIONALES = [
        {
            "verificacion": "aprobado",
            "identidad": "aprobado",
            "disponible": True,
            "experiencia": 8,
            "descripcion": "Plomero especializado en fugas, redes hidráulicas e instalación de grifería residencial.",
        },
        {
            "verificacion": "aprobado",
            "identidad": "aprobado",
            "disponible": True,
            "experiencia": 6,
            "descripcion": "Electricista con experiencia en iluminación, tomacorrientes y mantenimiento de instalaciones domésticas.",
        },
        {
            "verificacion": "aprobado",
            "identidad": "aprobado",
            "disponible": True,
            "experiencia": 5,
            "descripcion": "Especialista en limpieza profunda, cocinas, baños y mantenimiento del hogar.",
        },
        {
            "verificacion": "aprobado",
            "identidad": "aprobado",
            "disponible": False,
            "experiencia": 9,
            "descripcion": "Carpintero dedicado a reparación de muebles, puertas y fabricación de estanterías.",
        },
        {
            "verificacion": "pendiente",
            "identidad": "pendiente",
            "disponible": False,
            "experiencia": 3,
            "descripcion": "Pintora residencial con experiencia en resane y acabados interiores.",
        },
        {
            "verificacion": "en_revision",
            "identidad": "aprobado",
            "disponible": False,
            "experiencia": 4,
            "descripcion": "Cerrajero enfocado en instalación y mantenimiento de cerraduras de seguridad.",
        },
        {
            "verificacion": "rechazado",
            "identidad": "rechazado",
            "disponible": False,
            "experiencia": 2,
            "descripcion": "Técnico de mantenimiento general para pequeñas reparaciones domésticas.",
        },
        {
            "verificacion": "aprobado",
            "identidad": "aprobado",
            "disponible": True,
            "experiencia": 7,
            "descripcion": "Profesional de plomería y mantenimiento preventivo de redes de agua.",
        },
        {
            "verificacion": "pendiente",
            "identidad": "aprobado",
            "disponible": False,
            "experiencia": 3,
            "descripcion": "Auxiliar de limpieza residencial y organización de espacios.",
        },
        {
            "verificacion": "aprobado",
            "identidad": "aprobado",
            "disponible": True,
            "experiencia": 10,
            "descripcion": "Técnico electricista con trayectoria en instalaciones y diagnóstico de fallas.",
        },
    ]

    DIRECCIONES = [
        "Calle 26 # 18-42, Bogotá",
        "Carrera 15 # 93-20, Bogotá",
        "Calle 80 # 24-16, Bogotá",
        "Carrera 7 # 45-30, Bogotá",
        "Calle 134 # 9-18, Bogotá",
        "Carrera 68 # 22-15, Bogotá",
        "Calle 53 # 16-27, Bogotá",
        "Carrera 30 # 12-40, Bogotá",
        "Calle 116 # 50-08, Bogotá",
        "Carrera  Deza # 10-35, Bogotá",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula la carga y revierte los registros creados.",
        )

    def handle(self, *args, **options):
        self.archivos_creados = []

        try:
            with transaction.atomic():
                self.crear_datos()

                if options["dry_run"]:
                    raise DryRunRollback()

        except DryRunRollback:
            self.eliminar_archivos_creados()
            self.stdout.write(
                self.style.WARNING(
                    "Simulación terminada: se revirtieron los registros "
                    "y se eliminaron los archivos temporales."
                )
            )
            return
        except Exception:
            self.eliminar_archivos_creados()
            raise

        self.stdout.write(
            self.style.SUCCESS(
                "Carga de demostración finalizada correctamente."
            )
        )
        self.stdout.write(
            f"Contraseña común de las cuentas demo: {self.PASSWORD_DEMO}"
        )

    def eliminar_archivos_creados(self):
        for storage, nombre in self.archivos_creados:
            try:
                storage.delete(nombre)
            except Exception:
                pass
        self.archivos_creados.clear()

    def guardar_archivo(self, campo, nombre, contenido):
        campo.save(nombre, contenido, save=False)
        self.archivos_creados.append((campo.storage, campo.name))

    def crear_imagen_portafolio(self, titulo):
        buffer = BytesIO()
        imagen = Image.new("RGB", (900, 600), "#e8eef4")
        dibujo = ImageDraw.Draw(imagen)
        dibujo.rectangle((35, 35, 865, 565), outline="#36536b", width=8)
        dibujo.text((75, 250), "SERVIHOME", fill="#183247")
        dibujo.text((75, 300), titulo[:55], fill="#183247")
        imagen.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue())

    def crear_pdf_documento(self, nombre, tipo):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle("Documento ficticio de demostracion ServiHome")
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(55, 735, "SERVIHOME - DOCUMENTO DE DEMOSTRACION")
        pdf.setFont("Helvetica", 11)
        pdf.drawString(55, 700, f"Nombre ficticio: {nombre}")
        pdf.drawString(55, 680, f"Tipo de documento: {tipo}")
        pdf.drawString(55, 640, "Archivo de prueba. No corresponde a una persona real.")
        pdf.drawString(55, 620, "Generado automaticamente para poblar el entorno demo.")
        pdf.save()
        return ContentFile(buffer.getvalue())

    def crear_datos(self):
        User = get_user_model()
        ahora = timezone.now()

        creados = {
            "Usuarios": 0,
            "Perfiles": 0,
            "Categorías": 0,
            "Servicios": 0,
            "Ofertas profesionales": 0,
            "Documentos": 0,
            "Trabajos de portafolio": 0,
            "Solicitudes": 0,
            "Propuestas": 0,
            "Reseñas": 0,
            "Pagos": 0,
            "Incidentes": 0,
        }

        clientes = []
        profesionales = []

        # 1. Usuarios y perfiles: 10 clientes y 10 profesionales.
        for indice, (nombre, apellido) in enumerate(self.NOMBRES):
            rol = "cliente" if indice < 10 else "profesional"
            numero = indice + 1 if rol == "cliente" else indice - 9
            from unicodedata import normalize

            nombre_usuario = normalize("NFKD", f"{nombre}.{apellido}")
            nombre_usuario = "".join(
                caracter for caracter in nombre_usuario
                if not __import__("unicodedata").combining(caracter)
            ).lower()

            username = nombre_usuario
            email = f"{username}@servihome.test"

            user, usuario_creado = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": nombre,
                    "last_name": apellido,
                },
            )

            if usuario_creado:
                user.set_password(self.PASSWORD_DEMO)
                user.save(update_fields=["password"])
                creados["Usuarios"] += 1
            else:
                if user.is_superuser:
                    raise CommandError(
                        f"El usuario {username} es administrador y no se modificará."
                    )
                user.email = email
                user.first_name = nombre
                user.last_name = apellido
                user.save(update_fields=["email", "first_name", "last_name"])

            perfil, perfil_creado = Perfil.objects.get_or_create(
                usuario=user,
                defaults={"rol": rol},
            )

            if perfil.rol != rol:
                if usuario_creado:
                    perfil.rol = rol
                    perfil.save(update_fields=["rol"])
                else:
                    raise CommandError(
                        f"El usuario {username} ya existe con un rol diferente."
                    )
            if perfil_creado:
                creados["Perfiles"] += 1

            perfil.telefono = f"310555{numero:04d}"
            perfil.direccion = self.DIRECCIONES[(indice) % len(self.DIRECCIONES)]

            if rol == "cliente":
                perfil.estado_verificacion = "no_aplica"
                perfil.estado_identidad = (
                    "aprobado" if numero <= 8 else "pendiente"
                )
                perfil.descripcion_profesional = ""
                perfil.experiencia_anos = 0
                perfil.disponible = True
                clientes.append(perfil)
            else:
                datos = self.PERFILES_PROFESIONALES[numero - 1]
                perfil.estado_verificacion = datos["verificacion"]
                perfil.estado_identidad = datos["identidad"]
                perfil.descripcion_profesional = datos["descripcion"]
                perfil.experiencia_anos = datos["experiencia"]
                perfil.disponible = datos["disponible"]
                profesionales.append(perfil)

            perfil.two_factor_enabled = False
            perfil.totp_secret = ""
            perfil.save()

        # 2. Categorías.
        categorias_datos = [
            ("Plomeria", "Reparación e instalación de redes hidráulicas."),
            ("Electricidad", "Instalaciones y mantenimiento eléctrico."),
            ("Carpinteria", "Reparación y fabricación de elementos en madera."),
            ("Pintura", "Pintura, resanes y acabados residenciales."),
            ("Cerrajeria", "Instalación y mantenimiento de cerraduras."),
            ("Limpieza", "Limpieza profunda y mantenimiento del hogar."),
        ]

        categorias = {}
        for nombre, descripcion in categorias_datos:
            categoria, creado = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion, "activa": True},
            )
            creados["Categorías"] += int(creado)
            categorias[nombre] = categoria

        # 3. Servicios.
        servicios_datos = {
            "Plomeria": [
                "Reparación de fugas",
                "Instalación de grifería",
            ],
            "Electricidad": [
                "Instalación de luminarias",
                "Revisión de conexiones",
            ],
            "Carpinteria": [
                "Reparación de puertas",
                "Instalación de estanterías",
            ],
            "Pintura": [
                "Pintura de habitaciones",
                "Resane de paredes",
            ],
            "Cerrajeria": [
                "Cambio de cerraduras",
                "Instalación de chapas",
            ],
            "Limpieza": [
                "Limpieza profunda",
                "Limpieza de baños",
            ],
        }

        servicios = []
        for nombre_categoria, nombres in servicios_datos.items():
            for posicion, nombre in enumerate(nombres):
                servicio, creado = Servicio.objects.get_or_create(
                    categoria=categorias[nombre_categoria],
                    nombre=nombre,
                    defaults={
                        "descripcion": (
                            f"{nombre}: atención residencial con "
                            "materiales y alcance acordados con el cliente."
                        ),
                        "precio_base": Decimal("80000")
                        + Decimal(posicion * 20000),
                        "activo": True,
                    },
                )
                creados["Servicios"] += int(creado)
                servicios.append(servicio)

        # 4. Ofertas: aprobadas, pendientes y rechazadas.
        ofertas = []
        combinaciones = [
            (0, 0, "aprobado"),
            (0, 1, "aprobado"),
            (1, 2, "aprobado"),
            (1, 3, "aprobado"),
            (2, 10, "aprobado"),
            (2, 11, "aprobado"),
            (3, 4, "aprobado"),
            (7, 0, "aprobado"),
            (7, 1, "aprobado"),
            (9, 2, "aprobado"),
            (4, 6, "pendiente"),
            (5, 8, "pendiente"),
            (6, 9, "rechazado"),
            (8, 10, "pendiente"),
            (9, 3, "aprobado"),
        ]

        for indice, (indice_profesional, indice_servicio, estado) in enumerate(
            combinaciones, start=1
        ):
            profesional = profesionales[indice_profesional]
            servicio = servicios[indice_servicio]
            oferta, creado = ServicioProfesional.objects.get_or_create(
                servicio=servicio,
                profesional=profesional,
                defaults={
                    "precio": Decimal("65000") + Decimal(indice * 7000),
                    "estado_aprobacion": estado,
                },
            )
            creados["Ofertas profesionales"] += int(creado)
            ofertas.append(oferta)

        ofertas_aprobadas = [
            oferta
            for oferta in ofertas
            if oferta.estado_aprobacion == "aprobado"
            and oferta.profesional.estado_verificacion == "aprobado"
            and oferta.profesional.disponible
        ]

        if not ofertas_aprobadas:
            raise CommandError(
                "No hay ofertas aprobadas de profesionales disponibles."
            )

        # 5. Documentos privados ficticios para revisión de identidad.
        for indice, profesional in enumerate(profesionales, start=1):
            tipo_estado = profesional.estado_identidad
            observacion = f"[DEMO-SERVIHOME] Identidad profesional {indice:02d}"

            documento, creado = DocumentoVerificacion.objects.get_or_create(
                perfil=profesional,
                tipo="identidad",
                observacion=observacion,
                defaults={"estado": tipo_estado},
            )

            if creado:
                archivo = self.crear_pdf_documento(
                    profesional.usuario.get_full_name(),
                    "Identidad",
                )
                self.guardar_archivo(
                    documento.archivo,
                    f"demo_identidad_{indice:02d}.pdf",
                    archivo,
                )
                documento.save()
                creados["Documentos"] += 1

        # Documentos de experiencia para seis profesionales.
        for indice, profesional in enumerate(profesionales[:6], start=1):
            observacion = (
                f"[DEMO-SERVIHOME] Experiencia profesional {indice:02d}"
            )
            documento, creado = DocumentoVerificacion.objects.get_or_create(
                perfil=profesional,
                tipo="experiencia",
                observacion=observacion,
                defaults={
                    "estado": profesional.estado_verificacion,
                },
            )
            if creado:
                archivo = self.crear_pdf_documento(
                    profesional.usuario.get_full_name(),
                    "Experiencia",
                )
                self.guardar_archivo(
                    documento.archivo,
                    f"demo_experiencia_{indice:02d}.pdf",
                    archivo,
                )
                documento.save()
                creados["Documentos"] += 1

        # 6. Trabajos de portafolio con imágenes PNG válidas.
        trabajos_portafolio = [
            (0, 0, "Reparación de fuga en cocina"),
            (0, 1, "Instalación de lavamanos"),
            (1, 2, "Instalación de iluminación LED"),
            (1, 3, "Mantenimiento de tablero eléctrico"),
            (2, 10, "Limpieza profunda de apartamento"),
            (2, 11, "Limpieza detallada de baño"),
            (3, 4, "Restauración de puerta de madera"),
            (7, 0, "Cambio de tubería residencial"),
            (9, 2, "Adecuación de puntos de iluminación"),
            (9, 3, "Revisión de conexiones eléctricas"),
        ]

        for indice, (indice_profesional, indice_servicio, titulo) in enumerate(
            trabajos_portafolio, start=1
        ):
            profesional = profesionales[indice_profesional]
            servicio = servicios[indice_servicio]
            trabajo, creado = TrabajoPortafolio.objects.get_or_create(
                profesional=profesional,
                titulo=f"[DEMO] {titulo}",
                defaults={
                    "servicio": servicio,
                    "descripcion": (
                        f"Registro de demostración: {titulo.lower()}. "
                        "Imagen ilustrativa generada para el entorno de pruebas."
                    ),
                    "activo": True,
                },
            )
            if creado:
                imagen = self.crear_imagen_portafolio(titulo)
                self.guardar_archivo(
                    trabajo.imagen,
                    f"demo_portafolio_{indice:02d}.png",
                    imagen,
                )
                trabajo.save()
                creados["Trabajos de portafolio"] += 1

        # 7. Solicitudes con todos los estados.
        estados_solicitud = (
            ["pendiente"] * 5
            + ["aceptada"] * 4
            + ["en_proceso"] * 4
            + ["completada"] * 8
            + ["rechazada"] * 2
            + ["cancelada"]
        )

        solicitudes = []
        for indice, estado in enumerate(estados_solicitud, start=1):
            oferta = ofertas_aprobadas[(indice - 1) % len(ofertas_aprobadas)]
            cliente = clientes[(indice - 1) % len(clientes)]
            precio = Decimal("85000") + Decimal(indice * 6500)

            datos = {
                "cliente": cliente,
                "profesional": oferta.profesional,
                "servicio": oferta.servicio,
                "descripcion": (
                    f"[DEMO-SERVIHOME] Solicitud {indice:02d}: "
                    f"{oferta.servicio.nombre} para vivienda."
                ),
                "direccion_servicio": self.DIRECCIONES[
                    (indice - 1) % len(self.DIRECCIONES)
                ],
                "fecha_solicitada": ahora
                + timedelta(days=(indice % 18) - 12),
                "estado": estado,
            }

            if estado in ("aceptada", "en_proceso", "completada"):
                datos["precio_acordado"] = precio
                datos["codigo_inicio"] = f"{310000 + indice:06d}"

            if estado in ("en_proceso", "completada"):
                datos["codigo_finalizacion"] = f"{420000 + indice:06d}"

            solicitud, creado = SolicitudServicio.objects.get_or_create(
                descripcion=datos["descripcion"],
                defaults=datos,
            )
            creados["Solicitudes"] += int(creado)
            solicitudes.append(solicitud)

        completadas = [s for s in solicitudes if s.estado == "completada"]
        pendientes = [s for s in solicitudes if s.estado == "pendiente"]
        rechazadas = [s for s in solicitudes if s.estado == "rechazada"]

        # 8. Propuestas aceptadas, pendientes y rechazadas.
        propuestas_datos = []
        for solicitud in completadas[:4]:
            propuestas_datos.append(
                (solicitud, solicitud.profesional, solicitud.precio_acordado, "aceptada")
            )
        for indice, solicitud in enumerate(pendientes[:3], start=1):
            propuestas_datos.append(
                (
                    solicitud,
                    solicitud.profesional,
                    Decimal("100000") + Decimal(indice * 12000),
                    "pendiente",
                )
            )
        for solicitud in rechazadas[:1]:
            propuestas_datos.append(
                (
                    solicitud,
                    solicitud.profesional,
                    Decimal("145000"),
                    "rechazada",
                )
            )

        for solicitud, proponente, precio, estado in propuestas_datos:
            propuesta, creado = PropuestaPrecio.objects.get_or_create(
                solicitud=solicitud,
                proponente=proponente,
                precio=precio,
                defaults={"estado": estado},
            )
            creados["Propuestas"] += int(creado)

        # 9. Reseñas: solo solicitudes completadas.
        comentarios = [
            "El profesional llegó puntual y explicó claramente el trabajo.",
            "Buen resultado, dejó el espacio limpio y organizado.",
            "Atención amable y solución efectiva al inconveniente.",
            "Trabajo cuidadoso y precio acorde con lo conversado.",
            "Servicio rápido; recomiendo mejorar la comunicación previa.",
            "Cumplió con lo acordado y entregó recomendaciones útiles.",
            "Muy buena calidad en los acabados.",
            "La reparación quedó funcionando correctamente.",
        ]

        for indice, solicitud in enumerate(completadas, start=1):
            resena, creado = Resena.objects.get_or_create(
                solicitud=solicitud,
                defaults={
                    "calificacion": [5, 4, 5, 4, 3, 5, 4, 5][indice - 1],
                    "comentario": comentarios[indice - 1],
                },
            )
            creados["Reseñas"] += int(creado)

        # 10. Pagos para las ocho solicitudes completadas.
        estados_pago = [
            "pagado",
            "pagado",
            "pagado",
            "pagado",
            "pendiente",
            "pendiente",
            "fallido",
            "reembolsado",
        ]
        metodos_pago = [
            "transferencia",
            "tarjeta",
            "efectivo",
            "pasarela",
            "transferencia",
            "efectivo",
            "tarjeta",
            "pasarela",
        ]

        for indice, solicitud in enumerate(completadas, start=1):
            estado = estados_pago[indice - 1]
            pago, creado = Pago.objects.get_or_create(
                solicitud=solicitud,
                defaults={
                    "monto_total": solicitud.precio_acordado,
                    "porcentaje_comision": Decimal("10.00"),
                    "metodo": metodos_pago[indice - 1],
                    "estado": estado,
                    "referencia": f"DEMO-PAGO-{indice:03d}",
                    "fecha_pago": (
                        ahora - timedelta(days=indice)
                        if estado in ("pagado", "reembolsado")
                        else None
                    ),
                },
            )
            creados["Pagos"] += int(creado)

        # 11. Incidentes reportados por clientes o profesionales.
        tipos_incidente = [
            "danos_materiales",
            "incumplimiento",
            "comportamiento",
            "cobro_indebido",
            "otro",
            "emergencia",
        ]
        estados_incidente = [
            "pendiente",
            "en_revision",
            "resuelto",
            "rechazado",
            "pendiente",
            "resuelto",
        ]
        descripciones_incidente = [
            "Se reportó un daño menor en un elemento cercano al área de trabajo.",
            "El horario acordado no se cumplió y se solicita revisión.",
            "Se solicita revisar la comunicación durante la prestación del servicio.",
            "El valor cobrado no coincide con el precio acordado en la solicitud.",
            "El cliente solicita acompañamiento para aclarar el cierre del servicio.",
            "Se reportó una situación que requiere revisión prioritaria.",
        ]

        for indice, solicitud in enumerate(completadas[:6]):
            estado = estados_incidente[indice]
            reportante = (
                solicitud.cliente if indice % 2 == 0
                else solicitud.profesional
            )
            incidente, creado = Incidente.objects.get_or_create(
                solicitud=solicitud,
                tipo=tipos_incidente[indice],
                defaults={
                    "reportado_por": reportante,
                    "descripcion": descripciones_incidente[indice],
                    "estado": estado,
                    "respuesta_administrador": (
                        "Caso revisado por el equipo de administración."
                        if estado in ("resuelto", "rechazado")
                        else ""
                    ),
                },
            )
            creados["Incidentes"] += int(creado)

        # Resumen de registros nuevos en esta ejecución.
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("RESUMEN DE DATOS DE DEMOSTRACIÓN")
        )
        total = 0
        for nombre, cantidad in creados.items():
            self.stdout.write(f"{nombre}: {cantidad} nuevos")
            total += cantidad

        self.stdout.write(f"Total de registros nuevos: {total}")
        self.stdout.write(
            "Cuentas creadas: 10 clientes y 10 profesionales."
        )
        self.stdout.write(
            "Estados incluidos: verificación, identidad, disponibilidad, "
            "ofertas, solicitudes, propuestas, pagos e incidentes."
        )
