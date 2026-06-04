# Dashboard Specification

## Purpose

The dashboard shows aggregate metrics for the active account. Revenue metric MUST change from estimated (`stock × precio`) to real (`SUM(paid_amount)` from synced orders).

## Requirements

### Requirement: Revenue metric uses real orders data

The system MUST replace the `valor_venta_meli` metric (currently `SUM(stock * precio)` from `publicaciones`) with `SUM(total_paid_amount)` from the `ordenes` table. The SHALL be calculated per active account.

#### Scenario: Dashboard shows real revenue after order sync

- GIVEN the user has synced orders with `total_paid_amount` = 15000.50
- WHEN the dashboard loads
- THEN the revenue card shows `$15,001` (rounded to 2 decimal places)
- AND the value matches a direct SQL sum of the active account's orders

#### Scenario: Multiple accounts show per-account real revenue

- GIVEN the active account has $10,000 in orders and another account has $5,000
- WHEN the dashboard loads with the first account active
- THEN the revenue card shows `$10,000`
- AND switching accounts shows the correct per-account total

### Requirement: Empty state when no orders exist

If the `ordenes` table has no rows for the active account, the system MUST NOT show $0. Instead it SHALL display the message "Sincronizá órdenes para ver revenue real".

#### Scenario: First login before any sync shows prompt

- GIVEN no orders have been synced for the active account
- WHEN the dashboard renders
- THEN the revenue card displays "Sincronizá órdenes para ver revenue real"
- AND no "$0" or zero value is shown

### Requirement: Revenue metric label changes

The system MUST change the revenue card label from "Venta MELI" to "Revenue Real". The SHALL match the existing card styling and color scheme.

#### Scenario: Dashboard card shows updated label

- GIVEN the user visits the dashboard
- WHEN the metrics section renders
- THEN the revenue card label is "Revenue Real"
- AND the card maintains the same visual style as other metric cards

### Requirement: Sync orders button on dashboard

The system MUST add a "Sync Orders" button to the dashboard action area. The SHOULD be visually distinct from the existing "Sync" (publications) button.

#### Scenario: Sync Orders button appears on dashboard

- GIVEN the user is on the dashboard with an active MELI account
- THEN a "📥 Sync Orders" button is visible in the action area
- AND clicking it triggers the orders sync endpoint
