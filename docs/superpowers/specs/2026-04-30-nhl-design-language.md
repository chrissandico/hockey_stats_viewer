# NHL.com Design Language — Hockey Stats Viewer

**Date:** 2026-04-30
**Approach:** CSS-first rewrite with targeted Python layout tweaks
**Source:** Design tokens extracted from https://www.nhl.com/stats/ via `designlang`

---

## Goals

Apply the NHL.com black treatment across all pages of the Hockey Stats Viewer (a Python/Dash + Bootstrap 5 app). Every page — including login — gets the same consistent look: black nav, white stats body, Inter font, NHL blue CTAs, dark footer.

---

## Color Palette

All values sourced from `design-extract-output/nhl-com-variables.css`.

| Role | Token | Value |
|---|---|---|
| Nav / hero background | `--nhl-bg-dark` | `#000000` |
| Footer / card dark bg | `--nhl-bg-dark-2` | `#1a1a1a` |
| Page body background | `--nhl-bg-light` | `#ffffff` |
| Card grid background | `--nhl-bg-light-2` | `#f8f8f8` |
| Primary blue (CTAs, links, active) | `--nhl-primary` | `#0055e9` |
| Primary text | `--nhl-text-primary` | `#121212` |
| Secondary text / inactive nav | `--nhl-text-secondary` | `#6f6f6f` |
| Muted text / nav ghost | `--nhl-text-muted` | `#98989e` |
| Border / dividers | `--nhl-border` | `#e0e0e0` |
| Table row separator | `--nhl-border-light` | `#f2f2f2` |
| Positive stat (+/-) | `--nhl-positive` | `#468254` |
| Negative stat (+/-) | `--nhl-negative` | `#c8102e` |

---

## Typography

- **Font family:** `Inter` — loaded from Google Fonts (weights 400, 500, 700, 900)
- **Added to:** `app.py` external_stylesheets, replaces Bootstrap default
- **Body:** 14px / 400 / 21px line-height
- **Nav links:** 13px / 500
- **Table column headers:** 11px / 500 / uppercase / 0.5px letter-spacing
- **Card titles:** 14px / 700
- **Hero heading:** 28px / 900
- **Button labels:** 13–14px / 500–700

---

## Navigation

**File:** `hockey_stats_webapp/navigation.py`

- Background: `#000000`
- Height: 52px
- Logo: white, weight 900, `⬡ HOCKEY STATS`
- Active page link: white text + `2px solid #0055e9` bottom border
- Inactive page links: `#98989e`, no underline
- Logout: right-aligned, `#98989e`
- Mobile: existing collapse behaviour preserved, dark background

Bootstrap classes to remove: `navbar-dark bg-primary`
Replace with: custom class `nhl-navbar`

---

## Login Page

**File:** `hockey_stats_webapp/app.py` — `create_login_layout()` function (~line 221)

Note: login uses a single **team access code** field (no username). The password-show/hide toggle button is kept.

- Full-page background: `#000000` (replaces current background image + glass card)
- Centred vertically and horizontally
- Logo block: hexagon icon + "HOCKEY STATS" in white, weight 900; subtitle `#98989e` ("Enter your team access code")
- Login card: `#1a1a1a` background, `rgba(255,255,255,0.1)` border, 8px radius, 32px padding
- Input field: black background, `rgba(255,255,255,0.15)` border, 4px radius, white text, placeholder "Team access code"
- Field label: `#98989e`, 11px, 600 weight, uppercase, 0.8px letter-spacing ("ACCESS CODE")
- Password toggle button: styled as icon-only, `#98989e` icon, no visible border
- Sign In button: full-width, `#0055e9` fill, white text, 8px radius, 12px vertical padding, 700 weight
- Error message: `#c8102e` text below input
- No background image, no gradients, no backdrop-filter, no puck spinner

---

## Home / Dashboard Page

**File:** `hockey_stats_webapp/layouts/main_layout.py`

- Hero banner: `#000000` background, white title (28px / 900), `#98989e` subtitle
- Card grid: `#f8f8f8` background, 3-column grid, 16px gap, 24px padding
- Each card: white, `#e0e0e0` border, 8px radius, `rgba(0,0,0,0.06) 0 2px 8px` shadow, 20px padding
- First card (Player Stats): blue filled CTA button
- Other cards: outlined CTA buttons (white bg, `#e0e0e0` border)
- Footer appended below grid

---

## Stats Tables (all stats pages)

Applies to: player, team, game, opponent, recent games layouts.

- Full-width, `border-collapse: collapse`, no outer border
- **Header row:** 11px, uppercase, `#6f6f6f`, 500 weight, `#e0e0e0` bottom border
- **Active sort column header:** `#0055e9` text + sort arrow indicator
- **Row padding:** 9px vertical, 6px horizontal
- **Zebra stripe:** even rows `#f8f8f8`, odd rows white
- **Row separator:** `1px solid #f2f2f2`
- **Rank column:** `#6f6f6f`
- **Player/entity name:** `#0055e9`, 600 weight (clickable link style)
- **Primary sort value:** `#121212`, 700 weight
- **Secondary stat cells:** `#6f6f6f`
- **+/- column:** positive → `#468254`, negative → `#c8102e`

---

## Buttons & Filter Bar

Two variants:

**Primary (filled):**
- Background: `#0055e9`
- Text: `#ffffff`, 13px, 500 weight
- Border radius: 8px
- Padding: 6px 14px

**Secondary (outlined):**
- Background: `#ffffff`
- Text: `#121212`, 13px, 500 weight
- Border: `1px solid #e0e0e0`
- Border radius: 8px
- Padding: 6px 14px

Filter bar sits between the nav and table: white background, 44px height, `#e0e0e0` bottom border, 24px horizontal padding.

---

## Footer

Add a dark footer to every page layout.

- Background: `#1a1a1a`
- Text: `#98989e`, 12px, Inter
- Copyright left, nav links right
- 16px vertical padding, 24px horizontal padding

Implementation: add a `footer_component()` helper in `components/` and include it in every layout's return value.

---

## CSS Implementation Plan

**File:** `hockey_stats_webapp/assets/css/style.css`

1. Add `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap');` at top
2. Define all NHL tokens as CSS custom properties on `:root`
3. Override Bootstrap body font: `body { font-family: 'Inter', sans-serif; }`
4. Write component-scoped rules for: `.nhl-navbar`, `.nhl-footer`, `.nhl-login`, `.nhl-hero`, `.nhl-card-grid`, `.nhl-filter-bar`, `.nhl-table`, `.nhl-btn-primary`, `.nhl-btn-secondary`
5. Remove/replace existing hardcoded `#00205b` Maple Leafs blue references

**File:** `hockey_stats_webapp/app.py`

- Add Google Fonts Inter URL to `external_stylesheets`

**Python layout files:** targeted structural changes only — class names, wrapper divs for footer, hero section markup on home page, login layout restructure.

---

## Out of Scope

- Dark mode toggle
- Per-team colour theming
- Animations (puck spinner removed from login; no new animations added)
- shadcn/ui or Tailwind (app stays on Bootstrap + custom CSS)
