# Tasks: Multitenancy — Google OAuth + Data Isolation

## config.py — Google OAuth env vars

- [x] 1.1 Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` env vars

## database.py — Usuarios table + migration + scoped CRUD

- [x] 2.1 Add `usuarios` table in init_db() (google_id, email, nombre, avatar_url)
- [x] 2.2 Add migration for `cuentas_meli.usuario_id` column (ALTER TABLE)
- [x] 2.3 Add `crear_usuario(google_id, email, nombre, avatar_url)` function
- [x] 2.4 Add `get_usuario_by_google_id(google_id)` function
- [x] 2.5 Update `listar_cuentas(usuario_id=None)` with optional user filter
- [x] 2.6 Update `crear_cuenta(...)` to accept `usuario_id` parameter

## app.py — Google OAuth + middleware

- [x] 3.1 Add `import requests` and `from urllib.parse import urlencode`
- [x] 3.2 Add Google OAuth config imports and `GOOGLE_REDIRECT_URI`
- [x] 3.3 Add `require_login()` before_request middleware
- [x] 3.4 Update `get_active_cuenta()` to verify user ownership
- [x] 3.5 Merge `inject_cuentas` + `inject_user` into single `inject_global_context` context_processor
- [x] 3.6 Add `/login` route with Google sign-in button
- [x] 3.7 Add `/auth/google/login` route (redirect to Google OAuth)
- [x] 3.8 Add `/auth/google/callback` route (code exchange + user creation)
- [x] 3.9 Add `/logout` route
- [x] 3.10 Update `/cuentas` route to filter by `usuario_id`
- [x] 3.11 Update MELI OAuth callback to pass `usuario_id` to `crear_cuenta`

## templates/login.html — New

- [x] 4.1 Create login.html with Google sign-in button

## templates/base.html — User info in sidebar

- [x] 5.1 Add user info section (avatar, name, email) in sidebar footer
- [x] 5.2 Add "Cerrar sesión" link below user info

## Review Workload Forecast

**400-line budget risk**: Medium
**Chained PRs recommended**: No
**Decision needed before apply**: No
**Chain strategy**: pending
