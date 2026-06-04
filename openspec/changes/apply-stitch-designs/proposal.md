# Proposal: Apply Stitch Design System to MELI Manager

## Intent

Replace Tailwind CDN + ad-hoc styling with a cohesive professional design system based on Stitch's "Professional Commerce Interface" — 260px sidebar, Inter typography, blue primary (#1a73e8), and consistent component tokens.

## Scope

### In Scope
1. **Base layout**: Fixed 260px sidebar + fluid content area (rewrite `base.html`)
2. **Design tokens**: Create `app.css` with Stitch colors, typography, spacing, shadows
3. **Component library**: Metric cards, data tables, buttons, inputs, status indicators
4. **Template restyling**: All 11 templates updated to new tokens
5. **Logo SVG**: Replace emoji branding with SVG

### Out of Scope
- Responsive/mobile breakpoints (deferred)
- Dark mode (deferred)
- Interactive JS components (dropdowns, modals)
- Backend or route changes

## Capabilities

No existing specs — first SDD change. New capabilities:

- `design-system`: Color/typography/spacing tokens
- `layout-shell`: Sidebar + content shell
- `component-library`: Cards, tables, buttons, inputs, status dots

## Approach

Four layers applied sequentially:

1. **Base** — Rewrite `base.html` layout and `app.css` tokens
2. **Components** — Metric cards, data tables, inputs, status indicators
3. **Pages** — Apply components to each template
4. **Refinement** — Transitions, hover states, focus rings

## Affected Areas

| Area | Impact |
|------|--------|
| `templates/base.html` | Full rewrite — sidebar layout |
| `static/css/app.css` | Replace Tailwind with tokens |
| `templates/dashboard.html` | Metric card restyle |
| `templates/products.html` | Table restyle |
| `templates/publications.html` | Table restyle |
| `templates/calculator.html` | Form restyle |
| `templates/publish.html` | Form restyle |
| `templates/config.html` | Form restyle |
| `templates/import_export.html` | Restyle |
| `templates/cuentas.html` | Restyle |
| `templates/product_form.html` | Form restyle |
| `static/img/logo.svg` | New file |

## Risks

- **Layout breakage**: Sidebar may overlap or misalign with content on narrow screens (responsive deferred)
- **Color clash**: MELI yellow (#FFE600) branding must coexist with blue primary (#1a73e8) — risk of visual inconsistency
- **Form width**: Sidebar reduces content width; wide forms (e.g. publish, config) need responsive handling

## Rollback Plan

Git revert of individual template commits, or full `git checkout -- templates/ static/css/`.

## Dependencies

- Inter font via Google Fonts
- Stitch design system as authoritative source

## Success Criteria

- [ ] All 11 templates use new design tokens
- [ ] Sidebar renders at 260px with correct active state
- [ ] Metric cards match Stitch specs (border, radius, typography)
- [ ] Data tables match Stitch specs (dividers, header, hover)
- [ ] Buttons/inputs match Stitch specs (padding, radius, focus halo)
- [ ] Logo SVG renders in sidebar
