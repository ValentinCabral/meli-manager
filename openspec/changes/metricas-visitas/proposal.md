# Proposal: Métricas de Publicaciones (Fase 2)

## Intent
Mostrar métricas reales de las publicaciones de MELI — visitas diarias, total acumulado, y datos de performance para tomar decisiones informadas sobre cada listing.

## Scope

### In Scope
- Nueva tabla `visitas_publicacion` con visitas por día por publicación
- Sync de visitas via `GET /visits/items` (batch) en `meli_client.py`
- Nueva sección `/metricas` con tabla de publicaciones + visitas + sold_quantity
- Columna de visitas en la tabla de publicaciones existente
- Sync button en dashboard para métricas

### Out of Scope
- Charts / tendencias (Fase 3)
- Listing quality score
- Impresiones / CTR (MELI no expone via API básica)

## Capabilities

### New Capabilities
- `visits-sync`: Sincronización de visitas por publicación via batch API
- `metricas-section`: Vista de métricas con tabla de listings + visitas + ventas

### Modified Capabilities
- `publicaciones`: Agregar columna de visitas a la tabla existente
- `dashboard`: Agregar botón de sync de métricas

## Approach
1. Crear `visitas_publicacion` table en `init_db()`
2. Agregar `sync_visits()` en `meli_client.py` — llama batch endpoint con todos los item_ids activos
3. Agregar `/meli/sync-visits` route y `_sync_visits()` helper
4. Crear `/metricas` route con tabla de publicaciones + visitas totales + sold_quantity
5. Agregar columna de visitas en `publications.html`
6. Agregar sync button en dashboard

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `database.py` | Modified | Nueva tabla + CRUD |
| `meli_client.py` | Modified | Nuevo `sync_all_visits()` |
| `app.py` | Modified | Routes sync + metricas |
| `templates/metricas.html` | New | Tabla de métricas |
| `templates/publications.html` | Modified | Columna visitas |
| `templates/dashboard.html` | Modified | Botón sync |
| `templates/base.html` | Modified | Nav item |

## Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Visit data delayed 48h | High | Mostrar fecha de última sync |
| Batch limit 20 items | Medium | Particionar en chunks |

## Rollback Plan
Revert `get_metricas()` changes. Remove `/metricas` route. Quitar nav item.

## Success Criteria
- [ ] Sync de visitas funciona para todas las publicaciones activas
- [ ] `/metricas` muestra tabla con visitas totales y vendidos
- [ ] Publicaciones existentes muestran columna de visitas
