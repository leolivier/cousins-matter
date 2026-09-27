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

## Conectarse a una familia

Todos inician sesión en la página de inicio de sesión estándar — la familia se resuelve
automáticamente a partir de la cuenta conectada; no existe una URL por familia. Una dirección
de correo electrónico pertenece a una sola familia: para unirse a otra familia hace falta
otra dirección de correo.

* **Creador de la familia**: tras registrarse en *"Crear una nueva familia"*, la cuenta
  permanece inactiva hasta hacer clic en el enlace del correo de verificación; después
  inicie sesión con normalidad y será el administrador de la familia.
* **Otros miembros**: o bien aceptar la invitación enviada por correo electrónico por el
  administrador de la familia (enlace vinculado al tenant → registro → verificación por correo),
  o bien enviar una solicitud de adhesión (formulario con captcha) que un administrador de la
  familia debe aprobar. En ambos casos, inicie sesión después en la página de inicio de
  sesión estándar.

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
hacer que la propia base de datos rechace las escrituras entre tenants. La RLS está activa cuando
`MULTI_TENANT_ENABLED=True` **y** `POSTGRES_RUNTIME_USER` está definido.

**Con Docker**, define en `.env`:

```
MULTI_TENANT_ENABLED=True
POSTGRES_RUNTIME_USER=cm_app
POSTGRES_RUNTIME_PASSWORD=<contraseña robusta>
```

y reinicia los contenedores de la aplicación:

```
docker compose restart cousins-matter qcluster
```

Al arrancar, el entrypoint ejecuta las migraciones **como propietario**
(`POSTGRES_USER`): la migración RLS (`tenants.0003_rls`) crea el rol de ejecución con
privilegios de solo DML y aplica las políticas; a continuación el servidor y qcluster se
reinician y se conectan con el rol de ejecución. No hay nada que ejecutar a mano.

**Con una instalación manual (sin Docker)**, define las mismas variables y ejecuta
`manage.py migrate` **como propietario** (`POSTGRES_USER`) — esto es exactamente lo que el
entrypoint automatiza arriba.

**Para qué sirve `POSTGRES_USER`**: es el propietario (superusuario) creado por la imagen
de PostgreSQL. Ejecuta las migraciones — crea el rol de ejecución, sus privilegios de solo DML
y las políticas — y, como propietario, evade por completo la RLS; es la razón por la que
`FORCE ROW LEVEL SECURITY` no se utiliza nunca. El servidor y qcluster solo lo usan como
recurso cuando `POSTGRES_RUNTIME_USER` no está definido (la RLS no tiene efecto entonces).

Comportamiento de las políticas para el rol de ejecución:

* todas las tablas con ámbito de tenant (galerías, chat, foro, anuncios clasificados, encuestas,
  tesoros, genealogía, páginas): las filas fuera del tenant de la sesión son invisibles **y** no escribibles;
* `members_member`: las lecturas siguen siendo permisivas (el inicio de sesión por correo electrónico ocurre antes de
  conocer el tenant), pero INSERT/UPDATE/DELETE están fuertemente acotados;
* el middleware define `app.current_tenant_id` en cada petición y siempre lo
  restablece después (las conexiones agrupadas nunca filtran un tenant); los superusuarios de la
  plataforma reciben `app.bypass` para poder administrar entre tenants;
* las migraciones se ejecutan como propietario, lo que evade la RLS — es intencional, y es la
  razón por la que `FORCE ROW LEVEL SECURITY` no se utiliza nunca.

## Alcance actual

Todas las aplicaciones del producto tienen ámbito de tenant y están cubiertas por la seguridad
a nivel de fila: `members`, `galleries`, `chat`, `troves`, `forum`, `classified ads`, `polls`,
`genealogy` y `pages` — 22 tablas, migraciones `tenants.0003_rls` a `tenants.0010_rls_pages`.
Solo las tablas de infraestructura (sesiones de Django, cuentas allauth) siguen siendo globales;
el acotado por ORM se aplica a todo lo demás.
