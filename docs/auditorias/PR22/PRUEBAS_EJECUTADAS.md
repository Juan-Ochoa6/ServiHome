# Registro de pruebas ejecutadas – PR #22

## 1. Identificación

- Proyecto: ServiHome
- PR auditado: #22
- Commit auditado: c579d28
- Fecha: 26 de noviembre de 2026
- Entorno: local, carpeta ServiHome-PR22-audit

## 2. Pruebas automatizadas

| ID | Actividad | Resultado |
|---|---|---|
| P01 | Ejecución de 20 pruebas específicas | 20 aprobadas |
| P02 | Ejecución de la suite completa | 147 aprobadas |
| P03 | Verificación del resultado final | OK |

La primera ejecución completa presentó fallos relacionados con la configuración de FERNET_KEY. Después de configurar la variable local, la suite terminó correctamente.

## 3. Comprobaciones de configuración y Git

| Comando o actividad | Objetivo | Resultado |
|---|---|---|
| `python manage.py check` | Revisar configuración Django | Sin problemas |
| `git diff --check 354dba7..c579d28` | Revisar errores de espacios en blanco | Sin errores |
| `python manage.py showmigrations` | Identificar migraciones aplicadas y pendientes | Se identificaron dos pendientes |
| `python manage.py migrate --plan` | Consultar operaciones previstas | Plan revisado, sin aplicar |
| `python manage.py makemigrations --check --dry-run` | Comprobar cambios de modelos pendientes | No changes detected |

## 4. Pruebas de autorización

Se revisó el permiso `EsAdminOFinanzas` y se comprobaron las respuestas de autorización para los endpoints:

- `/api/admin/finanzas/`
- `/api/admin/estadisticas/`

| Perfil | Código HTTP observado |
|---|---:|
| Administrador | 200 |
| Finanzas | 200 |
| Cliente | 403 |
| Anónimo | 401 |

**Limitación:** las comprobaciones autenticadas se realizaron con `APIRequestFactory` y métodos GET simulados. Validan la autorización, no el cálculo real de las respuestas.

## 5. Pruebas funcionales en navegador

### P05 – Acceso al panel financiero como administrador

1. Iniciar el backend local.
2. Iniciar el frontend con Vite.
3. Iniciar sesión con el usuario administrador de QA.
4. Abrir el panel financiero.
5. Comprobar las tarjetas y la tabla de pagos.

Resultado observado:
- Total pagado: $50.000.
- Comisión ServiHome: $5.000.
- Total profesionales: $45.000.
- Un pago confirmado.

### P06 – Agrupación de información financiera

Se probaron las agrupaciones:

- Día.
- Semana.
- Mes.
- Año.

Resultado: las cuatro opciones mostraron los datos correspondientes al periodo seleccionado.

### P07 – Acceso al panel de estadísticas

1. Iniciar sesión con `finanzas_qa1`.
2. Completar la configuración inicial de MFA.
3. Acceder a `/finanzas`.
4. Abrir la sección de estadísticas generales.
5. Revisar los indicadores presentados.

Resultado: el panel cargó y mostró los indicadores de solicitudes, profesionales, ofertas y servicios más solicitados.

### P08 – Restricción de rutas por rol

Con la sesión del usuario `finanzas_qa1` activa:

- `/finanzas`: acceso permitido.
- `/panel`: redirección al inicio de sesión.

Resultado: comportamiento observado coherente con la protección de rutas del frontend.

### P09 – Autenticación MFA

Se revisó el flujo de primer acceso:

1. Envío de credenciales.
2. Generación del desafío.
3. Presentación del QR para configurar MFA.
4. Verificación del código.
5. Activación de MFA.
6. Entrega de tokens JWT y rol.

Resultado: se completó el acceso con el usuario de QA.

## 6. Revisión estática del frontend y backend

Se inspeccionaron:

- `servicios/views.py`
- `servicios/urls.py`
- `servicios/tests.py`
- `usuarios/views.py`
- `usuarios/models.py`
- `usuarios/migrations/0014_alter_perfil_rol.py`
- `servicios/migrations/0013_pago_comprobante.py`
- `frontend/src/App.jsx`
- `frontend/src/auth/AuthProvider.jsx`
- `frontend/src/auth/RutaProtegida.jsx`
- `frontend/src/auth/useAuth.js`
- `frontend/src/components/PanelEstadisticas.jsx`
- `frontend/src/components/InicioFinanzas.jsx`
- `frontend/src/services/admin.js`

Resultado: se revisó la correspondencia entre rutas, permisos, respuestas del backend y componentes del frontend. No se identificó un desajuste funcional demostrado.

## 7. Migraciones

Migraciones pendientes identificadas:

- `servicios.0013_pago_comprobante`
- `usuarios.0014_alter_perfil_rol`

Se revisaron los archivos de migración y el plan de ejecución.

**No se ejecutó `migrate`.** La base de datos local de QA no se modificó mediante la aplicación de estas migraciones.

## 8. Herramientas utilizadas

- Git.
- Git worktree.
- Python.
- Django.
- Django REST Framework.
- MySQL.
- Node.js.
- npm.
- Vite.
- PowerShell.
- Brave Developer Tools.

## 9. Limitaciones y pendientes

1. Agregar pruebas automatizadas específicas para estadísticas.
2. Agregar una prueba automatizada explícita del rol finanzas en `FinanzasTests`.
3. Validar las migraciones en una base de datos independiente.
4. Realizar una prueba de despliegue.
5. Revisar por separado las vulnerabilidades moderadas reportadas por npm.

## 10. Resultado general

Se ejecutaron pruebas automatizadas, comprobaciones de autorización, pruebas funcionales en navegador y revisión estática.

Resultado registrado: 147 pruebas automatizadas aprobadas y funcionamiento observado correcto en los escenarios funcionales ejecutados.

No se identificaron defectos funcionales demostrados dentro del alcance revisado.
