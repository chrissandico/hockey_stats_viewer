# NHL Token Alignment — Design Spec

**Date:** 2026-06-26  
**Branch:** `feature/nhl-design`  
**Scope:** `hockey_stats_webapp/assets/css/style.css` only — login-page blocks untouched

## Goal

Align the existing NHL design token definitions and their usages in the nav/stats views with the authentic values extracted from nhl.com. No structural changes to components or Python layout files.

## Changes

### 1. Token corrections (`:root`)

Fix the primary blue and add missing tokens.

| Token | Before | After |
|---|---|---|
| `--nhl-primary` | `#0055e9` | `#0042bb` |
| `--nhl-primary-hover` | `#0042bb` | `#001e8c` |

Add:
```css
--nhl-accent:      #eca200;
--nhl-positive:    #00843d;
--nhl-negative:    #c8102e;
--nhl-shadow-card: rgba(0,0,0,.08) 0 16px 32px 0,
                   rgba(0,0,0,.16) 0 8px 16px 0,
                   rgba(0,0,0,.24) 0 4px 8px 0;
```

Note: `--nhl-positive` and `--nhl-negative` already existed with different values; update them to match the NHL extraction (`#00843d`, `#c8102e`).

### 2. Navigation

No structural changes. Active-tab indicator automatically corrects once `--nhl-primary` is fixed.

### 3. Buttons

NHL.com uses 0px border-radius (sharp corners) and `10px 32px` padding on primary buttons.

```css
/* before */
border-radius: 8px;

/* after */
border-radius: 0;
padding: 10px 32px;   /* primary only */
```

Applies to `.btn-primary` and `.btn-outline-primary`.

### 4. Cards

Update to NHL.com card spec: 24px radius + 3-layer soft shadow.

```css
/* before */
border-radius: 0.5rem;

/* after */
border-radius: 24px;
box-shadow: var(--nhl-shadow-card);
```

### 5. Tables

Table hover row background: replace old navy with NHL primary tint.

```css
/* before */
background-color: rgba(0, 32, 91, 0.075);

/* after */
background-color: rgba(0, 66, 187, 0.08);
```

### 6. Dropdowns

Replace all 6 occurrences of hardcoded `#00205b` with `var(--nhl-primary)`.  
Replace `rgba(0, 32, 91, …)` hover/selected tints with `rgba(0, 66, 187, …)`.

## Out of Scope

- Login page CSS blocks (`.hockey-login-page`, `.hockey-card`, `.hockey-login-btn`, etc.)
- Python layout files
- Any new components

## Success Criteria

- No `#00205b` or `#0055e9` in the nav/stats CSS sections
- Primary blue visually matches nhl.com (`#0042bb`)
- Buttons have sharp corners
- Cards have 24px radius and soft shadow
- All changes are on `feature/nhl-design` branch
