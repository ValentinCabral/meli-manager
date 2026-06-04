# Proposal: Multitenancy — Login con Google + datos por usuario

## Intent
Cada usuario se loguea con Google, linkea su/sus cuentas de MELI, y ve solo sus propios datos. Dos usuarios que acceden a la misma URL ven información completamente distinta.

## Scope
- Tabla `usuarios` (google_id, email, nombre)
- Google OAuth login/logout
- `before_request` middleware: todas las rutas requieren login
- `cuentas_meli` scoped por `usuario_id`
- Todas las queries filtran por usuario
- Login page simple
- Nav muestra email + botón logout
- Migración: datos existentes se asignan al primer usuario

## Approach
1. Google OAuth: redirect → code exchange → userinfo → session
2. `before_request` redirige a /login si no hay session
3. ALTER TABLE cuentas_meli ADD usuario_id
4. Cada DB function recibe usuario_id o lo hereda del helper

## Affected Areas
| Area | Impact |
|------|--------|
| database.py | Nueva tabla + ALTER + scoped queries |
| app.py | Google OAuth + before_request + login/logout |
| templates/login.html | New |
| templates/base.html | User info + logout |
| config.py | Google OAuth env vars |
