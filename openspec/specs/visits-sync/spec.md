# Visits Sync Specification

## Purpose

Sync daily visit counts from MELI's `GET /visits/items` batch API into local SQLite.

## Requirements

### Requirement: Manual visits sync in batches of 20

The system MUST sync ALL active items' visits via `GET /visits/items?ids=ID1,ID2` in chunks of 20, with rate-limit delays. Table `visitas_publicacion` SHALL store `cuenta_id`, `meli_item_id`, `visitas INTEGER`, `fecha TEXT`, `synced_at`.

#### Scenario: Full sync across chunks

- GIVEN 45 active publications
- WHEN sync is triggered
- THEN 3 API calls are made (20, 20, 5 items each)
- AND each item's visits are stored with today's date

#### Scenario: No active items

- GIVEN zero active publications
- WHEN sync is triggered
- THEN no API calls are made

#### Scenario: Re-sync updates same-day row

- GIVEN `visitas=50` for MLA123 on 2026-06-04
- WHEN re-sync returns 75 visits for the same item+date
- THEN the existing row updates to 75 (no duplicate)
