# Personaliza tu sitio

## Ajustes
Consulta [Ajustes](settings.md) para personalizar el sitio modificando los ajustes.

### Gestión de las funcionalidades
Mediante los ajustes, también puedes gestionar las funcionalidades que se ofrecerán a los miembros, tal como se explica en [Gestión de las funcionalidades](settings.md/#features-management)

### Preferencias de notificación
Los miembros pueden configurar la frecuencia de sus notificaciones por correo electrónico en los ajustes de su perfil. Consulta [Funcionalidades - Seguidores y notificaciones](features.md#seguidores-y-notificaciones) para más detalles.

## Creación de páginas
El administrador puede crear o actualizar páginas estáticas utilizando la función "Editar página" de la barra de navegación. **¡Solo los administradores tienen acceso a esta función!**

Al crear una página, se abre un formulario en el que debes rellenar algunos campos:

* URL: Este campo se utilizará para mostrar la página.
	Hay diferentes categorías de páginas:

	* Las páginas "About" (acerca de), que incluyen la política de privacidad descrita más abajo, deben empezar por '/<language-code\>/about/<page-slug\>'. Se muestran en el lado derecho de la barra de navegación, bajo un icono de interrogación.
	* Las páginas "Home" (inicio) son páginas que empiezan por '/<language-code\>/home/'. Consulta [Página de inicio (front)](#front-or-home-pages) más abajo
	* Las páginas "Static" (estáticas) son páginas que empiezan por '/publish/'. Pueden tener 2 subformas:

		* /publish/<page-slug\>: el título de estas páginas se muestra directamente en el menú Páginas de la barra de navegación.
		* /publish/<menu-name\>/<page-slug\>: Son menús desplegables del menú Páginas con el nombre "menu-name", y el título de cada página se muestra en la lista desplegable bajo <menu-name\>.

	* Las páginas de mensaje, con una URL que empieza por '/admin-message/', consulta [Mostrar un mensaje de administración en todas las páginas](#show-an-admin-message-on-all-pages)
	* Cualquier otra URL puede incluirse como enlace en otras páginas, pero no será accesible desde la barra de menús.

* Título: es la cadena que se mostrará en los menús.
* Contenido: es el contenido de la página. Puede editarse con el editor enriquecido.
* Una casilla de verificación llamada "Authorize comments" (Autorizar comentarios) se muestra, pero no se utiliza por el momento.

## Gestión de la privacidad
Las páginas estáticas (una por idioma) que describen la política de privacidad del sitio se cargan en la base de datos durante la instalación de la aplicación.
Estas páginas pueden personalizarse con la función estándar "Editar página" descrita anteriormente.

**ADVERTENCIA**: ¡No cambies la URL de estas páginas! El patrón de esta URL es /<language-code\>/about/privacy-policy. Si cambias este patrón, ¡la política de privacidad asociada dejará de ser accesible!

## Pie de página personalizado
Define `SITE_FOOTER` tal como se explica en [Personalización general](settings.md/#general-customization)

## Páginas de inicio (front o home)
Tu sitio necesita dos páginas de inicio (front, también llamadas home) diferentes:

* La primera para las personas no autenticadas, donde puedes explicar el propósito de tu sitio sin dar demasiados detalles ni nada privado.
* La segunda es la página para tus miembros una vez que hayan iniciado sesión.
Puedes editar estas 2 páginas directamente desde la página de inicio por defecto o desde la lista de páginas del menú.

La URL de estas páginas se construye así: /<language code\>/home/authenticated y /<language code\>/home/unauthenticated.

Versiones predefinidas de estas dos páginas se cargan en la base de datos en la primera carga.
Si el código de idioma del .env no corresponde con ninguna de las páginas precargadas, se muestra la versión en-US.

**PRECAUCIÓN**: ¡No cambies las URL de estas páginas o no funcionará!

## Mostrar un mensaje de administración en todas las páginas
Los administradores pueden crear páginas especiales con una URL que empiece por '/admin-message/'. El título de esta página solo se utilizará en la lista de páginas del menú "Editar páginas". El contenido de estas páginas se muestra como una notificación en la parte superior de cada página y puede cerrarse, pero volverá a aparecer en cada nueva conexión mientras la página exista en la base de datos.

Puedes crear una única página con la URL '/admin-message/' o cualquier número de páginas que empiecen todas por '/admin-message/', y cada página se mostrará como una notificación específica.

## Temas
Para crear tu propio tema, debes aplicar nuevos valores a las variables de Bulma en el archivo llamado media/public/theme.css (este archivo está montado en las imágenes de docker).

La personalización debe tener el siguiente formato:

```
:root {
	--bulma-xxx: value;
	--bulma-yyy: value;
	--bulma-zzz: value;
}
```


p. ej.


```
:root {
	--bulma-body-font-size: 16px;
	--bulma-primary-h: 155deg !important;
	--bulma-primary-s: 80% !important;
	--bulma-primary-l: 37% !important;
}
```

cambiará el tamaño global de la fuente del sitio y cambiará el color primario (definido en términos de HSL (tono, saturación y luminosidad). (Puedes probar colores HSL en https://hslpicker.com/) También puedes cambiar variables en el ámbito de un componente, pero entonces ya no es un tema real; consulta los detalles en [Bulma CSS Variables](https://bulma.io/documentation/features/css-variables/) y [Customizing Bulma CSS variables](https://bulma.io/documentation/customize/with-css-variables/) Para conocer todas las variables CSS definidas por Bulma, consulta el [Bulma CSS File](https://cdn.jsdelivr.net/npm/bulma@1.0.1/css/bulma.css) y pruébalas en tu navegador para ver su efecto.
