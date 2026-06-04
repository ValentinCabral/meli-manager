# Design: Métricas de Publicaciones (Fase 2)

## Technical Approach

Add a `visitas_publicacion` table, batch-sync via `GET /visits/items`, and expose a `/metricas` page with a LEFT JOIN view sorted by visits DESC. Follow existing sync patterns (`_sync_cuenta_items`, `_sync_cuenta_ordenes`).

## Architecture Decisions

### Decision: Visit data storage

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Store per-day rows | Enables trends (Fase 3), but each sync inserts new rows | ✅ **Current: aggregate row per item** — simpler, matches proposal scope |
| Store latest aggregate only | No history, but zero dedup logic | ❌ Rejected: loses trend potential |
| Discard and re-fetch each sync | No persistence needed, but can't sort/filter offline | ❌ Rejected: need stable data for table view |

**Rationale**: Single row per `(cuenta_id, meli_item_id)` with `fecha` + `visitas` fits both current table view and future trend extension.

### Decision: Sync chunk strategy

| Option | Tradeoff | Decision |
|--------|----------|----------|
| One request per item | N requests for N items (slow, rate-limited) | ❌ Rejected |
| Chunk 20 IDs per request | 1 request per 20 items, matches MELI batch limit | ✅ **Current: match `sync_all_items` batch_size=20** |
| Chunk 50 IDs | Fewer requests, but MELI may truncate | ❌ Rejected: undocumented upper bound |

**Rationale**: Same `batch_size=20` already proven in `sync_all_items()`.

### Decision: Query approach for /metricas

**Choice**: `LEFT JOIN visitas_publicacion v ON p.meli_item_id = v.meli_item_id` aggregated per publication, default sort by `COALESCE(v.visitas, 0) DESC`.

**Alternatives considered**: Subquery per row (N+1), materialized view (overkill).

**Rationale**: Single query, no N+1, covers null visits gracefully.

## Data Flow

```
Sync:
  Dashboard button → /meli/sync-visits
    → get_active_cuenta()
    → listar_publicaciones(estado='activo') → item_ids[]
    → Chunk [0:20, 20:40, ...]
    → MeliClient.sync_all_visits(chunk)
    → upsert_visita() per item
    → flash result → redirect /metricas

View:
  /metricas
    → query("SELECT p.*, v.visitas, v.fecha FROM publicaciones p
             LEFT JOIN visitas_publicacion v
             ON p.meli_item_id = v.meli_item_id
             WHERE p.cuenta_id = ?
             ORDER BY v.visitas DESC NULLS LAST")
    → render metricas.html
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `database.py` | Modify | Add `visitas_publicacion` table in `init_db()` + `upsert_visita()` + `get_metricas_detalle()` |
| `meli_client.py` | Modify | Add `sync_all_visits(item_ids: list) -> dict` calling `GET /visits/items?ids=` |
| `app.py` | Modify | Add `_sync_cuenta_visits()` helper + `/meli/sync-visits` + `/metricas` routes |
| `templates/metricas.html` | Create | Table with columns: Producto, MELI ID, Precio, Visitas, Vendidos, Stock |
| `templates/publications.html` | Modify | Add "Visitas" column in thead + td for each row |
| `templates/dashboard.html` | Modify | Add "📊 Sync Metrics" button in Acciones Rápidas card |
| `templates/base.html` | Modify | Add `('/metricas', 'metricas', 'Métricas')` before `/ventas` in nav_items + SVG chart icon |

## Interfaces / Contracts

```python
# meli_client.py — new method
def sync_all_visits(self, item_ids: list[str]) -> dict[str, int]:
    """Returns {item_id: visits, ...} from GET /visits/items?ids=MLA1,MLA2"""

# database.py — new CRUD
def upsert_visita(cuenta_id: int, meli_item_id: str, visitas: int) -> None
def get_metricas_detalle(cuenta_id: int) -> list[dict]
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `sync_all_visits()` chunking | Mock `requests.get`, verify `ids=` param has max 20 IDs |
| Unit | `upsert_visita()` idempotency | Insert same `(cuenta_id, meli_item_id)` twice, assert single row |
| Integration | `/metricas` returns 200 | Flask test client with seeded DB |
| E2E | Dashboard button → sync → metricas page | Manual: click Sync Metrics, check /metricas renders data |

## Migration / Rollout

No migration required. Table created on next `init_db()` via `executescript()`. Existing data unaffected.

## Open Questions

- [ ] Does the current MELI token have `read_visits` scope? If not, sync will 403.
