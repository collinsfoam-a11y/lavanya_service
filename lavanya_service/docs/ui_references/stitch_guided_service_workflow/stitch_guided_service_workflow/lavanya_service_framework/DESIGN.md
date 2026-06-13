---
name: Lavanya Service Framework
colors:
  surface: '#fdf7ff'
  surface-dim: '#ded7e6'
  surface-bright: '#fdf7ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f7f1ff'
  surface-container: '#f2ebfa'
  surface-container-high: '#ece6f4'
  surface-container-highest: '#e6e0ef'
  on-surface: '#1c1a24'
  on-surface-variant: '#494456'
  inverse-surface: '#322f3a'
  inverse-on-surface: '#f5eefd'
  outline: '#7a7487'
  outline-variant: '#cac3d9'
  surface-tint: '#6533ed'
  primary: '#5412dd'
  on-primary: '#ffffff'
  primary-container: '#6d3df5'
  on-primary-container: '#e9e0ff'
  inverse-primary: '#ccbeff'
  secondary: '#545f73'
  on-secondary: '#ffffff'
  secondary-container: '#d5e0f8'
  on-secondary-container: '#586377'
  tertiary: '#823700'
  on-tertiary: '#ffffff'
  tertiary-container: '#a84900'
  on-tertiary-container: '#ffddcd'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e7deff'
  primary-fixed-dim: '#ccbeff'
  on-primary-fixed: '#1f0060'
  on-primary-fixed-variant: '#4d00d2'
  secondary-fixed: '#d8e3fb'
  secondary-fixed-dim: '#bcc7de'
  on-secondary-fixed: '#111c2d'
  on-secondary-fixed-variant: '#3c475a'
  tertiary-fixed: '#ffdbca'
  tertiary-fixed-dim: '#ffb690'
  on-tertiary-fixed: '#331100'
  on-tertiary-fixed-variant: '#783200'
  background: '#fdf7ff'
  on-background: '#1c1a24'
  surface-variant: '#e6e0ef'
typography:
  display-metrics:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.02em
  page-title:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  section-title:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-default:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  button-text:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  field-label:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.01em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  container-margin: 24px
  gutter: 16px
---

## Brand & Style
The design system focuses on high-velocity service management for staff users. The brand personality is **efficient, authoritative, and focused**, minimizing cognitive load for support agents handling high ticket volumes. 

The design style follows a **Corporate / Modern** aesthetic with high-density layouts and clear information hierarchy. It utilizes a systematic approach to depth and color to ensure that "Next Actions" are never missed and work priority is immediately apparent upon dashboard entry.

## Colors
The palette is engineered for clarity. The **Lavanya Purple** acts as the primary driver for all interactive elements, while the **Deep Navy** provides high-contrast grounding for typography. 

The extensive status palette is used for immediate visual categorization. Each status color must be paired with a 10% opacity background of the same hue when used in "Pill" components to ensure legibility while maintaining the distinct color coding.

## Typography
This design system uses a strictly utilitarian typographic scale. **Inter** is utilized for its exceptional legibility in data-heavy environments. 

- **Numerical Data:** Use `display-metrics` for ticket counts on dashboard cards.
- **Form Labels:** Always use `field-label` in the secondary color (Deep Navy) for maximum readability against white surfaces.
- **Hierarchy:** Maintain clear distinction between `page-title` and `section-title` to help users navigate multi-panel forms.

## Layout & Spacing
The layout relies on a **Fluid Grid** model with a base-8 spacing system.

- **Desktop:** A permanent 240px side navigation bar on the left. Content area uses a 12-column fluid grid with 16px gutters.
- **Margins:** Standard outer padding for containers is 24px (`lg`). 
- **Density:** High-density layouts are preferred. Use 16px (`md`) padding for cards and 8px (`sm`) for vertical spacing between form fields.

## Elevation & Depth
Depth is used sparingly to define "Work Zones." 

- **Level 0 (Background):** Soft App Background (#F8FAFC) - No shadow.
- **Level 1 (Cards/Panels):** Surface White (#FFFFFF) with a 1px border (#E2E8F0) and a very soft ambient shadow (0px 1px 3px rgba(0,0,0,0.05)).
- **Level 2 (High Emphasis):** Used for "Next Action" panels. These use a subtle 2px border in Lavanya Purple or a light indigo tint to pull focus without breaking the layout flow.
- **Level 3 (Popovers/Modals):** Standard elevation with a more pronounced shadow for focus.

## Shapes
A **Soft** shape language is employed to maintain a professional, structured feel while remaining approachable.

- **Buttons & Inputs:** 4px (`0.25rem`) corner radius.
- **Cards & Panels:** 8px (`0.5rem`) corner radius.
- **Status Chips:** Full radius (Pill-shaped) to distinguish them clearly from interactive buttons.

## Components

### Buttons
- **Primary:** Lavanya Purple background, White text. High-weight (600).
- **Secondary:** White background, 1px Border (#E2E8F0), Deep Navy text.
- **Ghost:** No background or border, used for secondary actions in lists.

### Work Priority Cards
Cards should feature the `display-metrics` count in the top left, a `section-title` label below it, and a bottom-aligned CTA link or button.

### Status Chips
Pill-shaped containers using the status colors defined in the color section. Text color should be the full-saturation hex, while the background should be the same color at 10-15% opacity.

### Forms & Input Fields
- **Fields:** 40px height, 1px #E2E8F0 border, white background.
- **Focus State:** 2px Lavanya Purple ring.
- **Collapsible Panels:** Use a 1px border separator with a chevron icon to the right of the `section-title`.

### Navigation
- **Side Nav:** Deep Navy background or high-contrast White. Active states should be indicated by a 4px vertical Lavanya Purple bar on the left edge and a light background tint.