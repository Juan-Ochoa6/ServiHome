# Registro de pruebas ejecutadas – PR #22

## 1. Identificación

- **Proyecto:** ServiHome
- **PR auditado:** #22 – Integra panel de finanzas y estadísticas
- **Commit auditado:** `c579d28`
- **Commit de integración:** `0897ddb`
- **Fecha:** 26 de noviembre de 2026
- **Entorno:** local, en el worktree aislado `ServiHome-PR22-audit`.

## 2. Clasificación de resultados

Se utilizan las siguientes categorías:

- **APROBADA:** prueba ejecutada y resultado esperado observado.
- **PARCIAL:** se comprobó solo una parte del comportamiento.
- **REVISIÓN ESTÁTICA:** inspección de código o configuración, sin validar su ejecución integral.
- **NO VERIFICADA:** no existe evidencia suficiente para confirmar el comportamiento.
- **PENDIENTE:** requiere una actividad adicional.

## 3. Pruebas automatizadas

| ID | Actividad | Resultado |
|---|---|---|
| P01 | Ejecución de 20 pruebas específicas seleccionadas | APROBADA: 20 aprobadas |
| P02 | Ejecución de la suite completa existente | APROBADA: 147 aprobadas |
| P03 | Comprobación del resultado final de la suite | APROBADA: resultado `OK` |

La primera ejecución de la suite completa presentó fallos relacionados con la ausencia de configuración de `FERNET_KEY` en el entorno local. Después de configurar la variable, la suite terminó correctamente.

La ejecución satisfactoria demuestra que las 147 pruebas existentes pasaron en ese entorno. No demuestra que todos los escenarios del PR estén cubiertos por pruebas automatizadas.

**Tiempo registrado de la ejecución completa:** 378.167 segundos.

## 4. Comprobaciones de configuración y Git

| Comando o actividad | Resultado | Clasificación |
|---|---|---|
| `python manage.py check` | Django no reportó problemas | APROBADA |
| `git diff --check 354dba7..c579d28` | Sin errores de espacios en blanco | APROBADA |
| `python manage.py showmigrations` | Se identificaron dos migraciones pendientes | REVISIÓN ESTÁTICA |
| `python manage.py migrate --plan` | Se revisó el plan, sin aplicarlo | REVISIÓN ESTÁTICA |
| `python manage.py makemigrations --check --dry-run` | `No changes detected` | APROBADA |

La comprobación de Django no sustituye las pruebas funcionales ni de integración.

## 5. Comprobaciones de autorización del backend

Se inspeccionó `EsAdminOFinanzas` y se realizaron comprobaciones mediante `APIRequestFactory` para:

- `GET /api/admin/finanzas/`
- `GET /api/admin/estadisticas/`

| Perfil | Código HTTP observado |
|---|---:|
| Administrador | 200 |
| Finanzas | 200 |
| Cliente | 403 |
| Anónimo | 401 |

**Clasificación: PARCIAL.**

Los GET fueron simulados y las comprobaciones se enfocaron en la autorización. No constituyen pruebas de integración de los endpoints ni validan los cálculos, la estructura JSON o los datos devueltos por las vistas.

Por tanto, estos resultados no deben presentarse como una validación integral de ambos endpoints.

## 6. Pruebas funcionales en navegador

### P05 – Visualización del panel financiero como administrador

**Clasificación: APROBADA para la visualización observada.**

Actividades:
1. Iniciar el backend local.
2. Iniciar el frontend mediante Vite.
3. Iniciar sesión con un usuario administrador de QA.
4. Abrir el panel financiero.
5. Revisar las tarjetas y la tabla de pagos.

Valores observados en la base de datos local de QA:

| Indicador | Valor observado |
|---|---:|
| Total pagado | $50.000 |
| Ganancia de ServiHome | $5.000 |
| Total para profesionales | $45.000 |
| Pagos confirmados | 1 |

Estos valores corresponden a los datos existentes en ese entorno. No representan una validación de todos los escenarios posibles de cálculo financiero.

### P06 – Opciones de agrupación financiera

**Clasificación: PARCIAL.**

Se seleccionaron las agrupaciones:
- Día.
- Semana.
- Mes.
- Año.

Se observó que las opciones presentaban la información correspondiente a la agrupación seleccionada.

No se realizó una comparación independiente y exhaustiva de todos los resultados con cálculos de referencia para cada periodo.

### P07 – Visualización del panel de estadísticas

**Clasificación: PARCIAL.**

Actividades:
1. Iniciar sesión con el usuario de QA `finanzas_qa1`.
2. Completar su configuración inicial de MFA.
3. Acceder a `/finanzas`.
4. Abrir la sección de estadísticas generales.
5. Observar los indicadores presentados.

Se observó la carga del panel y la presentación de indicadores de solicitudes, profesionales, ofertas y servicios más solicitados.

**Limitación:** no se contrastó exhaustivamente cada indicador con consultas independientes a la base de datos. La visualización no demuestra por sí sola la exactitud de todos los cálculos del backend.

### P08 – Protección de rutas del frontend por rol

**Clasificación: APROBADA para el recorrido observado.**

Con la sesión del usuario `finanzas_qa1` activa:
- `/finanzas`: acceso permitido.
- `/panel`: redirección al inicio (`/`).

Esta comprobación corresponde a la protección de rutas del frontend. No sustituye las pruebas de autorización del backend.

### P09 – Configuración inicial y acceso mediante MFA

**Clasificación: APROBADA para el flujo completado con el usuario de QA.**

Se completó el proceso de acceso que incluyó:
1. Envío de credenciales.
2. Presentación del proceso de configuración inicial de MFA.
3. Configuración mediante QR.
4. Verificación del código.
5. Activación de MFA.
6. Obtención de la sesión y tokens JWT.

El resultado acredita el flujo completado con ese usuario en el entorno local. No representa una prueba exhaustiva de concurrencia, expiración, recuperación o todos los escenarios de error de MFA.

## 7. Revisión estática del código

Se inspeccionaron archivos del backend y frontend, entre ellos:

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

**Clasificación: REVISIÓN ESTÁTICA.**

Se inspeccionó la relación entre rutas, permisos, vistas, modelos y componentes. Esta revisión no demuestra que todos los flujos funcionen correctamente ni sustituye las pruebas de integración.

## 8. Pendientes concretos del backend

Los siguientes puntos representan limitaciones de cobertura o validaciones que no se completaron. No constituyen, por sí solos, defectos funcionales demostrados.

### BACK-01 – Pruebas automatizadas del endpoint de estadísticas

**Endpoint:** `GET /api/admin/estadisticas/`

**Estado: NO VERIFICADO mediante pruebas automatizadas específicas.**

No se encontraron pruebas automatizadas específicas para `EstadisticasGeneralesAPIView`.

Se recomienda agregar casos que comprueben:

- Cantidad de servicios completados.
- Cantidad de solicitudes por estado.
- Cantidad de profesionales por estado de verificación.
- Cantidad de ofertas por estado de aprobación.
- Servicios más solicitados.
- Respuesta cuando no existen registros.
- Restricciones de acceso según el rol.

**Criterio de cierre:** las pruebas deben contrastar los valores devueltos por el endpoint con datos de prueba conocidos.

### BACK-02 – Prueba explícita del rol Finanzas en FinanzasTests

**Endpoint:** `GET /api/admin/finanzas/`

**Estado: NO CUBIERTO explícitamente en la clase `FinanzasTests`.**

En la revisión de `FinanzasTests` se identificaron casos para administrador, cliente y usuario anónimo, pero no un caso específico para el rol `finanzas`.

Se recomienda agregar una prueba que compruebe:

- Que un usuario autenticado con rol `finanzas` puede consultar el resumen.
- Que recibe la estructura y los valores esperados.
- Que un cliente no obtiene acceso.
- Que un usuario anónimo no obtiene acceso.

**Criterio de cierre:** prueba automatizada ejecutada con un usuario cuyo rol sea `finanzas`.

### BACK-03 – Pruebas de integración reales de los endpoints

**Endpoints:**
- `GET /api/admin/finanzas/`
- `GET /api/admin/estadisticas/`

**Estado: PARCIAL.**

Las comprobaciones realizadas con `APIRequestFactory` se limitaron a autorización y utilizaron GET simulados.

Falta ejecutar solicitudes de integración contra los endpoints reales y comprobar:

- Código HTTP.
- Estructura y tipos de los campos JSON.
- Valores devueltos con registros de prueba controlados.
- Cálculos financieros.
- Conteos y agrupaciones de estadísticas.
- Acceso permitido y denegado según el rol.

**Criterio de cierre:** pruebas de integración que ejecuten las vistas y validen sus respuestas con datos controlados.

### BACK-04 – Aplicación y validación de migraciones

**Migraciones identificadas:**
- `servicios.0013_pago_comprobante`
- `usuarios.0014_alter_perfil_rol`

**Estado: NO VERIFICADO mediante aplicación real.**

Se inspeccionaron los archivos y el plan de ejecución, pero las migraciones no se aplicaron durante esta auditoría.

Falta:
- Aplicarlas en una base de datos independiente.
- Comprobar que finalizan sin errores.
- Verificar los cambios de esquema.
- Comprobar que los modelos funcionan después de la migración.

**Criterio de cierre:** evidencia de aplicación exitosa y comprobaciones posteriores en una base de datos de prueba.

### BACK-05 – Suite automatizada existente

**Estado: APROBADA en el entorno local utilizado.**

La suite existente terminó con 147 pruebas aprobadas después de configurar `FERNET_KEY`.

Este resultado acredita la ejecución satisfactoria de las pruebas disponibles. No cierra los pendientes BACK-01, BACK-02 ni BACK-03, porque la ejecución de una suite no demuestra que existan los casos específicos requeridos.

## 9. Aspectos fuera del alcance

- El campo `Pago.comprobante` y su migración son anteriores al PR #22; no deben atribuirse a este cambio.
- La integración con Mercado Pago corresponde a un commit posterior y quedó fuera del alcance.
- No se aplicaron las migraciones identificadas.
- No se realizó una prueba de despliegue en producción.
- Las vulnerabilidades moderadas reportadas por npm requieren una revisión independiente. No se ejecutó `npm audit fix`.

## 10. Resultado y limitaciones

Se ejecutaron pruebas automatizadas, comprobaciones de autorización, recorridos funcionales en navegador y revisión estática.

La suite existente finalizó con 147 pruebas aprobadas. Se observó la visualización de los paneles financiero y de estadísticas en el entorno local de QA.

Sin embargo, no se completó una validación de integración de los dos endpoints con comprobación exhaustiva de sus respuestas y cálculos. Tampoco se aplicaron las migraciones en una base de datos independiente.

Por tanto, los resultados permiten documentar los escenarios ejecutados, pero no certificar el funcionamiento integral del backend ni la ausencia de defectos.

Los pendientes BACK-01 a BACK-04 requieren seguimiento antes de considerar completa la validación del backend del PR #22.
