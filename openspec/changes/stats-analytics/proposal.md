# Proposal: Stats / Analytics Dashboard (Fase 3)

## Intent
Mostrar estadísticas agregadas del negocio — revenue en el tiempo, productos más vendidos, comisiones de MELI, y comparativas periódicas.

## Scope

### In Scope
- `/stats` route con cards + tabla de revenue mensual
- Revenue over time (monthly aggregation from ordenes)
- Top 5 productos por revenue
- Fee summary (total marketplace_fee vs revenue)
- Period comparison: este mes vs mes anterior
- Chart.js CDN para gráficos inline

### Out of Scope
- Visitas trends (ya en Fase 2)
- Export de stats
- Predicciones / forecasting

## Approach
1. Agregar Chart.js CDN a base.html
2. Crear queries de agregación en database.py (revenue mensual, top productos, fee summary)
3. Crear `/stats` route que pase datos agregados
4. Crear `stats.html` con cards + Chart.js bar chart + tabla top productos

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `database.py` | Modified | Agregar queries de stats |
| `app.py` | Modified | Nueva ruta /stats |
| `templates/stats.html` | New | Dashboard de estadísticas |
| `templates/base.html` | Modified | Nav item + Chart.js CDN |

## Success Criteria
- [ ] `/stats` muestra revenue mensual en chart de barras
- [ ] Top 5 productos se muestran con revenue real
- [ ] Fee summary muestra comisiones pagadas vs revenue neto
- [ ] Comparativa mes actual vs anterior funciona
