# Ventas Section Specification

## Purpose

Provide a browsable, filterable view of synced orders with server-side pagination. Shows real sales data from the `ordenes` table.

## Requirements

### Requirement: The `/ventas` route renders an orders table

The system MUST provide a `GET /ventas` route that renders a table of synced orders. Each row SHALL display: order ID (meli), date, status, total amount, item names, and buyer nickname.

#### Scenario: Ventas page loads with orders

- GIVEN the user has synced orders and navigates to `/ventas`
- WHEN the page renders
- THEN the table shows columns: ID de Orden, Fecha, Estado, Total, Items, Comprador
- AND rows are sorted by date descending (newest first)

#### Scenario: No orders synced yet shows empty state

- GIVEN no orders have been synced
- WHEN the user visits `/ventas`
- THEN the page shows an empty state message: "Todavía no hay órdenes sincronizadas"
- AND a link to the dashboard to trigger sync

### Requirement: Date range filter

The system SHALL support filtering by `fecha_desde` and `fecha_hasta` query parameters. Results SHALL be filtered server-side by `date_created` range.

#### Scenario: Filtering by date range works

- GIVEN the user selects a from-date of 2026-01-01 and to-date of 2026-01-31
- WHEN the form is submitted
- THEN the URL contains `?fecha_desde=2026-01-01&fecha_hasta=2026-01-31`
- AND only orders within that range are displayed

### Requirement: Order status filter

The system SHALL support filtering by `estado` query parameter. Accepted values SHALL match MELI order statuses (e.g. `paid`, `cancelled`, `shipped`).

#### Scenario: Filtering by paid status works

- GIVEN the user selects "Pagadas" from the status dropdown
- WHEN the form is submitted
- THEN only orders with `status = 'paid'` are shown

### Requirement: Server-side pagination (50 per page)

The system MUST paginate results server-side with a default page size of 50. The page SHALL be controlled via a `page` query parameter.

#### Scenario: Pagination navigates between pages

- GIVEN the user has 150 synced orders
- WHEN the user clicks page 2
- THEN the URL contains `?page=2`
- AND the response shows orders 51–100
- AND pagination controls show "Anterior" / "Siguiente" links

#### Scenario: Page parameter is validated

- GIVEN the user manually sets `?page=999`
- WHEN the page renders
- THEN the last page of data is shown
- AND no 404 error is raised

### Requirement: Sortable by date

The system SHALL default to sorting by `date_created DESC`. The SHALL support reversing sort order via a `sort_order` parameter (`asc` / `desc`).

#### Scenario: Toggling sort order reverses results

- GIVEN the table shows newest-first by default
- WHEN the user clicks the Fecha column header
- THEN the URL contains `?sort_order=asc`
- AND the oldest orders display first
