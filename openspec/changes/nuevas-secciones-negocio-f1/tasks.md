# Tasks: Orders + Real Revenue (Fase 1)

## Review Workload Forecast

Decision needed before apply: Yes (user approved single-pr)
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

| Field | Value |
|-------|-------|
| Estimated changed lines | ~350–400 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes (risk is Medium, delivery strategy is ask-on-risk — user decides whether to proceed as single PR)

## Phase 1: Database — Tables + CRUD Functions

- [x] 1.1 `database.py` — Add `CREATE TABLE IF NOT EXISTS ordenes (...)` with all columns per design in `init_db()`
- [x] 1.2 `database.py` — Add `CREATE TABLE IF NOT EXISTS orden_items (...)` with FK to `ordenes(id)` in `init_db()`
- [x] 1.3 `database.py` — Add `upsert_orden(cuenta_id, data) → int` using `INSERT ... ON CONFLICT(meli_order_id) DO UPDATE`
- [x] 1.4 `database.py` — Add `upsert_orden_items(orden_id, items)` — delete old items for orden then bulk-insert current
- [x] 1.5 `database.py` — Add `listar_ordenes(cuenta_id, desde, hasta, estado, page, per_page, sort_order)` with WHERE building + LIMIT/OFFSET + GROUP_CONCAT for items
- [x] 1.6 `database.py` — Add `get_revenue_total(cuenta_id) → float` — SUM over `ordenes.total_paid_amount`
- [x] 1.7 `database.py` — Add `count_ordenes(cuenta_id, desde, hasta, estado) → int` for pagination total
- [x] 1.8 `database.py` — Update `get_metricas()` — replace `SUM(stock * precio)` with `get_revenue_total()` for `valor_venta_meli`

## Phase 2: API Client — Sync Orders

- [x] 2.1 `meli_client.py` — Add `sync_all_orders(since_days=365) → list[dict]` calling `GET /orders/search?seller=$UID&order.status=paid&order.date_created.from=...&order.date_created.to=...&offset=0&limit=50`
- [x] 2.2 `meli_client.py` — Implement pagination in `sync_all_orders()`: loop `offset+=50` until `offset >= paging.total`, same delay pattern as `sync_all_items()`

## Phase 3: Backend Routes

- [x] 3.1 `app.py` — Add `_sync_cuenta_ordenes(cuenta, client)` helper: call `sync_all_orders()`, call `upsert_orden()` + `upsert_orden_items()` per order, return count
- [x] 3.2 `app.py` — Add `GET /meli/sync-orders` route: iterate active cuentas, call `_sync_cuenta_ordenes()`, flash result, redirect to dashboard
- [x] 3.3 `app.py` — Add `GET /ventas` route: read query params (`fecha_desde`, `fecha_hasta`, `estado`, `page`, `sort_order`), call `listar_ordenes()`, render `ventas.html`
- [x] 3.4 `app.py` — Handle empty state in `/ventas`: if `count_ordenes() == 0`, pass empty_rows flag instead of calling listar_ordenes

## Phase 4: Templates + Nav

- [x] 4.1 `templates/ventas.html` — Create full template: filter form (date range + status dropdown), data table with columns ID de Orden/Fecha/Estado/Total/Items/Comprador, sortable Fecha header, empty state message, prev/next pagination with page info
- [x] 4.2 `templates/base.html` — Add `('ventas', 'ventas', 'Ventas')` to `nav_items` after `publicaciones`, add matching SVG bar-chart icon in `nav_icon()` macro
- [x] 4.3 `templates/dashboard.html` — Replace "Venta MELI" card label with "Revenue Real", add conditional body: either `$N` formatted number or `"Sincronizá órdenes para ver revenue real"` prompt
- [x] 4.4 `templates/dashboard.html` — Add "📥 Sync Orders" button to action area that calls `/meli/sync-orders`

## Phase 5: Manual Verification

- [x] 5.1 Verify `init_db()` creates both new tables on app restart — inspect via SQLite CLI
- [x] 5.2 Verify dashboard loads without error and shows correct label + sync button
- [x] 5.3 Click Sync Orders — verify orders appear in DB (check `ordenes` and `orden_items` row counts)
- [x] 5.4 Visit `/ventas` — verify table renders, filters work, pagination navigates, empty state shows when no orders
- [x] 5.5 Verify dashboard revenue matches manual `SELECT SUM(total_paid_amount)` query
- [x] 5.6 Re-sync — verify dedup: same meli_order_id updates rather than duplicates
