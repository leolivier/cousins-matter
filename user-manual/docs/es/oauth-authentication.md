# Autenticación OAuth/SSO

## Introducción

Cousins Matter admite la autenticación mediante OAuth2/OpenID Connect con múltiples proveedores. Esto permite a los miembros iniciar sesión con sus cuentas existentes de servicios populares como Google, Facebook, GitHub y muchos más.
**IMPORTANTE**: el enlace entre la cuenta del proveedor de identidad OAuth y Cousins Matter se establece utilizando la dirección de correo electrónico del miembro.

## Requisitos previos

* Los miembros deben tener una invitación válida para registrarse mediante OAuth
* Los proveedores OAuth deben configurarse en el archivo `.env`
* Cada proveedor requiere un client ID y un client secret

## Configuración

### Activar los proveedores OAuth

En tu archivo `.env`, define la lista de proveedores que quieres activar:

```bash
OAUTH_PROVIDERS=google,facebook,github,pocketid
```

Proveedores disponibles:
* `google` - OAuth de Google
* `facebook` - OAuth de Facebook
* `apple` - Apple Sign In
* `github` - OAuth de GitHub
* `pocketid` - PocketID (OpenID Connect)
* Cualquier otro proveedor compatible con OpenID Connect

### Configuración del registro automático

Controla si los usuarios necesitan confirmar su inicio de sesión cuando utilizan OAuth:

```bash
# Exigir confirmación (recomendado por seguridad)
SOCIALACCOUNT_AUTO_SIGNUP=False

# Permitir el registro automático sin confirmación
SOCIALACCOUNT_AUTO_SIGNUP=True
```

**Por defecto:** `False` (se requiere confirmación)

## Configuración específica de cada proveedor

### OAuth de Google

1. Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Activa la API de Google+
3. Crea credenciales OAuth 2.0
4. Añade las URIs de redirección autorizadas: `https://yourdomain.com/accounts/google/login/callback/`

Configuración en `.env`:
```bash
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

### OAuth de Facebook

1. Crea una aplicación en [Facebook Developers](https://developers.facebook.com/)
2. Añade el producto Facebook Login
3. Configura las URIs de redirección OAuth válidas: `https://yourdomain.com/accounts/facebook/login/callback/`

Configuración en `.env`:
```bash
FACEBOOK_OAUTH_CLIENT_ID=your_facebook_app_id
FACEBOOK_OAUTH_CLIENT_SECRET=your_facebook_app_secret
```

### Apple Sign In

1. Registra tu aplicación en [Apple Developer Portal](https://developer.apple.com/)
2. Crea un Service ID
3. Configura Sign In with Apple

Configuración en `.env`:
```bash
APPLE_OAUTH_CLIENT_ID=your_apple_service_id
APPLE_OAUTH_CLIENT_SECRET=your_apple_client_secret
```

### OAuth de GitHub

1. Registra una nueva aplicación OAuth en [GitHub Settings](https://github.com/settings/developers)
2. Define la URL de callback de autorización: `https://yourdomain.com/accounts/github/login/callback/`

Configuración en `.env`:
```bash
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
```

### PocketID (OpenID Connect)

[PocketID](https://pocketid.app/) es un proveedor de OpenID Connect autoalojado.

Configuración en `.env`:
```bash
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=your_pocketid_client_id
POCKETID_OAUTH_CLIENT_SECRET=your_pocketid_client_secret
```

### Proveedor genérico de OpenID Connect

Para cualquier otro proveedor compatible con OpenID Connect:

Configuración en `.env`:
```bash
OPENID_CONNECT_SERVER_URL=https://your.openidconnect.server.com
OPENID_CONNECT_OAUTH_CLIENT_ID=your_client_id
OPENID_CONNECT_OAUTH_CLIENT_SECRET=your_client_secret
```

## Proceso de invitación

La autenticación OAuth en Cousins Matter requiere una invitación válida:

1. **Para usuarios nuevos:**
   * Un administrador o un miembro autorizado debe enviar una invitación al correo electrónico del usuario
   * El usuario hace clic en el enlace de la invitación
   * La invitación se guarda en la sesión
   * El usuario puede entonces autenticarse mediante OAuth
   * La cuenta se activa automáticamente

2. **Para usuarios existentes inactivos:**
   * Si existe una cuenta de usuario pero no está activa
   * El usuario debe utilizar el enlace de invitación enviado a su correo electrónico
   * Tras hacer clic en el enlace, puede autenticarse mediante OAuth
   * La cuenta se activa y se vincula al proveedor OAuth

3. **Para usuarios activos:**
   * Los usuarios activos pueden iniciar sesión directamente mediante OAuth
   * No se requiere ninguna invitación
   * La cuenta OAuth se vincula a su cuenta existente

## Consideraciones de seguridad

* **Verificación del correo electrónico:** los proveedores OAuth deben proporcionar una dirección de correo electrónico
* **Invitación obligatoria:** los usuarios nuevos no pueden registrarse por sí mismos sin una invitación
* **Seguridad de la sesión:** los tokens de invitación se guardan de forma segura en la sesión
* **Caducidad de los tokens:** los tokens de invitación caducan tras un periodo configurable (ver `MAX_REGISTRATION_AGE` en [Ajustes](settings.md))

## Resolución de problemas

### "No se ha encontrado ninguna invitación para esta dirección de correo electrónico"

Este error se produce cuando:
* El usuario no ha hecho clic en un enlace de invitación
* La invitación ha caducado
* El correo electrónico del proveedor OAuth no coincide con el correo electrónico invitado

**Solución:** solicita una nueva invitación a un administrador con la dirección de correo electrónico correcta.

### "El proveedor de identidad no ha proporcionado una dirección de correo electrónico"

Algunos proveedores OAuth pueden no compartir la dirección de correo electrónico.

**Solución:** configura el proveedor OAuth para incluir el correo electrónico en el scope.

### "Esta cuenta aún no está activa"

La cuenta de usuario existe pero aún no se ha activado.

**Solución:** utiliza el enlace de invitación enviado por correo electrónico antes de intentar el inicio de sesión OAuth.

## Reinicio necesario

Tras modificar los ajustes de OAuth en `.env`, reinicia Cousins Matter:

```bash
docker compose restart
```

## Véase también

* [Ajustes](settings.md) - Referencia completa de los ajustes
* [Instalación](installation.md) - Configuración inicial
* [Funcionalidades](features.md) - Funciones de gestión de los miembros
