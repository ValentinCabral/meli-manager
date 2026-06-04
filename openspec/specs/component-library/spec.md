# Component Library Specification

## Purpose

Define reusable UI components — metric cards, data tables, buttons, inputs, and status dots — that implement the Stitch design tokens consistently across all templates.

## Requirements

### Requirement: Metric Cards

Metric cards MUST use: white background, 1px `#E2E8F0` border, 8px border-radius, label-sm title, headline-lg value.

#### Scenario: Dashboard renders metric cards

- GIVEN the dashboard page with 6 metrics (productos, publicaciones, stock, etc.)
- WHEN the page renders
- THEN each metric SHALL appear as a card with the specified border, radius, and typography

### Requirement: Data Tables

Tables MUST use thin horizontal dividers `#F1F5F9`, light gray header background (`#f8fafc`), and row hover with blue tint (`#e7eeff`).

#### Scenario: Products table renders

- GIVEN the products page with product data
- WHEN the table renders
- THEN header row SHALL have light gray background with label-sm text
- AND each data row SHALL have thin horizontal dividers
- AND hovering a row SHALL tint it light blue

### Requirement: Buttons

Three variants: Primary (solid `#1a73e8`, white text, 8px radius), Secondary (white background, slate border), Ghost (blue `#1a73e8` text, no background).

#### Scenario: Primary button renders

- GIVEN any page with a primary action button
- WHEN it renders
- THEN it SHALL have solid `#1a73e8` background with white text and 8px radius

### Requirement: Input Fields

Inputs MUST be 40px height, 8px radius, 1px solid outline border, and on focus display blue border with a subtle shadow ring.

#### Scenario: Search input renders

- GIVEN the products search form
- WHEN the input renders
- THEN it SHALL be 40px tall with 8px radius and outline border
- AND on focus SHALL show blue border with shadow ring

### Requirement: Status Dots

Status MUST render as 8px circles: green (`#10b981`) for connected/active, red (`#ef4444`) for disconnected/inactive.

#### Scenario: Connection status shown

- GIVEN an active cuenta on the dashboard
- WHEN the status indicator renders
- THEN it SHALL be an 8px green circle
- AND an inactive cuenta SHALL show an 8px red circle

### Requirement: Functionality Preservation

All component restyles MUST preserve existing form field names, action URLs, method types, JavaScript behaviors, and interactive features (sync buttons, delete confirmations, dropdown toggles).

#### Scenario: Delete with confirmation still works

- GIVEN the products page
- WHEN the user clicks the delete button on a product row
- THEN a JavaScript confirmation dialog SHALL appear (existing behavior preserved)
- AND submitting SHALL POST to the same `/productos/eliminar` route with the same field names
