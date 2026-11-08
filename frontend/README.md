# ServiHome — Frontend

Interfaz web de ServiHome, una plataforma que conecta clientes con profesionales
que ofrecen servicios para el hogar.

## Tecnologías

- React y Vite
- React Router (navegación por páginas)
- CSS propio, sin frameworks de estilos
- ESLint

Consume la API REST del backend (Django REST Framework) con autenticación JWT y
verificación en dos pasos con Microsoft Authenticator.

## Requisitos

- Node.js (versión LTS reciente) y npm
- El backend corriendo en `http://127.0.0.1:8000` (consulta el README del backend)

## Instalación y ejecución

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`.

### Configuración opcional

Si el backend corre en otra dirección, copia `.env.example` como `.env` y cambia
`VITE_API_URL`. Por defecto usa `http://127.0.0.1:8000/api`.

## Scripts

| Comando | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo |
| `npm run build` | Compila para producción en `dist/` |
| `npm run preview` | Sirve la compilación para probarla |
| `npm run lint` | Revisa el código con ESLint |

## Datos de prueba

Desde la carpeta del backend, con su entorno virtual activo:

```bash
python manage.py poblar_datos       # categorías, servicios, profesionales y ofertas aprobadas
python manage.py poblar_pendientes  # profesionales y ofertas pendientes, para probar el panel de administrador
```

`poblar_datos` imprime al final la contraseña de los profesionales de prueba.
Son datos solo para desarrollo. La primera vez que un usuario inicia sesión debe
configurar Microsoft Authenticator con el código QR y guardar sus códigos de recuperación.

## Roles y pantallas

| Rol | Pantallas |
|---|---|
| Visitante | Inicio, Servicios, Profesionales, perfil de un profesional, Registro, Login |
| Cliente | Lo anterior, Solicitudes (con negociación de precio), Nueva solicitud, Mi cuenta |
| Profesional | Solicitudes recibidas, Mis servicios, Portafolio, Mi cuenta (verificación, documentos y disponibilidad) |
| Administrador | Panel: revisión de documentos, aprobación de profesionales y de ofertas |

## Flujo principal

1. El cliente busca un servicio, elige un profesional y crea una solicitud.
2. Cliente y profesional negocian el precio con propuestas y contrapropuestas.
3. Al aceptarse un precio, la solicitud queda aceptada.
4. Para aparecer en el catálogo, el profesional sube su documento de identidad, el
   administrador aprueba su identidad y su perfil, el profesional activa su
   disponibilidad y publica servicios que el administrador aprueba.

## Estructura de `src`

```
auth/         sesión, contexto y rutas protegidas por rol
components/   piezas reutilizables (menú, formularios, negociación, etc.)
hooks/        useCargar: carga de datos con estados de carga y error
pages/        una página por pantalla
services/     llamadas a la API (api.js es la base; el resto agrupa endpoints)
utils/        formato de precios y fechas, etiquetas de estados
assets/       imágenes
```

## Pendiente

Depende de decisiones de requerimientos y de nuevos endpoints del backend:
pagos con tarjeta y reserva, código de inicio y llegada, completar el servicio,
botón de pánico e incidentes, notificaciones y recuperación de contraseña.

## Créditos

Los iconos son de [Flaticon](https://www.flaticon.es). Los créditos completos
aparecen en el pie de página de la aplicación.