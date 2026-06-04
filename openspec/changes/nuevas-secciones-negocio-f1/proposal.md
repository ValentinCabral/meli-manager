# Proposal: Orders + Real Revenue (Fase 1)

## Intent

MELI Manager currently has zero real sales data — "Venta MELI" on dashboard is price × stock from DB, not actual revenue. We need to sync real orders from MELI, store them locally, and show actual revenue. This is the foundation for all future analytics features.

## Scope

### In Scope
- New tables `ordenes` and `orden_items` in SQLite
- `GET /orders/search` sync method in meli_client.py
- `/ventas` route with orders table, date range + status filters
- Replace dashboard "Venta MELI" metric with real revenue from orders
- Add "Ventas" nav item + sync orders button on dashboard

### Out of Scope
- Visits / listing metrics (Fase 2)
- Stats dashboard with charts (Fase 3)
- Bulk publish with installments (Fase 4)
- Chart.js or any chart library

## Capabilities

### New Capabilities
- `orders-sync`: MELI orders fetching, pagination, storage in SQLite
- `ventas-section`: Sales view with date/status filtering, server-side pagination

### Modified Capabilities
- `dashboard`: Revenue metric changes from estimated (`stock × precio`) to real (`SUM(orden_items.total)`) — spec-level behavior change

## Approach

1. Create `ordenes` and `orden_items` tables in `database.py` (matching MELI schema for fees, status, totals)
2. Add `sync_orders()` to `meli_client.py` — call `GET /orders/search?seller=$ID`, paginate same pattern as existing publication sync
3. Add DB functions: `sync_orden()`, `listar_ordenes()`, `get_ordenes_metric()` for revenue sum
4. New `/ventas` route in `app.py` — reads orders with filters, renders table
5. Update `get_metricas()` to replace valor_venta_meli with real revenue
6. Add nav item to `base.html`, create `ventas.html` template matching existing table styling

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `database.py` | Modified | New tables + CRUD functions |
| `meli_client.py` | Modified | New `sync_orders()` method |
| `app.py` | Modified | New `/ventas` route, dashboard metric change |
| `templates/ventas.html` | New | Orders table with filters |
| `templates/base.html` | Modified | "Ventas" nav item + icon |
| `templates/dashboard.html` | Modified | Metric label + sync button |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| MELI rate limit (100 req/min) | Low | Same pagination delay pattern as publications sync |
| Existing orders have no payments | Low | Use `status` filter, handle null fees gracefully |

## Rollback Plan

Revert `get_metricas()` to original stock×price calculation. Remove `/ventas` route and nav item. Tables can stay (no downstream impact). Restore `base.html` nav_items list.

## Dependencies

- Existing MELI OAuth token (no new scopes needed)

## Success Criteria

- [ ] First sync pulls all historical orders from MELI without errors
- [ ] `/ventas` page shows orders table, filters work, pagination works
- [ ] Dashboard "Venta MELI" shows real revenue matching a manual MELI orders query
- [ ] All existing routes continue working
