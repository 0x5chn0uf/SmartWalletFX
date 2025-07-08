# OAuth Setup Guide

This document describes how to configure OAuth providers for the SmartWalletFX application.

## Environment Variables

Set the following environment variables in your `.env` file or deployment environment:

- `GOOGLE_CLIENT_ID` – Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` – Google OAuth client secret
- `GITHUB_CLIENT_ID` – GitHub OAuth client ID
- `GITHUB_CLIENT_SECRET` – GitHub OAuth client secret
- `OAUTH_REDIRECT_URI` – Base callback URL template, e.g. `http://localhost:8000/auth/oauth/{provider}/callback`

## Google Configuration

1. Create a project on [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google+ API** and create OAuth credentials.
3. Set the authorized redirect URI to `OAUTH_REDIRECT_URI` with `{provider}` replaced by `google`.

## GitHub Configuration

1. Go to [GitHub Developer Settings](https://github.com/settings/developers).
2. Create a new OAuth App with the callback URL using `github` in place of `{provider}`.
3. Save the client ID and secret in the corresponding environment variables.

After updating the environment, restart the application to apply the new settings.
