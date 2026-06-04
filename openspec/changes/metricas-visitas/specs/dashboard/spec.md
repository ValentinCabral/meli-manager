# Delta for dashboard

## ADDED Requirements

### Requirement: Sync Metrics button on dashboard

The system MUST add a "📊 Sync Metrics" button alongside "Sync Orders". Clicking triggers `/meli/sync-visits`.

#### Scenario: Button renders and navigates

- GIVEN the dashboard with an active account
- THEN a "📊 Sync Metrics" button is visible
- AND clicking navigates to `/meli/sync-visits`

#### Scenario: No account warns

- GIVEN no MELI account configured
- WHEN the button is clicked
- THEN the system flashes "Conectá una cuenta de MercadoLibre primero"
