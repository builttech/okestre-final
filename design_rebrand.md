# Design System Inspired by Dayact IA

> Auto-extracted from `https://www.dayact.ia/dayact` on 2026-07-07

## 1. Visual Theme & Atmosphere

Clean, minimal, and product-focused with deliberate use of whitespace.

The hero section leads with "Overwatch_" followed by "Real-time monitoring and historical roll call archival of the 119th United States Congress. Data syn".

**Key Characteristics:**
- switzer as the heading font (custom web font loaded via @font-face)
- switzer as the body font for all running text
- Heading weight 300, letter-spacing -3px
- Light/white background (#f9f4ed) as the primary canvas
- Primary accent `#888888` used for CTAs and brand highlights
- 3 shadow level(s) detected — tinted shadows
- Sharp corners (0-2px) for a precise, technical aesthetic
- Tags: light, sharp, monochrome, monospace, sans-serif

## 2. Color Palette & Roles

### Primary
- **Primary Accent** (`#888888`) · `--color-primary`: Brand color, CTA backgrounds, link text, interactive highlights.
- **Secondary Accent** (`#aaaaaa`) · `--color-secondary`: Secondary brand, hover states, complementary highlights.
- **Background** (`#f9f4ed`) · `--color-bg`: Page background, primary canvas.
- **Background Secondary** (`#f4f4f5`) · `--color-bg-secondary`: Cards, surfaces, alternating sections.

### Text
- **Text Primary** (`#000000`) · `--color-text`: Headings and body text.
- **Text Secondary** (`#52525b`) · `--color-text-secondary`: Muted text, captions, placeholders.

### Borders & Surfaces
- **Border** (`#050505`) · `--color-border`: Dividers, outlines, input borders.

### Full Extracted Palette

| # | Hex | CSS Variable | Role | Area | Contrast |
|---|---|---|---|---|---|
| 1 | `#000000` | `--palette-1` | section | large | text-light |
| 2 | `#f4f4f5` | `--palette-2` | block | medium | text-dark |
| 3 | `#ffffff` | `--palette-3` | badge | medium | text-dark |
| 4 | `#52525b` | `--palette-4` | badge | medium | text-light |

## 3. Typography Rules

- **Heading Font:** `switzer` (web font)
- **Body Font:** `switzer` (web font)

### Type Hierarchy

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|---|---|---|---|---|---|
| H1 | switzer | 60px | 300 | 60px | -3px |
| Body | switzer | 14px | 300 | 22.75px | normal |
| Code | redditMono | 10px | 400 | 15px | normal |

### Type Scale

| Token | Size | Suggested Usage |
|---|---|---|
| Display | `60px` | headings |
| H1 | `30px` | headings |
| H2 | `20px` | headings |
| H3 | `16px` | headings |
| H4 | `14px` | headings |
| Body L | `12px` | body / supporting text |
| Body | `10px` | body / supporting text |
| Small | `9px` | body / supporting text |
| XS | `8px` | body / supporting text |

## 4. Component Stylings

### Primary Button

```css
.btn-primary {
  background: #f4f4f5;
  color: #000000;
  border-radius: 0px;
  padding: 0px 32px;
  font-size: 16px;
  font-weight: 400;
  border: none;
  cursor: pointer;
}
```

## 5. Layout Principles

- **Base spacing unit:** `16px` — use multiples (32px, 48px, 64px, etc.)

### Spacing Scale (extracted from real elements)

| Token | Value | Role |
|---|---|---|
| spacing-1 | `16px` | element |
| spacing-2 | `8px` | element |
| spacing-3 | `24px` | card |
| spacing-4 | `40px` | card |

### Border Radius Scale

| Token | Value | Element |
|---|---|---|

## 6. Depth & Elevation

| Level | Shadow | Usage |
|---|---|---|
| Mid | `rgba(255, 255, 255, 0.45) 0px 0px 8px 0px` | Dropdowns, popovers |
| Mid | `rgba(113, 113, 122, 0.3) 0px 0px 6px 0px` | Dropdowns, popovers |
| Low | `rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0, 0) 0px 0px 0px 0px, rgba(0, 0, 0...` | Cards, subtle elevation |

> **Note:** This site uses chromatic (color-tinted) shadows rather than pure black — this is a deliberate brand choice that adds warmth to elevation.

## 7. Do's and Don'ts

### Do
- Use `#f9f4ed` as the primary background color
- Use `switzer` for all headings and `switzer` for body text
- Use `#888888` as the single dominant accent/CTA color
- Maintain `16px` as the base spacing unit — all gaps should be multiples
- Keep corners sharp (0-2px radius) for a precise, technical feel
- Stick to grayscale + `#888888` accent — avoid color overload
- Apply the shadow system for elevation — use the extracted shadow values
- Use weight 300 for headings to match the brand's typographic voice

### Don't
- Don't use colors outside the extracted palette without justification
- Don't substitute switzer/switzer with generic alternatives
- Don't use irregular spacing — stick to 16px grid
- Don't use dark/black backgrounds — this is a light-themed design
- Don't use large border-radius — keep everything crisp and geometric
- Don't add additional saturated colors beyond the primary accent
- Don't use pure black (#000000) for text — use `#000000` instead
- Don't add decorative elements not present in the original design — no badges, ribbons, banners, or ornaments unless the source site uses them
- Don't invent UI patterns the source site doesn't have — if the original has no NEW badge, don't add one just because a red is in the palette

## 8. Responsive Behavior

| Breakpoint | Width | Notes |
|---|---|---|
| Mobile | < 640px | Single column, stack sections, reduce font sizes ~80% |
| Tablet | 640–1024px | 2-column where appropriate, maintain spacing ratios |
| Desktop | 1024–1440px | Full layout as designed |
| Wide | > 1440px | Max-width container, center content |

- Touch targets: minimum 44×44px on mobile
- Maintain 16px base unit across breakpoints — only scale multipliers

## 9. Agent Prompt Guide

### Quick Color Reference

```
Background:  #f9f4ed
Text:        #000000
Accent:      #888888
Secondary:   #aaaaaa
Border:      #050505
```

### Example Prompts

1. "Build a hero section with a `#f9f4ed` background, `switzer` heading in `#000000`, and a `#888888` CTA button with 0px radius."
2. "Create a pricing card using background `#f4f4f5`, border `#050505`, `switzer` for text, and 48px padding."
3. "Design a navigation bar — `#f9f4ed` background, `#000000` links, `#888888` for active state."
4. "Build a feature grid with 3 columns, 48px gap, each card using the card component style."
5. "Create a footer with `#000000` background, `#f9f4ed` text, and 32px padding."

### Iteration Guide

1. Start with layout structure (sections, grid, spacing)
2. Apply colors from the palette — background first, then text, then accents
3. Set typography — font families, sizes from the type scale, weights
4. Add components — buttons, cards, inputs using the specs above
5. Apply border-radius consistently across all elements
6. Add shadows for depth — use the extracted shadow values, not defaults
7. Check responsive behavior — test mobile and tablet layouts
8. Final pass — verify all colors match, spacing is consistent, fonts are correct

## 10. CSS Custom Properties

> 30 custom properties extracted from `:root` / `html` stylesheets.

### Color Variables

| Variable | Value |
|---|---|
| `--cream-50` | `#fdfcfa` |
| `--cream-100` | `#faf7f4` |
| `--cream-200` | `#fcf9f5` |
| `--cream-400` | `#f9f4ed` |
| `--cream-450` | `#f7f1e7` |
| `--cream-500` | `#f2ede3` |
| `--cream-850` | `#97896e` |
| `--cream-900` | `#b7a981` |
| `--gray-50` | `#f5f5f5` |
| `--gray-100` | `#f2f2f2` |
| `--gray-150` | `#dedede` |
| `--gray-200` | `#bdbbb6` |
| `--gray-250` | `#b3b3b3` |
| `--gray-300` | `#8f8f8f` |
| `--gray-400` | `#696969` |
| `--gray-500` | `#5a5a5a` |
| `--gray-600` | `#515151` |
| `--gray-700` | `#3b3b3b` |
| `--orange-400` | `#f1b143` |
| `--orange-500` | `#ea7900` |
| `--green-200` | `#ebffe4` |
| `--green-600` | `#217a04` |
| `--party-democrat` | `#2140e3` |
| `--party-republican` | `#e32128` |
| `--party-independent` | `#8b5cf6` |
| `--black` | `#000` |
| `--white` | `#fff` |

### Spacing Variables

| Variable | Value |
|---|---|
| `--content-max-width` | `1800px` |

### Other Variables

| Variable | Value |
|---|---|
| `--foreground` | `var(--black)` |
| `--background` | `var(--cream-400)` |
