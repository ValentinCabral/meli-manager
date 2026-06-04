# Design: Apply Stitch Design System to MELI Manager

## Technical Approach

Replace Tailwind CDN utility classes with a custom CSS design-token system mirroring Stitch's "Professional Commerce Interface". Four layers: (1) base layout + CSS variables, (2) component classes, (3) page-level application, (4) hover/focus refinements. Zero backend changes — pure UI restyle with all JS behaviors, form field names, routes, and Alpine.js interactions preserved intact.

## Architecture Decisions

### CSS Strategy: Custom Properties + Utility Classes

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Tailwind JIT (keep) | Fast dev but CDN limits custom tokens, bloated HTML | ❌ Remove CDN |
| CSS Modules / scoped | Requires build tool, no JS bundler in project | ❌ Overkill |
| CSS custom props + component classes | Matches Stitch token model, zero build step, easy to maintain | ✅ **Chosen** |

Rationale: The project has no JS bundler or build pipeline. Custom properties in `:root` mirror Stitch's token structure exactly, and component classes (`.btn-primary`, `.card-metric`) keep templates readable without Tailwind noise.

### Layout Migration: Sidebar + Top Bar

The current gradient navbar becomes a 260px fixed sidebar. Nav items move to the sidebar. The account switcher stays but moves to the sidebar footer. A thin top bar above content shows the active account and sync actions.

Preserving Alpine.js account switcher: the `x-data`, `@click.away`, and `x-show` directives remain unchanged — only the wrapper element changes from navbar to sidebar.

### Yellow Branding Coexistence

MELI yellow (`#FFE600`) is used in two specific buttons ("Conectar cuenta", "Publicar en MELI"). These keep their yellow treatment as accent actions, styled via a `.btn-accent` class over the base `.btn` component. The rest of the UI uses blue primary.

## Data Flow

No data flow changes — all routes, form submissions, and redirect chains are identical.

```
Browser ──GET──→ Flask route ──→ render_template("page.html", data)
                     ↑                      ↓
                     └── POST/redirect ──────┘
                    (identical before/after)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `static/css/app.css` | Modify | Replace Tailwind with design tokens + component classes |
| `static/img/logo.svg` | Create | MELI Manager SVG logo for sidebar |
| `templates/base.html` | Modify | Sidebar layout, flash messages below top bar |
| `templates/dashboard.html` | Modify | Metric cards → `.card-metric`, section cards → `.card` |
| `templates/products.html` | Modify | Table → `.table-data`, search form → new input classes |
| `templates/publications.html` | Modify | Table → `.table-data`, status badges → `.badge` |
| `templates/calculator.html` | Modify | Form → new input/button classes, results table restyle |
| `templates/publish.html` | Modify | Form → new input/button classes, step list restyle |
| `templates/config.html` | Modify | Form + info table restyle |
| `templates/cuentas.html` | Modify | Account cards restyle, action buttons update |
| `templates/product_form.html` | Modify | Form fields restyle |
| `templates/import_export.html` | Modify | Cards restyle, file input restyle |
| `templates/import_result.html` | Modify | Result cards restyle |

## Component Mapping

| Stitch Token | CSS Class / Variable | Used In |
|--------------|---------------------|---------|
| `--color-primary: #1a73e8` | `var(--primary)` | Buttons, links, active states |
| Metric card | `.card-metric` | Dashboard metricas |
| Data table | `.table-data` | products, publications, calculator results |
| Primary button | `.btn-primary` | "Nuevo Producto", "Guardar", etc. |
| Secondary button | `.btn-secondary` | Clear filters, Cancel |
| Accent button | `.btn-accent` | MELI yellow buttons (Conectar, Publicar) |
| Ghost link | `.btn-ghost` | Edit/delete actions in tables |
| Input | `.input` | All form inputs |
| Status badge | `.badge-{success,warning,danger,info}` | Publication status, stock levels |
| Status dot | `.status-dot` | Connection indicator |
| Sidebar item | `.sidebar-item--active` | Current page nav highlight |
| Card | `.card` | Section containers |

## Interfaces / Contracts

**No new interfaces.** The `CAMPAIGNS` JS constant, `toggleModo()`, `onProductChange()`, and `onListingTypeChange()` remain unchanged. Their element references (IDs, classes) are preserved or mapped to new class names.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Visual | Layout renders correctly | Manual: sidebar width, content alignment, no overlaps |
| Functional | All forms submit with correct fields | Manual smoke test: create/edit product, publish, calculate, import |
| Interactive | Dropdown toggle, mobile menu, flash auto-dismiss | Manual: click each interactive element |
| Regression | Account switcher, sync, verify buttons | Manual: switch accounts, click sync/verify, confirm redirects |
| JS | Inline scripts execute without errors | Browser console check for JS errors on every page |

## Migration / Rollout

Apply as a single PR. Merge order: (1) `app.css` tokens, (2) `base.html` layout, (3) templates in dependency order. Each template commit is independently revertible. Verify every route loads without JS errors after each batch of 2-3 templates.

## Open Questions

- [ ] Sidebar on narrow viewports — responsive mode is deferred but should we add a basic collapse toggle now?
