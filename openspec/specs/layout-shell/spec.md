# Layout Shell Specification

## Purpose

Define the 260px fixed sidebar + fluid content area layout that replaces the current top navbar. ALL existing routes, links, form submissions, and interactive features MUST continue working.

## Requirements

### Requirement: Fixed Sidebar Navigation

The system SHALL render a 260px-wide sidebar fixed to the left edge of the viewport, containing the app logo and navigation links.

- Sidebar MUST have background `#f8fafc` and full viewport height
- Sidebar MUST contain the MELI Manager logo SVG at the top
- Active nav item MUST display a 3px blue left bar (`#1a73e8`) with light blue tint background
- Nav items MUST link to the same routes as the current top navbar: `/`, `/productos`, `/calculadora`, `/publicaciones`, `/publicar`, `/importar`, `/cuentas`, `/config`

#### Scenario: Sidebar renders with navigation

- GIVEN the user loads any page
- WHEN the template renders
- THEN a 260px sidebar SHALL appear on the left with all nav links
- AND clicking each link SHALL navigate to the correct route

#### Scenario: Active item highlighted

- GIVEN the user is on the Products page
- WHEN the sidebar renders
- THEN the "Productos" item SHALL show a 3px blue left bar and tinted background

### Requirement: Fluid Content Area

The content area SHALL occupy the remaining viewport width to the right of the sidebar.

#### Scenario: Content fills available space

- GIVEN a page with the sidebar rendered
- WHEN the page loads
- THEN the main content SHALL fill the space to the right of the 260px sidebar
- AND flash messages SHALL appear at the top of the content area

### Requirement: Account Switcher Preserved

The account switcher dropdown SHALL move to the sidebar bottom area while retaining all functionality: click-to-open, click-away-to-close, cuenta activation links, and status indicators.

#### Scenario: Account switching still works

- GIVEN the user has multiple cuentas
- WHEN they click the cuenta selector in the sidebar
- THEN the dropdown SHALL open showing all cuentas
- AND clicking a different cuenta SHALL activate it via the existing `/cuenta/<cid>/activar` route

### Requirement: All Existing Functionality Preserved

The layout shell MUST NOT break any existing form submission, route, link, button, or JavaScript behavior. This is a PURE UI restyle.

#### Scenario: Form submissions unchanged

- GIVEN a form on any page (search, product creation, publish, config)
- WHEN the user submits the form
- THEN the same POST/GET action, field names, and target URL MUST be used as before the restyle
