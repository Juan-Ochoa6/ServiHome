# Informe de auditoría QA – PR #22

## 1. Información general

- **Proyecto:** ServiHome
- **Pull Request:** #22 – Integra panel de finanzas y estadísticas
- **Commit auditado:** `c579d28`
- **Commit de integración:** `0897ddb`
- **Fecha de auditoría:** 26 de noviembre de 2026
- **Entorno:** entorno local de auditoría, separado del repositorio de trabajo original.
- **Alcance:** backend, frontend, permisos, autenticación, panel financiero, estadísticas y migraciones relacionadas con el PR.

## 2. Objetivo

Verificar el funcionamiento y la integración de las funcionalidades incorporadas en el PR #22, especialmente el panel financiero, las estadísticas generales y el acceso diferenciado según el rol del usuario.

También se revisaron las pruebas automatizadas, la protección de rutas y la coherencia entre las respuestas del backend y los componentes del frontend.

## 3. Entorno y herramientas utilizadas

- Git y Git worktree para mantener aislado el código auditado.
- Python y Django para ejecutar el backend y las pruebas.
- MySQL como base de datos local de QA.
- Node.js, npm y Vite para ejecutar el frontend.
- Brave para las pruebas de navegación.
- PowerShell para inspección, ejecución de comandos y revisión de resultados.
- Herramientas de desarrollo del navegador para comprobar la sesión y el comportamiento de la aplicación.

No se incluyen contraseñas, tokens, claves secretas ni datos sensibles en esta documentación.

## 4. Actividades y resultados

### 4.1. Revisión inicial del código

Se revisaron los archivos modificados por el PR, las rutas del backend, las vistas financieras y de estadísticas, los modelos, las migraciones y los componentes del frontend.

**Resultado:** no se encontraron inconsistencias funcionales demostradas en la revisión realizada.

### 4.2. Verificación de configuración

Se ejecutó:

- `python manage.py check`
- `git diff --check 354dba7..c579d28`

**Resultado:**
- Django no reportó problemas en la configuración.
- Git no reportó errores de espacios en blanco en las diferencias revisadas.

### 4.3. Pruebas automatizadas

Se ejecutaron pruebas específicas y posteriormente la suite completa del proyecto.

**Resultados registrados:**
- 20 pruebas específicas aprobadas.
- Suite completa: 147 pruebas aprobadas.
- Tiempo registrado para la suite completa: 378.167 segundos.
- Resultado final: `OK`.

Durante la primera ejecución de la suite completa se presentaron fallos relacionados con la configuración de `FERNET_KEY`. Después de configurar la variable localmente, la ejecución completa terminó correctamente.

### 4.4. Pruebas de permisos y roles

Se revisó la clase `EsAdminOFinanzas` y la protección de las vistas financieras y de estadísticas.

Se comprobaron las respuestas de autorización para los siguientes perfiles:

| Perfil | Resultado esperado | Resultado observado |
|---|---|---|
| Administrador | Acceso permitido | 200 en la comprobación de autorización |
| Finanzas | Acceso permitido | 200 en la comprobación de autorización |
| Cliente | Acceso denegado | 403 |
| Usuario anónimo | Acceso denegado | 401 |

Nota: las comprobaciones HTTP de autorización se realizaron con `APIRequestFactory` y la ejecución de los métodos GET fue simulada. No deben interpretarse como una prueba completa de los datos devueltos por ambas vistas.

### 4.5. Prueba funcional del panel financiero

Se inició el backend y el frontend localmente y se accedió con un usuario administrador de QA.

Se verificaron los siguientes valores:

| Indicador | Valor observado |
|---|---:|
| Total pagado | $50.000 |
| Ganancia de ServiHome | $5.000 |
| Total para profesionales | $45.000 |
| Pagos confirmados | 1 |

También se comprobó que los valores se mantenían coherentes al agrupar la información por:

- Día.
- Semana.
- Mes.
- Año.

**Resultado:** el panel presentó la información esperada para los datos existentes en la base de QA.

### 4.6. Prueba funcional del panel de estadísticas

Se creó, con autorización, el usuario de QA `finanzas_qa1`, con rol `finanzas`, para comprobar el acceso al panel.

Se completó su configuración inicial de MFA y se ingresó a `/finanzas`.

Se observaron los indicadores de solicitudes, profesionales, ofertas y servicios más solicitados.

**Resultado:** el panel cargó y presentó los indicadores disponibles en la base de datos de QA.

### 4.7. Pruebas de autenticación y protección de rutas

Se revisaron el inicio de sesión, la configuración inicial de MFA, la verificación del código, la generación de JWT, la recuperación de sesión y el cierre de sesión.

También se comprobó en el navegador:

- El usuario con rol `finanzas` puede acceder a `/finanzas`.
- Al intentar entrar a `/panel`, la aplicación lo redirige.
- El rol se conserva en la sesión y se utiliza en la protección de rutas.

**Resultado:** el comportamiento observado coincide con la separación de roles implementada.

### 4.8. Revisión de migraciones

Se identificaron dos migraciones pendientes en el entorno local:

- `servicios.0013_pago_comprobante`
- `usuarios.0014_alter_perfil_rol`

Se revisó su contenido y el plan de ejecución.

También se ejecutó `makemigrations --check --dry-run`, que indicó que no había cambios adicionales pendientes de generar.

**Importante:** las migraciones no se aplicaron durante esta auditoría. Por tanto, no se considera validado su comportamiento mediante una ejecución real sobre una base independiente.

## 5. Hallazgos y oportunidades de mejora

### QA-PR22-01 – Falta de pruebas específicas para estadísticas

**Tipo:** oportunidad de mejora de cobertura.

No se encontraron pruebas automatizadas específicas para `EstadisticasGeneralesAPIView`.

Se recomienda agregar casos que validen los conteos por estado, los profesionales por verificación, las ofertas por aprobación y los servicios más solicitados.

### QA-PR22-02 – Falta de prueba explícita del rol finanzas en FinanzasTests

**Tipo:** oportunidad de mejora de cobertura.

La clase `FinanzasTests` contempla administrador, cliente y usuario anónimo, pero no se encontró un caso específico para el rol `finanzas`.

Se recomienda incorporar una prueba automatizada que verifique que este rol puede consultar el resumen financiero.

### QA-PR22-03 – Comentario incompleto de roles

**Tipo:** observación menor.

En `frontend/src/auth/AuthProvider.jsx`, un comentario enumera los roles cliente, profesional y administrador, pero omite el rol `finanzas`.

El código sí admite el rol; se recomienda actualizar únicamente el comentario para mantener la documentación interna coherente.

## 6. Aspectos fuera del alcance

- El campo `Pago.comprobante` y su migración ya existían antes del PR #22 y no fueron introducidos por este cambio.
- La integración con Mercado Pago corresponde a un commit posterior, fuera del alcance de esta auditoría.
- No se aplicaron migraciones.
- No se realizó una prueba de despliegue en un entorno de producción.
- Las vulnerabilidades moderadas reportadas por npm requieren una revisión independiente. No se ejecutó `npm audit fix`.

## 7. Conclusión

Durante la auditoría se revisaron el backend y el frontend, se ejecutaron 147 pruebas automatizadas y se realizaron pruebas funcionales de los paneles financiero y de estadísticas con usuarios de QA.

Se verificaron los cálculos financieros disponibles, los filtros de agrupación, el acceso por roles, la autenticación MFA y la protección de rutas.

**No se identificaron defectos funcionales demostrados dentro del alcance revisado.**

Se documentaron oportunidades de mejora relacionadas con la cobertura automatizada de estadísticas y del rol finanzas, además de una observación menor en un comentario del frontend.

La conclusión se limita a las verificaciones realizadas y no representa una certificación de ausencia total de errores.

## 8. Estado de auditoría

**Resultado:** sin defectos funcionales demostrados en el alcance revisado.

**Recomendación:** conservar este informe como evidencia de QA y registrar las oportunidades de mejora para su seguimiento.
