# OAuth/SSO Authentication

## Introduction

Cousins Matter supports authentication via OAuth2/OpenID Connect with multiple providers. This allows members to log in using their existing accounts from popular services like Google, Facebook, GitHub, and more.
**IMPORTANT**: The link between the OAuth identity provider account and Cousins Matter is established using email address of the member.

## Prerequisites

* Members must have a valid invitation to register via OAuth
* OAuth providers must be configured in the `.env` file
* Each provider requires a client ID and client secret

## Configuration

### Enable OAuth Providers

In your `.env` file, define the list of providers you want to enable:

```bash
OAUTH_PROVIDERS=google,facebook,github,pocketid
```

Available providers:
* `google` - Google OAuth
* `facebook` - Facebook OAuth
* `apple` - Apple Sign In
* `github` - GitHub OAuth
* `pocketid` - PocketID (OpenID Connect)
* Any other OpenID Connect compatible provider

### Auto-Signup Configuration

Control whether users need to confirm their login when using OAuth:

```bash
# Require confirmation (recommended for security)
SOCIALACCOUNT_AUTO_SIGNUP=False

# Allow automatic signup without confirmation
SOCIALACCOUNT_AUTO_SIGNUP=True
```

**Default:** `False` (confirmation required)

## Provider-Specific Configuration

### Google OAuth

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google+ API
3. Create OAuth 2.0 credentials
4. Add authorized redirect URIs: `https://yourdomain.com/accounts/google/login/callback/`

Configuration in `.env`:
```bash
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

### Facebook OAuth

1. Create an app in [Facebook Developers](https://developers.facebook.com/)
2. Add Facebook Login product
3. Configure Valid OAuth Redirect URIs: `https://yourdomain.com/accounts/facebook/login/callback/`

Configuration in `.env`:
```bash
FACEBOOK_OAUTH_CLIENT_ID=your_facebook_app_id
FACEBOOK_OAUTH_CLIENT_SECRET=your_facebook_app_secret
```

### Apple Sign In

1. Register your app in [Apple Developer Portal](https://developer.apple.com/)
2. Create a Service ID
3. Configure Sign In with Apple

Configuration in `.env`:
```bash
APPLE_OAUTH_CLIENT_ID=your_apple_service_id
APPLE_OAUTH_CLIENT_SECRET=your_apple_client_secret
```

### GitHub OAuth

1. Register a new OAuth application in [GitHub Settings](https://github.com/settings/developers)
2. Set Authorization callback URL: `https://yourdomain.com/accounts/github/login/callback/`

Configuration in `.env`:
```bash
GITHUB_OAUTH_CLIENT_ID=your_github_client_id
GITHUB_OAUTH_CLIENT_SECRET=your_github_client_secret
```

### PocketID (OpenID Connect)

[PocketID](https://pocketid.app/) is a self-hosted OpenID Connect provider.

Configuration in `.env`:
```bash
POCKETID_SERVER_URL=https://pocketid.yourdomain.com
POCKETID_OAUTH_CLIENT_ID=your_pocketid_client_id
POCKETID_OAUTH_CLIENT_SECRET=your_pocketid_client_secret
```

### Generic OpenID Connect Provider

For any other OpenID Connect compatible provider:

Configuration in `.env`:
```bash
OPENID_CONNECT_SERVER_URL=https://your.openidconnect.server.com
OPENID_CONNECT_OAUTH_CLIENT_ID=your_client_id
OPENID_CONNECT_OAUTH_CLIENT_SECRET=your_client_secret
```

## Invitation Process

OAuth authentication in Cousins Matter requires a valid invitation:

1. **For New Users:**
   * An admin or authorized member must send an invitation to the user's email
   * The user clicks the invitation link
   * The invitation is stored in the session
   * The user can then authenticate via OAuth
   * The account is automatically activated

2. **For Existing Inactive Users:**
   * If a user account exists but is not active
   * The user must use the invitation link sent to their email
   * After clicking the link, they can authenticate via OAuth
   * The account is activated and linked to the OAuth provider

3. **For Active Users:**
   * Active users can directly log in via OAuth
   * No invitation is required
   * The OAuth account is linked to their existing account

## Security Considerations

* **Email Verification:** OAuth providers must provide an email address
* **Invitation Required:** New users cannot self-register without an invitation
* **Session Security:** Invitation tokens are stored securely in the session
* **Token Expiration:** Invitation tokens expire after a configurable period (see `MAX_REGISTRATION_AGE` in [Settings](settings.md))

## Troubleshooting

### "No invitation found for this email address"

This error occurs when:
* The user hasn't clicked on an invitation link
* The invitation has expired
* The email from the OAuth provider doesn't match the invited email

**Solution:** Request a new invitation from an admin with the proper email address.

### "The identity provider did not provide an email address"

Some OAuth providers may not share the email address.

**Solution:** Configure the OAuth provider to include email in the scope.

### "This account is not yet active"

The user account exists but hasn't been activated.

**Solution:** Use the invitation link sent by email before attempting OAuth login.

## Restart Required

After modifying OAuth settings in `.env`, restart Cousins Matter:

```bash
docker compose restart
```

## See Also

* [Settings](settings.md) - Complete settings reference
* [Installation](installation.md) - Initial setup
* [Features](features.md) - Member management features