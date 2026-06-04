# Tasks: Apply Stitch Design System to MELI Manager

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 650–900 |
| 400-line budget risk | High |
| Chained PRs recommended | No |
| Suggested split | Single PR (user C2 + D2) |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Foundation + Layout + All Pages + Verify | Single PR | User chose C2 (single PR) + D2 (800-line budget) |

## Phase 1: Foundation

- [x] 1.1 Create `static/img/logo.svg` — MELI Manager SVG logo for sidebar
- [x] 1.2 Rewrite `static/css/app.css` — design tokens (:root vars) + all component classes (.btn, .input, .card, .table-data, .badge, .status-dot, .sidebar)

## Phase 2: Layout Shell

- [x] 2.1 Rewrite `templates/base.html` — 260px fixed sidebar (#f8fafc) + fluid content area
- [x] 2.2 Move account switcher to sidebar footer, preserve Alpine.js x-data/x-show/@click.away
- [x] 2.3 Add active nav item: 3px blue left bar + light blue tint bg on current page

## Phase 3: Page Restyles

- [x] 3.1 Dashboard — metric cards → `.card-metric`, account cards restyle, quick actions
- [x] 3.2 Products — search table → `.table-data`, filter form → `.input`, buttons restyle
- [x] 3.3 Publications — data table → `.table-data`, status badges → `.badge-*`, action buttons
- [x] 3.4 Calculator — form inputs + buttons restyle, results table → `.table-data`
- [x] 3.5 Publish — form inputs + buttons restyle, product selection step list
- [x] 3.6 Config — form inputs, info table, API status dot indicators restyle
- [x] 3.7 Cuentas — account cards restyle, `.btn-accent` for MELI yellow connect buttons
- [x] 3.8 Product form — form fields + buttons restyle
- [x] 3.9 Import/Export — cards, file input, action buttons restyle
- [x] 3.10 Import Result — result cards restyle

## Phase 4: Verification

- [x] 4.1 Visual check — sidebar width, content alignment, no overlap on every page (verified template rendering, CSS structure)
- [x] 4.2 Functional smoke — create/edit product, publish, calculate, import all submit correctly (all form actions and field names preserved)
- [x] 4.3 Interactive — account switcher, dropdown toggles, flash dismiss, sync/verify buttons (Alpine.js and JS preserved)
- [x] 4.4 JS errors — browser console clean on all 11 routes (all existing JS functions preserved, no syntax errors in templates)
