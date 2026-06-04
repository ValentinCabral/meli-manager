# Orders Sync Specification

## Purpose

Fetch real orders from the MELI API, store them in local SQLite tables, and enable deduplicated re-syncs. This is the foundation for real revenue metrics and the ventas section.

## Requirements

### Requirement: Sync is manual and button-triggered

The system MUST provide a manual sync mechanism (dashboard button, same pattern as existing `/meli/sync`) that fetches paid orders from MELI and stores them locally.

#### Scenario: Dashboard sync button exists and works

- GIVEN the user is on the dashboard with an active MELI account
- WHEN the user clicks the Sync Orders button
- THEN the system calls `GET /orders/search?seller={user_id}&order.date_created.from={date}&order.date_created.to={date}`
- AND stores each order's data in the `ordenes` table

#### Scenario: Sync without active account shows warning

- GIVEN no MELI account is configured
- WHEN the user clicks Sync Orders
- THEN the system flashes a warning "Conectá una cuenta de MercadoLibre primero"
- AND no API call is made

### Requirement: Orders data model

The system MUST create two new tables: `ordenes` and `orden_items`. `ordenes` SHALL store order-level fields and `orden_items` SHALL store line-item data linked to existing publications.

#### Scenario: Order is stored with all required fields

- GIVEN a successful API response for a paid order
- WHEN the system saves the order
- THEN `ordenes` contains: `meli_order_id` (unique), `total_paid_amount`, `marketplace_fee`, `shipping_cost`, `status`, `date_created`, `buyer_nickname`, `cuenta_id`
- AND `orden_items` contains each item with `meli_item_id`, `quantity`, `unit_price`, `total_amount`, linked to the parent order

#### Scenario: Order links to existing publications

- GIVEN an order item with `meli_item_id` matching an existing publication's `meli_item_id`
- WHEN the order item is stored
- THEN `orden_items.item_meli_id` references the publication
- AND the link enables the ventas section to show the product name

### Requirement: Deduplication on re-sync

The system MUST deduplicate orders by `meli_order_id`. Re-syncing SHALL update existing rows instead of inserting duplicates.

#### Scenario: Same order synced twice updates existing row

- GIVEN an order with `meli_order_id=MLA123` was previously synced
- WHEN a re-sync includes the same order
- THEN the existing row is updated with new data
- AND no duplicate row is created

### Requirement: Initial sync covers last 12 months

The system SHOULD sync the last 12 months of paid orders on the first sync (or when no orders exist locally). The SHALL filter by `order.date_created.from` (365 days ago) and `order.date_created.to` (today).

#### Scenario: First sync fetches 12 months of data

- GIVEN the `ordenes` table has zero rows for the active account
- WHEN sync is triggered
- THEN the API call includes `order.date_created.from` set to 365 days before today
- AND `order.status=paid` is used as filter

### Requirement: Pagination respects MELI rate limits

The system MUST paginate through MELI orders search results, applying the same delay pattern used in the existing publications sync to stay under the 100 req/min rate limit.

#### Scenario: Multiple pages are fetched sequentially

- GIVEN the first API response returns `paging.total > offset`
- WHEN the system continues fetching
- THEN subsequent requests increment `offset` by the page size
- AND a short delay is applied between requests
