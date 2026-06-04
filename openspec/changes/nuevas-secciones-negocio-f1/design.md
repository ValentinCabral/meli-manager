# Design: Orders + Real Revenue (Fase 1)

## Technical Approach

Extend existing sync pattern (`_sync_cuenta_items`) to orders: add `sync_orders()` to `MeliClient`, new tables in `init_db()`, DB CRUD functions, `GET /meli/sync-orders` route, `/ventas` route with server-side pagination, and dashboard metric swap from estimated to real revenue.

## Architecture Decisions

| Decision | Options | Trade-off | Choice |
|----------|---------|-----------|--------|
| Dedup strategy | ON CONFLICT DO UPDATE vs SELECT+INSERT | Upsert is atomic, single query | `INSERT ... ON CONFLICT(meli_order_id) DO UPDATE` |
| Sync delay | `time.sleep(0.5)` between pages vs none | Publications sync has no sleep — matching avoids breaking rate limits | No delay (match existing pattern) |
| Ventas pagination | Manual prev/next in Jinja vs Alpine | No new JS deps, simple counters | Manual prev/next with page info |
| Link `orden_items` → `publicaciones` | FK constraint vs logical JOIN | `meli_item_id` is TEXT not a PK; FK would fail on nulls | Logical JOIN via `LEFT JOIN publicaciones ON orden_items.meli_item_id = publicaciones.meli_item_id` |
| Dashboard empty state | Show text "$0" vs prompt | Spec says never show $0 | Show `"Sincronizá órdenes para ver revenue real"` in metric card body |
| Nav icon | New SVG vs reuse | Sidebar uses inline SVGs with consistent stroke-width=2 style | New `ventas` SVG (bar-chart icon) matching existing icon set |

## Table Schemas

```sql
CREATE TABLE IF NOT EXISTS ordenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta_id INTEGER NOT NULL REFERENCES cuentas_meli(id),
    meli_order_id TEXT NOT NULL UNIQUE,
    total_paid_amount REAL DEFAULT 0,
    marketplace_fee REAL DEFAULT 0,
    shipping_cost REAL DEFAULT 0,
    status TEXT DEFAULT 'paid',
    date_created TIMESTAMP,
    buyer_nickname TEXT DEFAULT '',
    buyer_id TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orden_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orden_id INTEGER NOT NULL REFERENCES ordenes(id),
    meli_item_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price REAL DEFAULT 0,
    total_amount REAL DEFAULT 0,
    item_title TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Data Flow

```
Dashboard Sync Orders → GET /meli/sync-orders
  → _sync_cuenta_ordenes(cuenta, client)
    → client.sync_all_orders(since=365d ago)
      → GET /orders/search?seller=$UID&order.status=paid
        &order.date_created.from=$T-365d
        &order.date_created.to=$T&offset=0&limit=50
      → paginate offset+=50 until paging.total reached
      → return [{id, total_amount, ...}] per order
    → db.upsert_orden()
      → INSERT ... ON CONFLICT(meli_order_id) DO UPDATE
    → db.upsert_orden_items(orden_id, items)
      → INSERT INTO orden_items for each line item
  → flash result → redirect dashboard

ventas page → GET /ventas?fecha_desde=X&fecha_hasta=Y&estado=paid&page=2
  → db.listar_ordenes(cuenta_id, filters)
    → SELECT o.*, GROUP_CONCAT(oi.item_title, ' | ') as items
      FROM ordenes o
      LEFT JOIN orden_items oi ON o.id = oi.orden_id
      WHERE o.cuenta_id=? AND filters... ORDER BY date_created DESC
      LIMIT 50 OFFSET 50
  → render ventas.html with pagination dict
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `database.py` | Modify | Add `ordenes` + `orden_items` tables in `init_db()`, add `upsert_orden()`, `upsert_orden_items()`, `listar_ordenes()` (filtered/paginated), `get_revenue_total()`, `count_ordenes()`. Update `get_metricas()` to replace `valor_venta_meli` with real revenue query. |
| `meli_client.py` | Modify | Add `sync_all_orders(since_days=365)` — calls `GET /orders/search` with pagination, same batch pattern as `sync_all_items()`. |
| `app.py` | Modify | Add `_sync_cuenta_ordenes()` helper. Add `GET /meli/sync-orders` route. Add `GET /ventas` route with query params for filters + pagination. |
| `templates/ventas.html` | Create | Orders table with columns: ID, Fecha, Estado, Total, Items, Comprador. Has date inputs, status dropdown, sortable date header, prev/next pagination. |
| `templates/dashboard.html` | Modify | Change "Venta MELI" → "Revenue Real". Replace metric value with conditional: if orders exist show `$N`, else show prompt text. Add "📥 Sync Orders" button. |
| `templates/base.html` | Modify | Add `('ventas', 'ventas', 'Ventas')` to `nav_items` list. Add SVG icon for `ventas` in `nav_icon()` macro. Insert after "Publicaciones" in nav order. |
| `static/css/app.css` | No change | Existing classes (`.data-table`, `.badge`, `.empty-state`, `.grid-2`, pagination via simple inline `<a>` tags) suffice. |

## Interfaces / Contracts

```python
# meli_client.py
def sync_all_orders(self, since_days: int = 365) -> list[dict]:
    """Returns [{id, total_amount, status, date_created, buyer, order_items: [{item_id, quantity, unit_price, total_amount}]}]. Paginates internally."""

# database.py
def upsert_orden(cuenta_id: int, data: dict) -> int:
    """Returns orden id. Uses ON CONFLICT(meli_order_id) DO UPDATE."""
def upsert_orden_items(orden_id: int, items: list[dict]) -> None:
    """Deletes old items for this orden, inserts current."""
def listar_ordenes(cuenta_id: int, desde="", hasta="", estado="",
                   page=1, per_page=50, sort_order="desc") -> dict:
    """Returns {'rows': [...], 'total': N, 'page': P, 'pages': M, 'per_page': 50}."""
def get_revenue_total(cuenta_id: int) -> float:
    """SUM(total_paid_amount) from ordenes. Returns 0.0 if no orders."""
```

## Testing Strategy

No test suite exists (config says `testing.runner: none`). Rely on manual verification per success criteria in proposal.

## Migration / Rollout

No migration required. New tables are created by `init_db()` on next app start. Existing `valor_venta_meli` metric is replaced atomically — no downtime. Rollback: revert `get_metricas()` calculation, remove route + nav item, keep tables (no downstream impact).

## Open Questions

- [ ] `GET /orders/search` response shape: does MELI return `total_amount` at order level or must we sum payments? If only payments, we parse `payments[].total_paid_amount`.
- [ ] Rate limit on orders endpoint: same pool as items (100 req/min)? If orders uses separate pool, we could skip delay but must verify.
