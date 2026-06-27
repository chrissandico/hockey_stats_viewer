# NHL Token Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the CSS token values and their usages in nav/stats sections of `style.css` with the authentic values extracted from nhl.com.

**Architecture:** Single-file CSS patch on the `feature/nhl-design` branch. All changes are inside `hockey_stats_webapp/assets/css/style.css`. No Python files touched. Login-page CSS blocks (`.hockey-login-page`, `.hockey-card`, `.hockey-login-btn`, etc.) are explicitly out of scope.

**Tech Stack:** CSS custom properties, Dash/Bootstrap 5

## Global Constraints

- Branch: `feature/nhl-design` — all commits go here
- Login-page CSS blocks must not be modified (`.hockey-login-page`, `.hockey-card`, `.hockey-login-btn`, `.hockey-header`, `.hockey-input`, `.password-toggle-btn`, `.login-container`, `.input-group`, `.puckSpin`, and their mobile/accessibility variants)
- No Python or HTML files modified
- Each task ends with a `git commit`

---

### Task 1: Fix primary color token and add missing tokens in `:root`

**Files:**
- Modify: `hockey_stats_webapp/assets/css/style.css` — `:root` block (lines 1–17)

**Interfaces:**
- Produces: `--nhl-primary: #0042bb`, `--nhl-primary-hover: #001e8c`, `--nhl-positive: #00843d`, `--nhl-negative: #c8102e`, `--nhl-accent: #eca200`, `--nhl-shadow-card` — consumed by all subsequent tasks

- [ ] **Step 1: Switch to the feature branch**

```bash
git checkout feature/nhl-design
```

Expected: `Switched to branch 'feature/nhl-design'`

- [ ] **Step 2: Update the `:root` block**

Replace the entire `:root` block at the top of `hockey_stats_webapp/assets/css/style.css`:

```css
:root {
  --nhl-bg-dark:       #000000;
  --nhl-bg-dark-2:     #1a1a1a;
  --nhl-bg-light:      #ffffff;
  --nhl-bg-light-2:    #f8f8f8;
  --nhl-primary:       #0042bb;
  --nhl-primary-hover: #001e8c;
  --nhl-text-primary:  #121212;
  --nhl-text-secondary:#6f6f6f;
  --nhl-text-muted:    #98989e;
  --nhl-border:        #e0e0e0;
  --nhl-border-light:  #f2f2f2;
  --nhl-accent:        #eca200;
  --nhl-positive:      #00843d;
  --nhl-negative:      #c8102e;
  --nhl-shadow-card:   rgba(0,0,0,.08) 0px 16px 32px 0px,
                       rgba(0,0,0,.16) 0px 8px 16px 0px,
                       rgba(0,0,0,.24) 0px 4px 8px 0px;
}
```

- [ ] **Step 3: Verify no old primary value remains in non-login CSS**

Search the file for `#0055e9` — should return zero matches outside the login section (there should be none at all since `#0055e9` only appeared in the old `:root`).

```bash
grep -n "0055e9" hockey_stats_webapp/assets/css/style.css
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add hockey_stats_webapp/assets/css/style.css
git commit -m "fix(css): correct NHL primary blue and add missing design tokens"
```

---

### Task 2: Fix button border-radius and padding

**Files:**
- Modify: `hockey_stats_webapp/assets/css/style.css` — `.btn-primary` and `.btn-outline-primary` blocks

**Interfaces:**
- Consumes: `--nhl-primary: #0042bb`, `--nhl-primary-hover: #001e8c` from Task 1
- Produces: sharp-cornered buttons matching nhl.com spec

- [ ] **Step 1: Update `.btn-primary`**

Find this block in `style.css`:

```css
.btn-primary {
  background-color: var(--nhl-primary) !important;
  border-color: var(--nhl-primary) !important;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  border-radius: 8px;
}
```

Replace with:

```css
.btn-primary {
  background-color: var(--nhl-primary) !important;
  border-color: var(--nhl-primary) !important;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  border-radius: 0;
  padding: 10px 32px;
}
```

- [ ] **Step 2: Update `.btn-outline-primary`**

Find:

```css
.btn-outline-primary {
  color: var(--nhl-primary) !important;
  border-color: var(--nhl-primary) !important;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  border-radius: 8px;
}
```

Replace with:

```css
.btn-outline-primary {
  color: var(--nhl-primary) !important;
  border-color: var(--nhl-primary) !important;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  border-radius: 0;
}
```

- [ ] **Step 3: Verify no `border-radius: 8px` remains in button blocks**

```bash
grep -n "border-radius: 8px" hockey_stats_webapp/assets/css/style.css
```

Expected: no output (the only `8px` radius was on buttons; `--radius-md: 8px` is not in this file).

- [ ] **Step 4: Commit**

```bash
git add hockey_stats_webapp/assets/css/style.css
git commit -m "fix(css): apply NHL sharp button corners and primary padding"
```

---

### Task 3: Fix card border-radius and shadow

**Files:**
- Modify: `hockey_stats_webapp/assets/css/style.css` — `.card` block

**Interfaces:**
- Consumes: `--nhl-shadow-card` from Task 1
- Produces: cards with 24px radius and 3-layer shadow matching nhl.com spec

- [ ] **Step 1: Update the `.card` block**

Find:

```css
/* Card Styles */
.card {
    border: none;
    border-radius: 0.5rem;
    overflow: hidden;
}
```

Replace with:

```css
/* Card Styles */
.card {
    border: none;
    border-radius: 24px;
    overflow: hidden;
    box-shadow: var(--nhl-shadow-card);
}
```

- [ ] **Step 2: Verify**

```bash
grep -n "0\.5rem" hockey_stats_webapp/assets/css/style.css
```

Expected: no output (the old `border-radius: 0.5rem` is gone).

- [ ] **Step 3: Commit**

```bash
git add hockey_stats_webapp/assets/css/style.css
git commit -m "fix(css): update card to NHL 24px radius and 3-layer shadow"
```

---

### Task 4: Fix table hover and dropdown hardcoded colors

**Files:**
- Modify: `hockey_stats_webapp/assets/css/style.css` — table hover block and dropdown blocks

**Interfaces:**
- Consumes: `--nhl-primary` (`#0042bb`) from Task 1
- Produces: zero occurrences of `#00205b` or `rgba(0, 32, 91` in non-login CSS

- [ ] **Step 1: Fix table hover row color**

Find:

```css
.table-hover tbody tr:hover {
    background-color: rgba(0, 32, 91, 0.075);
}
```

Replace with:

```css
.table-hover tbody tr:hover {
    background-color: rgba(0, 66, 187, 0.08);
}
```

- [ ] **Step 2: Fix dropdown border colors**

Find:

```css
.Select-control, .dash-dropdown .Select-control {
    border-radius: 0.25rem;
    border: 2px solid #00205b;
    height: 44px;
    font-size: 1.1rem;
    background-color: #f8f9fa;
}
```

Replace with:

```css
.Select-control, .dash-dropdown .Select-control {
    border-radius: 0.25rem;
    border: 2px solid var(--nhl-primary);
    height: 44px;
    font-size: 1.1rem;
    background-color: #f8f9fa;
}
```

- [ ] **Step 3: Fix dropdown menu outer border**

Find:

```css
.Select-menu-outer, .dash-dropdown .Select-menu-outer {
    border-bottom-right-radius: 0.25rem;
    border-bottom-left-radius: 0.25rem;
    border: 2px solid #00205b;
    border-top: none;
    font-size: 1.1rem;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    z-index: 1000;
}
```

Replace with:

```css
.Select-menu-outer, .dash-dropdown .Select-menu-outer {
    border-bottom-right-radius: 0.25rem;
    border-bottom-left-radius: 0.25rem;
    border: 2px solid var(--nhl-primary);
    border-top: none;
    font-size: 1.1rem;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    z-index: 1000;
}
```

- [ ] **Step 4: Fix dropdown option hover and selected tints**

Find:

```css
.Select-option:hover, .dash-dropdown .Select-option:hover {
    background-color: rgba(0, 32, 91, 0.1);
}

.Select-option.is-selected, .dash-dropdown .Select-option.is-selected {
    background-color: rgba(0, 32, 91, 0.2);
}
```

Replace with:

```css
.Select-option:hover, .dash-dropdown .Select-option:hover {
    background-color: rgba(0, 66, 187, 0.1);
}

.Select-option.is-selected, .dash-dropdown .Select-option.is-selected {
    background-color: rgba(0, 66, 187, 0.2);
}
```

- [ ] **Step 5: Verify zero remaining old-navy occurrences outside login blocks**

```bash
grep -n "00205b\|32, 91" hockey_stats_webapp/assets/css/style.css
```

Expected: no output. If any lines appear, check whether they fall inside a login-page block (`.hockey-` prefix). If they do, leave them. If not, fix them.

- [ ] **Step 6: Commit**

```bash
git add hockey_stats_webapp/assets/css/style.css
git commit -m "fix(css): replace old-navy hardcodes with NHL primary token in tables and dropdowns"
```

---

### Task 5: Manual visual verification

**Files:** none modified

- [ ] **Step 1: Start the dev server**

From the repo root:

```bash
python hockey_stats_webapp/app.py
```

Expected: server starts at `http://localhost:8050`

- [ ] **Step 2: Log in and check the nav bar**

Open `http://localhost:8050` in a browser. Log in with any valid team password.

Verify:
- Nav bar is solid black (`#000000`)
- Active tab has a blue underline — color should be `#0042bb` (a slightly darker, less electric blue than before)
- Inactive tab labels are medium gray (`#98989e`)

- [ ] **Step 3: Check a stats table**

Navigate to Player Stats or Team Stats. Hover over a table row.

Verify:
- Hover highlight is a subtle blue tint (not the old dark-navy `rgba(0,32,91)`)

- [ ] **Step 4: Check cards**

Verify any stat cards on the page have:
- Rounded corners (24px — noticeably rounder than before)
- A soft multi-layer shadow (visible as a gentle elevation, not a flat card)

- [ ] **Step 5: Check dropdowns**

Open any dropdown (e.g. game type filter). Verify:
- The border is `#0042bb` blue (slightly darker than the old `#0055e9`)
- Hover state is a light blue tint

- [ ] **Step 6: Confirm login page is untouched**

Navigate to `http://localhost:8050/logout` (or clear session) and return to the login page.

Verify: the login card still has the navy gradient header and hockey branding — it should look identical to before these changes.
