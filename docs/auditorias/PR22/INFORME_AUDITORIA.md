# Informe de auditoría QA – PR #22

## 1. Información general

- **Proyecto:** ServiHome
- **Pull Request:** #22 – Integra panel de finanzas y estadísticas
- **Commit auditado:** `c579d28`
- **Commit de integración:** `0897ddb`
- **Fecha de auditoría:** 26 de noviembre de 2026
- **Entorno:** entorno local de auditoría, aislado mediante Git worktree.
- **Alcance:** backend, frontend, permisos, autenticación, panel financiero, estadísticas y migraciones relacionadas con el PR.

## 2. Objetivo

Evaluar la implementación incorporada en el PR #22, centrándose en el panel financiero, las estadísticas generales y el acceso diferenciado según el rol del usuario.

La auditoría incluyó ejecución de pruebas automatizadas, comprobaciones de autorización, recorridos funcionales en navegador y revisión estática del código.

El alcance de las conclusiones se limita a las actividades efectivamente ejecutadas. No representa una certificación integral del sistema.

## 3. Entorno y herramientas utilizadas

- Git y Git worktree para mantener aislado el código auditado.
- Python y Django para ejecutar el backend y las pruebas.
- Django REST Framework.
- MySQL como base de datos local de QA.
- Node.js, npm y Vite para ejecutar el frontend.
- Brave y herramientas de desarrollo del navegador.
- PowerShell para inspección y ejecución de comandos.

No se incluyen contraseñas, tokens, claves secretas ni datos sensibles en esta documentación.

## 4. Actividades y resultados

Para interpretar los resultados se utilizan estas categorías:

- **APROBADA:** prueba ejecutada y resultado esperado observado.
- **PARCIAL:** se comprobó una parte del comportamiento, pero no el flujo completo.
- **REVISIÓN ESTÁTICA:** inspección de código o configuración sin validar integralmente su ejecución.
- **NO VERIFICADA:** no existe evidencia suficiente para confirmar el comportamiento.
- **PENDIENTE:** requiere una actividad adicional.

### 4.1. Revisión del código

Se inspeccionaron archivos modificados por el PR, vistas, rutas, permisos, modelos, migraciones, pruebas automatizadas y componentes del frontend.

**Clasificación: REVISIÓN ESTÁTICA.**

Se revisó la correspondencia entre rutas, permisos, vistas y componentes. Esta actividad no demuestra que todos los flujos funcionen correctamente ni sustituye las pruebas de integración.

### 4.2. Comprobaciones de configuración y Git

Se ejecutaron:

- `python manage.py check`
- `git diff --check 354dba7..c579d28`

Resultados:
- Django no reportó problemas en la comprobación de configuración.
- Git no reportó errores de espacios en blanco en las diferencias revisadas.

**Clasificación: APROBADA para las comprobaciones ejecutadas.**

Estas comprobaciones no representan una validación funcional de los endpoints.

### 4.3. Pruebas automatizadas

Se ejecutaron pruebas específicas y posteriormente la suite completa existente.

Resultados:
- 20 pruebas específicas aprobadas.
- 147 pruebas aprobadas en la suite completa.
- Tiempo registrado para la suite completa: 378.167 segundos.
- Resultado final: `OK`.

La primera ejecución completa presentó fallos relacionados con la configuración de `FERNET_KEY` en el entorno local. Después de configurar la variable, la suite terminó correctamente.

**Clasificación: APROBADA para las pruebas existentes ejecutadas.**

La ejecución satisfactoria no demuestra que todos los escenarios del PR estén cubiertos. En particular, no sustituye los casos específicos pendientes para estadísticas, permisos del rol Finanzas e integración de endpoints.

### 4.4. Comprobaciones de autorización del backend

Se revisó la clase `EsAdminOFinanzas` y se realizaron comprobaciones con `APIRequestFactory` para:

- `GET /api/admin/finanzas/`
- `GET /api/admin/estadisticas/`

Resultados observados:

| Perfil | Código HTTP |
|---|---:|
| Administrador | 200 |
| Finanzas | 200 |
| Cliente | 403 |
| Usuario anónimo | 401 |

**Clasificación: PARCIAL.**

Los GET fueron simulados y las comprobaciones se enfocaron en la autorización. No se validaron las respuestas reales de ambos endpoints, sus estructuras JSON ni sus cálculos.

Por tanto, estos resultados no deben interpretarse como pruebas de integración completas.

### 4.5. Panel financiero

Se inició el backend y el frontend localmente y se ingresó con un usuario administrador de QA.

Se observaron los siguientes valores en la base de datos local:

| Indicador | Valor observado |
|---|---:|
| Total pagado | $50.000 |
| Ganancia de ServiHome | $5.000 |
| Total para profesionales | $45.000 |
| Pagos confirmados | 1 |

También se seleccionaron las agrupaciones por día, semana, mes y año, observando la presentación de información al cambiar de opción.

**Clasificación: PARCIAL.**

Se comprobó la visualización del panel y el comportamiento observado al seleccionar agrupaciones. No se realizó una comparación independiente y exhaustiva de todos los cálculos con resultados de referencia.

Los valores registrados corresponden exclusivamente a los datos existentes en la base de QA utilizada.

### 4.6. Panel de estadísticas

Se utilizó el usuario local de QA `finanzas_qa1`, con rol `finanzas`. Se completó su configuración inicial de MFA y se accedió a `/finanzas`.

Se observó la presentación de indicadores relacionados con solicitudes, profesionales, ofertas y servicios más solicitados.

**Clasificación: PARCIAL.**

Se comprobó la carga y visualización del panel. No se contrastó exhaustivamente cada indicador con consultas independientes a la base de datos ni se validaron todos los cálculos del backend.

La visualización de los indicadores no demuestra por sí sola su exactitud.

### 4.7. Autenticación y protección de rutas

Se completó con el usuario de QA el proceso de configuración inicial de MFA y acceso a la aplicación.

También se observó:
- Acceso a `/finanzas` con el rol `finanzas`.
- Redirección desde `/panel` hacia `/` con ese mismo rol.

Se inspeccionaron `AuthProvider.jsx`, `RutaProtegida.jsx` y los componentes relacionados con la sesión.

**Clasificación: PARCIAL.**

Se completaron los recorridos indicados y se revisó estáticamente la protección de rutas. No se considera validado exhaustivamente el conjunto de escenarios de autenticación, expiración de tokens, concurrencia, recuperación de sesión y errores de MFA.

### 4.8. Revisión de migraciones

Se identificaron dos migraciones pendientes:

- `servicios.0013_pago_comprobante`
- `usuarios.0014_alter_perfil_rol`

Se inspeccionaron sus archivos y se revisó el plan de ejecución. También se ejecutó `makemigrations --check --dry-run`, que indicó `No changes detected`.

**Clasificación: REVISIÓN ESTÁTICA.**

Las migraciones no se aplicaron durante esta auditoría. Por tanto, no se verificó su ejecución real ni el estado del esquema después de aplicarlas.

## 5. Hallazgos y pendientes del backend

Los siguientes puntos representan deficiencias de cobertura o validaciones pendientes. No constituyen por sí solos defectos funcionales demostrados.

### BACK-01 – Falta de pruebas automatizadas específicas para estadísticas

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

### BACK-02 – Falta de prueba explícita del rol Finanzas en FinanzasTests

**Endpoint:** `GET /api/admin/finanzas/`

**Estado: NO CUBIERTO explícitamente en `FinanzasTests`.**

En la revisión de la clase se encontraron casos para administrador, cliente y usuario anónimo, pero no un caso específico para el rol `finanzas`.

Se recomienda agregar una prueba que compruebe:
- Acceso permitido para un usuario autenticado con rol `finanzas`.
- Estructura y valores esperados de la respuesta.
- Acceso denegado para cliente.
- Acceso denegado para usuario anónimo.

**Criterio de cierre:** prueba automatizada ejecutada con un usuario cuyo rol sea `finanzas`.

### BACK-03 – Falta de pruebas de integración reales de los endpoints

**Endpoints:**
- `GET /api/admin/finanzas/`
- `GET /api/admin/estadisticas/`

**Estado: PARCIAL.**

Las comprobaciones realizadas con `APIRequestFactory` se limitaron a autorización y utilizaron GET simulados.

Falta ejecutar pruebas de integración que comprueben:
- Códigos HTTP.
- Estructura y tipos de los campos JSON.
- Valores devueltos con registros de prueba controlados.
- Cálculos financieros.
- Conteos y agrupaciones de estadísticas.
- Acceso permitido y denegado según el rol.

**Criterio de cierre:** pruebas que ejecuten las vistas y validen sus respuestas con datos controlados.

### BACK-04 – Falta de aplicación y validación de migraciones

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

### BACK-05 – Ejecución de la suite automatizada existente

**Estado: APROBADA en el entorno local utilizado.**

La suite existente terminó con 147 pruebas aprobadas después de configurar `FERNET_KEY`.

Este resultado acredita la ejecución satisfactoria de las pruebas disponibles. No cierra los pendientes BACK-01, BACK-02 ni BACK-03, porque no demuestra que existan los casos específicos requeridos.

### QA-PR22-06 – Comentario incompleto de roles en frontend

**Tipo:** observación menor de documentación interna.

En `frontend/src/auth/AuthProvider.jsx`, un comentario enumera los roles cliente, profesional y administrador, pero omite el rol `finanzas`.

Se recomienda actualizar el comentario para mantener la documentación interna coherente. La observación corresponde al comentario, no a un defecto funcional demostrado del mecanismo de autenticación.

## 6. Aspectos fuera del alcance

- El campo `Pago.comprobante` y su migración son anteriores al PR #22 y no deben atribuirse a este cambio.
- La integración con Mercado Pago corresponde a un commit posterior y quedó fuera del alcance.
- No se aplicaron las migraciones identificadas.
- No se realizó una prueba de despliegue en producción.
- Las vulnerabilidades moderadas reportadas por npm requieren una revisión independiente. No se ejecutó `npm audit fix`.

## 7. Conclusión

Durante la auditoría se ejecutaron pruebas automatizadas, comprobaciones de autorización, recorridos funcionales en navegador y revisión estática del código.

La suite automatizada existente finalizó con 147 pruebas aprobadas, después de configurar `FERNET_KEY` en el entorno local.

Se observó la visualización de los paneles financiero y de estadísticas con los datos disponibles en la base de QA. También se realizaron comprobaciones parciales de autorización y se completó un recorrido de configuración inicial de MFA con un usuario de QA.

Sin embargo, no se completó una validación de integración de los endpoints financieros y de estadísticas con comprobación exhaustiva de sus respuestas y cálculos. Tampoco se aplicaron las migraciones en una base de datos independiente.

Por tanto, los resultados permiten documentar los escenarios ejecutados, pero no certificar el funcionamiento integral del backend ni la ausencia de defectos.

Los pendientes BACK-01 a BACK-04 requieren seguimiento antes de considerar completa la validación del backend del PR #22.

## 8. Estado de auditoría

**Resultado:** pruebas existentes aprobadas y funcionamiento observado parcialmente en los escenarios ejecutados.

**Pendientes principales:** cobertura automatizada de estadísticas, prueba explícita del rol Finanzas, integración real de endpoints y validación de migraciones.

**Recomendación:** mantener los pendientes registrados y solicitar evidencia de su cierre antes de considerar completa la validación del backend.
