## Funcionalidades

### Gestión de los miembros

* Los miembros pueden listarse, filtrarse por nombre y apellido y ordenarse

	![members](assets/members.webp)

* El administrador del sitio o cualquier miembro (según la configuración) puede invitar a otros miembros por correo electrónico

	![invite](assets/invite.webp)

* Cualquiera puede solicitar una invitación, que se enviará por correo electrónico al administrador del sitio, quien podrá invitarle a continuación. Las solicitudes de invitación están protegidas por un captcha.

	![request-invite](assets/request-invite.webp)

* Los miembros pueden crear miembros "gestionados", es decir, miembros que no están activos en el sitio (por ejemplo, niños pequeños o personas mayores)
* Los miembros gestionados pueden ser activados por los miembros que los gestionan (por ejemplo, cuando un niño tiene edad suficiente para ser activo en el sitio).
* Los miembros pueden importarse en bloque mediante archivos CSV
* Los miembros pueden actualizar su propio perfil y el perfil de los miembros que gestionan
* Los miembros pueden marcarse como fallecidos con una fecha de fallecimiento (útil para la genealogía y la historia familiar)

	![profile](assets/profile.webp)

* Se puede imprimir un directorio de miembros en formato PDF

	![directory](assets/directory.webp)

* Se pueden mostrar los cumpleaños de los próximos 50 días (50 puede modificarse en la configuración)

	![birthdays](assets/birthdays.webp)

### Autenticación

* Autenticación estándar por correo electrónico/contraseña
* Autenticación OAuth/SSO con múltiples proveedores:
	* Google
	* Facebook
	* Apple
	* GitHub
	* PocketID (OpenID Connect autoalojado)
	* Cualquier proveedor compatible con OpenID Connect
* Consulta [Autenticación OAuth](oauth-authentication.md) para una configuración detallada

### Seguridad e historial de conexiones

* Todos los intentos de conexión se rastrean automáticamente con geolocalización de la IP
* El historial de conexiones se guarda para auditoría de seguridad (visible para los administradores del sitio en el admin de Django)
* Purga automática de los registros de conexión antiguos tras un periodo de retención configurable
* Ayuda a los administradores a detectar intentos de acceso no autorizados

### Seguidores y notificaciones

* Los miembros pueden seguir a otros miembros para ser notificados de sus actividades
* Los miembros pueden seguir salas de chat, foros, galerías y otros contenidos
* Notificaciones automáticas por correo electrónico cuando se actualiza un contenido seguido
* Frecuencia de notificación configurable por miembro:
	* **Inmediata** - Recibir las notificaciones en cuanto se produzcan los eventos
	* **Cada hora** - Recibir un resumen de los eventos cada hora
	* **Diaria** - Recibir un resumen diario de los eventos
	* **Semanal** - Recibir un resumen semanal
	* **Mensual** - Recibir un resumen mensual
	* **Nunca** - Desactivar completamente las notificaciones
* Cada miembro puede configurar su frecuencia de notificación preferida en los ajustes de su perfil
* La agrupación de notificaciones reduce la sobrecarga de correo electrónico manteniendo a los miembros informados

### Galerías

* Todos los miembros activos pueden crear galerías y añadirles fotos y vídeos
* Las galerías pueden tener subgalerías de cualquier profundidad
* Las fotos y los vídeos pueden importarse en bloque mediante archivos zip. Cada carpeta del archivo zip se convierte en una galería. Las actualizaciones se gestionan
* La visualización de fotos de la galería está paginada
* Las fotos y los vídeos pueden mostrarse en modo de pantalla completa y como diapositivas con un intervalo configurable

### Foro

* Los miembros activos pueden crear publicaciones
* Los miembros activos pueden responder a las publicaciones de otros miembros o añadir comentarios sencillos

### Chat

* Los miembros conectados pueden chatear en directo con otros miembros conectados
* Cousins Matter gestiona tantas salas de chat como se deseen
* Los miembros pueden crear salas de chat privadas y seleccionar a los miembros que pueden participar en ellas. 
	El creador de la sala se convierte en administrador de la misma y puede añadir a otros miembros y nombrar administradores entre ellos.
	Los administradores pueden invitar a otros miembros y a otros administradores

### Páginas / CMS

Funciones básicas de CMS: los administradores pueden crear páginas HTML estáticas y publicarlas en el sitio. 
La página de inicio también puede configurarse de esta manera, así como la política de privacidad y las páginas "acerca de"... 
Las páginas públicas (las que se muestran en el menú Páginas aunque no hayas iniciado sesión) pueden ser creadas y publicadas por cualquier miembro administrador. Su URL debe empezar por '/publish/'
Las páginas privadas (las que se muestran en el menú Páginas solo si has iniciado sesión) pueden ser creadas y publicadas por cualquier miembro administrador. Su URL debe empezar por '/private/'
Los mensajes de administración son un tipo específico de página que se muestra a todos los miembros conectados en la parte superior del sitio. Su URL debe empezar por '/admin-message/'
Otras páginas específicas por defecto pueden ser modificadas por cualquier miembro administrador. Se muestran en el menú de administración en "Editar páginas" y muestran respectivamente la página de inicio cuando no estás conectado (/home/unauthenticated/\<lang>), cuando estás conectado (/home/authenticated/\<lang>) y la política de privacidad (/about/privacy-policy/\<lang>).

### Tesoros

Este es un lugar donde puedes poner el foco en los tesoros familiares digitales, ya sean textos, música o vídeos

### Encuestas

Cualquier miembro activo puede crear una encuesta y cualquier miembro activo puede responder a una encuesta activa.
Las encuestas tienen fechas de publicación y de cierre. Pueden contener varias preguntas y las preguntas pueden ser de los siguientes tipos:

* preguntas simples de sí/no: marca la casilla de verificación
* texto abierto: introduce el texto enriquecido que quieras
* fecha: elige una fecha
* opciones: elige una opción de una lista

### Planificación de eventos

Como submódulo del módulo de encuestas, cualquier miembro activo puede crear una encuesta de planificación de eventos para definir cuándo debe tener lugar un evento. Esto añade al módulo de encuestas los siguientes tipos de opciones:

* elegir una fecha de una lista proporcionada
* elegir varias fechas de una lista proporcionada

### Anuncios clasificados

Cualquier miembro activo puede publicar un anuncio clasificado que pueden ver todos los demás miembros. Si a un miembro le interesa un anuncio, puede enviar un mensaje al publicador del anuncio, quien recibirá un correo electrónico.

### Genealogía

Cualquier miembro activo puede añadir personas a la genealogía del sitio. Puedes añadir personas a la genealogía introduciendo sus datos en formularios o importando un archivo GEDCOM. Puedes exportar la genealogía en formato GEDCOM. La genealogía puede mostrarse como un árbol dinámico o como listas de personas o de familias.
