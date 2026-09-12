# Multi-tenancy (varias familias en un mismo despliegue)

Cousins Matter puede servir a **varias familias (tenants) desde un único despliegue**,
con los datos de cada familia aislados. Esta página documenta la funcionalidad y
su despliegue.

## Activar la funcionalidad

La funcionalidad está **desactivada por defecto**: un despliegue de una sola familia se
comporta exactamente igual que la aplicación clásica. Para activarla, define en `.env`:

```
MULTI_TENANT_ENABLED=True
```

Esto monta las URLs `/tenants/` (registro de familias + gestión) y muestra el
enlace "Crear una nueva familia" en la página de inicio de sesión. Cuando está desactivada, todo esto da 404.

## Conceptos

| Concepto | Dónde |
|---|---|
| **Familia (tenant)** | `tenants.Tenant` — nombre, slug, `is_active` |
| **Administrador de familia** | `Member.role = "admin"` — gestiona los miembros y los ajustes de su familia |
| **Administrador de la plataforma** | `is_superuser` — entre tenants, reside en el tenant `system`, con acceso al admin de Django (`is_staff`) |
| **Aislamiento (principal)** | manager del ORM con ámbito de tenant (`TenantManager`) + `TenantMiddleware` |
| **Aislamiento (red de seguridad)** | seguridad a nivel de fila de PostgreSQL (ver más abajo) |

Dos tenants se crean mediante una migración y no pueden eliminarse: `default`
(asignado cuando no puede resolverse ninguno) y `system` (hogar de los administradores de la plataforma).

## Crear una familia

* **Autoservicio**: con la funcionalidad activada, la página de inicio de sesión ofrece
  *"Crear una nueva familia"*. El creador se registra con verificación por correo electrónico y
  se convierte en el administrador de la familia.
* **Por un administrador de la plataforma**: `/tenants/create/` crea la familia y puede enviar por
  correo electrónico una invitación (enlace vinculado al tenant) a su primer administrador.

Un identificador de familia (slug) se deriva de su nombre; los slugs reservados
(`default`, `system`, `admin`, …) se rechazan.

## Ajustes de la familia

Un administrador de familia edita los ajustes de su familia en **Ajustes de familia**
(desplegable de la barra de navegación): nombre del sitio, logo, copyright, pie de página,
modo oscuro, tamaño de página PDF, idioma, zona horaria, anticipación de cumpleaños,
permisos de miembros (crear/invitar) y la raíz del árbol genealógico. Los valores iguales a los
por defecto globales **no se almacenan**, de modo que un cambio global se propaga igualmente a
las familias que nunca los hayan modificado. Los correos dirigidos a "el administrador"
(formulario de contacto, invitaciones, notificaciones de fallecimiento) se envían al
**administrador de la familia**.

## Ciclo de vida

* **Desactivar** (`/tenants/<slug>/toggle-active/`): los miembros de la familia cierran
  su sesión y no pueden iniciarla hasta la reactivación.
* **Borrado definitivo** (`/tenants/<slug>/delete/`, o `manage.py delete_tenant
  <slug>`): elimina permanentemente la familia y todos sus datos. Rechaza el
  tenant system y cualquier familia todavía activa; requiere escribir el slug.

## Seguridad a nivel de fila de PostgreSQL (refuerzo opcional)

El ámbito a nivel de ORM es la capa principal de aislamiento. Como defensa en profundidad, puedes
hacer que la propia base de datos rechace las escrituras entre tenants:

1. Elige un rol que no sea el propietario, por ejemplo `cm_app`, con una contraseña robusta.
2. En `.env`, define `POSTGRES_RUNTIME_USER` / `POSTGRES_RUNTIME_PASSWORD` (y
   mantén `MULTI_TENANT_ENABLED=True`).
3. Ejecuta `manage.py migrate` **como propietario** (`POSTGRES_USER`) — la migración RLS
   (`tenants.0003_rls`) crea el rol, concede privilegios de solo DML
   y las políticas. El entrypoint del contenedor lo hace automáticamente:
   la inicialización se ejecuta como propietario y solo el servidor de larga duración
   utiliza el rol de ejecución.

Comportamiento de las políticas para el rol de ejecución:

* las tablas con ámbito de tenant fuera de los modelos de las propias aplicaciones (galerías): las filas fuera
  del tenant de la sesión son invisibles **y** no escribibles;
* `members_member`: las lecturas siguen siendo permisivas (el inicio de sesión por correo electrónico ocurre antes de
  conocer el tenant), pero INSERT/UPDATE/DELETE están fuertemente acotados;
* el middleware define `app.current_tenant_id` en cada petición y siempre lo
  restablece después (las conexiones agrupadas nunca filtran un tenant); los superusuarios de la
  plataforma reciben `app.bypass` para poder administrar entre tenants;
* las migraciones se ejecutan como propietario, lo que evade la RLS — es intencional, y es la
  razón por la que `FORCE ROW LEVEL SECURITY` no se utiliza nunca.

## Alcance actual

Hoy, `members` y `galleries` tienen ámbito de tenant. Convertir las demás
aplicaciones (chat, foro, encuestas, anuncios clasificados, páginas, tesoros, genealogía) sigue
el mismo patrón (clase base `TenantModel` + índices compuestos); hasta entonces, los datos de
esas aplicaciones se comparten entre las familias de un despliegue.
