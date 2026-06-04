# Métricas Section Specification

## Purpose

Dedicated view showing per-listing performance: visits, sales, and stock.

## Requirements

### Requirement: `/metricas` route with metrics table

The system MUST render a table joining `publicaciones` with aggregate `visitas_publicacion` data. Columns: Producto, MELI ID, Precio, Visitas, Vendidos (`sold_quantity`), Stock. Sorted by Visitas DESC.

#### Scenario: Full data renders correctly

- GIVEN publications with synced visits
- WHEN the user navigates to `/metricas`
- THEN all 6 columns render sorted by Visitas descending

#### Scenario: No sync yet shows dashes

- GIVEN publications but no visits synced
- WHEN `/metricas` renders
- THEN the Visitas column shows "—" per row
- AND other columns are normal

#### Scenario: Partial sync

- GIVEN 3 of 5 items have visit data
- WHEN the table renders
- THEN synced items show counts, unsynced show "—"

### Requirement: Visitas header links to sync

The "Visitas" column heading SHALL link to `/meli/sync-visits`, redirecting back to `/metricas` after completion.
