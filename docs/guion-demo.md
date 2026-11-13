# Guion de demostración — ServiHome

Duración estimada: 10 minutos.

## Antes de empezar

1. Backend y frontend corriendo.
2. Datos frescos: `python manage.py poblar_datos` y `python manage.py poblar_pendientes`.
3. Tener **ya configurado Microsoft Authenticator** con tres cuentas (un cliente, un
   profesional y un administrador): iniciar sesión en cada una una vez antes de la demo.
4. Dos ventanas del navegador: una normal y una de incógnito. Así se ven dos roles a la vez.

## Recorrido

| # | Rol | Qué mostrar | Qué se ve |
|---|---|---|---|
| 1 | Visitante | Inicio, Servicios y búsqueda por categoría | Catálogo real con profesionales aprobados |
| 2 | Cliente | Perfil de un profesional y sus trabajos | Servicios, precios y portafolio |
| 3 | Cliente | Solicitar un servicio | Formulario, resumen y solicitud Pendiente |
| 4 | Cliente | Negociar precio: proponer un valor | Propuesta pendiente, a la espera de respuesta |
| 5 | Profesional | Solicitudes recibidas, contraoferta | Historial de propuestas con sus estados |
| 6 | Cliente | Aceptar la contraoferta | Solicitud Aceptada con precio acordado |
| 7 | Profesional | Mi cuenta: estado de verificación y documentos | Estados de identidad, perfil y disponibilidad |
| 8 | Administrador | Panel: documentos, profesionales y ofertas | Aprobar en el orden recomendado |
| 9 | Profesional | Mis servicios y Portafolio | Oferta pendiente de aprobación y trabajos con foto |

## Puntos para destacar

- Cada rol ve un menú distinto y no puede entrar a pantallas de otro rol.
- El frontend no calcula estados ni dinero: muestra lo que decide el backend.
- Seguridad: inicio de sesión con verificación en dos pasos y códigos de recuperación.

## Lo que aún no está

Pagos, código de inicio, botón de pánico y notificaciones: pendientes de las decisiones
de requerimientos y de sus endpoints.