# Tasks: Métricas de Publicaciones (Fase 2)

## Review Workload Forecast

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Database

- [x] 1.1 `database.py` — Add `visitas_publicacion` table in `init_db()`: id, cuenta_id, meli_item_id, visitas, fecha, synced_at, UNIQUE(cuenta_id, meli_item_id)
- [x] 1.2 `database.py` — Add `upsert_visita(cuenta_id, meli_item_id, visitas)` — upsert individual row; called in loop from routes for bulk
- [x] 1.3 `database.py` — Add `get_visitas(cuenta_id) → dict` + `get_metricas_detalle(cuenta_id) → list[dict]` with LEFT JOIN query

## Phase 2: API Client

- [x] 2.1 `meli_client.py` — Add `sync_all_visits(item_ids) → dict` — chunks items into groups of 20, calls `GET /visits/items?ids=ID1,...`, returns combined dict

## Phase 3: Routes

- [x] 3.1 `app.py` — Add `_sync_cuenta_visits(cuenta, client)` helper and `GET /meli/sync-visits` route
- [x] 3.2 `app.py` — Add `GET /metricas` route with `get_metricas_detalle()` LEFT JOIN query, renders metricas.html

## Phase 4: Templates

- [x] 4.1 `templates/metricas.html` — Create: table with Producto, MELI ID, Precio, Visitas, Vendidos (—), Stock; sorted by visitas DESC
- [x] 4.2 `templates/base.html` — Add `('/metricas', 'metricas', 'Métricas')` nav item after Ventas, with bar-chart SVG icon
- [x] 4.3 `templates/publications.html` — Add "Visitas" column with visit count (from merged visitas dict) or "—"
- [x] 4.4 `templates/dashboard.html` — Add "📊 Sync Metrics" button linking to /meli/sync-visits

## Phase 5: Verification

- [ ] 5.1 Verify app starts without errors
- [ ] 5.2 Sync visits → verify metricas page shows data
- [ ] 5.3 Verify publications page shows visits column
