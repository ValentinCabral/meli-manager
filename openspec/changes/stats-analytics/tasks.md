# Tasks: Stats / Analytics Dashboard (Fase 3)

## database.py — Nuevas queries de agregación

- [x] 1.1 Add `get_revenue_mensual(cuenta_id, meses=6)` — revenue agrupado por mes
- [x] 1.2 Add `get_top_productos(cuenta_id, limit=5)` — top N productos por revenue
- [x] 1.3 Add `get_stats_resumen(cuenta_id)` — resumen este mes vs anterior + fees

## app.py — Nueva ruta

- [x] 2.1 Add `/stats` route with aggregation queries and render stats.html

## templates/stats.html — Nueva página

- [x] 3.1 Create stats.html extending base.html
- [x] 3.2 Summary cards row (Revenue, Comisiones, Órdenes)
- [x] 3.3 Revenue chart with Chart.js bar chart (revenue + comisiones per month)
- [x] 3.4 Top productos table (sorted by revenue DESC)
- [x] 3.5 Empty state when no orders synced

## templates/base.html — Modificaciones

- [x] 4.1 Add Chart.js CDN (v4.4.0) before Alpine.js
- [x] 4.2 Add nav item for /stats with trending-up SVG icon
- [x] 4.3 Add `{% block scripts %}{% endblock %}` before closing `</body>`

## Review Workload Forecast

**400-line budget risk**: Low
**Chained PRs recommended**: No
**Decision needed before apply**: No
**Chain strategy**: pending
