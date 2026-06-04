# Design System Specification

## Purpose

Define the visual design tokens — colors, typography, spacing, and shadows — that all templates SHALL consume via `app.css`. These tokens replace Tailwind utility classes with a cohesive Stitch-based system.

## Requirements

### Requirement: Color Palette

The system MUST expose CSS custom properties for the color palette, matching the Stitch "Professional Commerce Interface".

| Token | Value | Usage |
|-------|-------|-------|
| `--md-sys-color-primary` | `#1a73e8` | Buttons, links, active states |
| `--md-sys-color-surface` | `#f9f9ff` | Page background |
| `--md-sys-color-surface-container` | `#e7eeff` | Card / section backgrounds |
| `--md-sys-color-on-surface` | `#111c2d` | Body text |
| `--md-sys-color-on-surface-variant` | `#414754` | Secondary text |
| `--md-sys-color-outline` | `#727785` | Borders |
| `--md-sys-color-outline-variant` | `#c1c6d6` | Subtle borders |
| `--md-sys-color-success` | `#10b981` | Status connected |
| `--md-sys-color-error` | `#ef4444` | Status disconnected |

#### Scenario: Colors applied consistently

- GIVEN any page in the app
- WHEN the page renders
- THEN all text, backgrounds, and borders MUST use the defined tokens

### Requirement: Typography Scale

The system MUST use Inter as the sole font family with five size/weight levels.

| Level | Size/Line-Height | Weight | Letter-Spacing | Usage |
|-------|-----------------|--------|----------------|-------|
| headline-lg | 30px/38px | 600 | -0.02em | Metric values |
| headline-md | 20px/28px | 600 | normal | Section titles |
| body-md | 14px/20px | 400 | normal | Body text |
| label-sm | 11px/14px | 600 | normal | Card titles, table headers |
| label-md | 12px/16px | 500 | 0.01em | Button text |

#### Scenario: Typography renders correctly

- GIVEN a page with headlines, body text, and labels
- WHEN the page loads
- THEN each element MUST use the correct font family Inter and matching typography token

### Requirement: Functionality Preservation

The design tokens MUST NOT alter any backend behavior, route handling, form submission, or JavaScript interactivity. Appearance-only changes.
