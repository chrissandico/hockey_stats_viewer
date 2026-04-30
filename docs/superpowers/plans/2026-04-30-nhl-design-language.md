# NHL Design Language Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the NHL.com black treatment (black nav, Inter font, #0055e9 blue, dark footer) to every page of the Hockey Stats Viewer.

**Architecture:** Rewrite `assets/css/style.css` with NHL design tokens as CSS custom properties, make targeted structural changes to Python layout files for nav/login/home/footer, and add a shared `footer.py` component used by all pages.

**Tech Stack:** Python/Dash, dash-bootstrap-components, Bootstrap 5, plain CSS custom properties, Google Fonts (Inter)

**Spec:** `docs/superpowers/specs/2026-04-30-nhl-design-language.md`

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Modify | `hockey_stats_webapp/app.py` | Add Inter font URL; rewrite `create_login_layout()` |
| Modify | `hockey_stats_webapp/layouts/navigation.py` | Switch to `nhl-navbar` class, remove Bootstrap color props |
| Modify | `hockey_stats_webapp/layouts/main_layout.py` | Add black hero, NHL card grid, import footer |
| Modify | `hockey_stats_webapp/assets/css/style.css` | Full NHL theme rewrite |
| Create | `hockey_stats_webapp/components/footer.py` | Dark footer component |
| Modify | `hockey_stats_webapp/layouts/player_layout.py` | Add footer, update loading color |
| Modify | `hockey_stats_webapp/layouts/team_layout.py` | Add footer, update loading color |
| Modify | `hockey_stats_webapp/layouts/game_layout.py` | Add footer, update loading color |
| Modify | `hockey_stats_webapp/layouts/opponent_layout.py` | Add footer, update loading color |
| Modify | `hockey_stats_webapp/layouts/recent_games_layout.py` | Add footer, update loading color |
| Modify | `hockey_stats_webapp/layouts/performance_layout.py` | Add footer, update loading color |
| Modify | `hockey_stats_webapp/components/unified_filter_bar.py` | Add `nhl-filter-card` class to filter card |
| Modify | `hockey_stats_webapp/components/__init__.py` | Export `create_footer` |

---

## Task 1: CSS Foundation — Inter Font, Root Variables, Global Body

**Files:**
- Modify: `hockey_stats_webapp/app.py` (line 34–37)
- Modify: `hockey_stats_webapp/assets/css/style.css` (lines 1–70, replace entirely)

- [ ] **Step 1: Add Inter to external_stylesheets in app.py**

  Open `hockey_stats_webapp/app.py`. Find the `external_stylesheets` list (~line 34) and add the Inter Google Fonts URL:

  ```python
  app = dash.Dash(
      __name__,
      external_stylesheets=[
          dbc.themes.BOOTSTRAP,
          "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
          "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&display=swap",
      ],
      suppress_callback_exceptions=True,
      meta_tags=[
          {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
      ],
  )
  ```

- [ ] **Step 2: Replace the top of style.css with NHL tokens and global body override**

  Replace lines 1–8 of `hockey_stats_webapp/assets/css/style.css` (the existing `/* Hockey Stats Web Application Styles */` block and `body {}`) with:

  ```css
  /* ============================================================
     NHL Design Language — Hockey Stats Viewer
     Tokens extracted from nhl.com/stats via designlang
     ============================================================ */

  :root {
    --nhl-bg-dark:       #000000;
    --nhl-bg-dark-2:     #1a1a1a;
    --nhl-bg-light:      #ffffff;
    --nhl-bg-light-2:    #f8f8f8;
    --nhl-primary:       #0055e9;
    --nhl-primary-hover: #0042bb;
    --nhl-text-primary:  #121212;
    --nhl-text-secondary:#6f6f6f;
    --nhl-text-muted:    #98989e;
    --nhl-border:        #e0e0e0;
    --nhl-border-light:  #f2f2f2;
    --nhl-positive:      #468254;
    --nhl-negative:      #c8102e;
  }

  /* Global */
  body {
    font-family: 'Inter', sans-serif;
    background-color: var(--nhl-bg-light);
    color: var(--nhl-text-primary);
    margin: 0;
  }
  ```

- [ ] **Step 3: Replace the old Bootstrap color overrides with NHL versions**

  Find and replace the block starting at `/* Blue and White Theme (Toronto Maple Leafs inspired) */` (lines 10–43) with:

  ```css
  /* Bootstrap primary color overrides */
  .btn-primary {
    background-color: var(--nhl-primary) !important;
    border-color: var(--nhl-primary) !important;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    border-radius: 8px;
  }

  .btn-primary:hover {
    background-color: var(--nhl-primary-hover) !important;
    border-color: var(--nhl-primary-hover) !important;
  }

  .btn-outline-primary {
    color: var(--nhl-primary) !important;
    border-color: var(--nhl-primary) !important;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    border-radius: 8px;
  }

  .btn-outline-primary:hover,
  .btn-outline-primary.active {
    background-color: var(--nhl-primary) !important;
    color: white !important;
  }

  .card-header {
    background-color: var(--nhl-bg-light-2);
    border-bottom: 2px solid var(--nhl-primary);
  }
  ```

- [ ] **Step 4: Run the app and verify Inter font loads**

  ```bash
  cd hockey_stats_webapp && python app.py
  ```

  Open `http://localhost:8050`. Open browser DevTools → Elements, inspect any text element. Computed font-family should show `Inter`. The nav will still be blue (we fix that in Task 2).

- [ ] **Step 5: Commit**

  ```bash
  git add hockey_stats_webapp/app.py hockey_stats_webapp/assets/css/style.css
  git commit -m "feat: add NHL design tokens and Inter font as CSS foundation"
  ```

---

## Task 2: Navigation Bar — Black with NHL Blue Active Tab

**Files:**
- Modify: `hockey_stats_webapp/layouts/navigation.py` (lines 13–41)
- Modify: `hockey_stats_webapp/assets/css/style.css` (add `.nhl-navbar` block)

- [ ] **Step 1: Update navigation.py to use NHL class instead of Bootstrap color**

  Replace the `dbc.Navbar(...)` call in `create_navigation()` with:

  ```python
  return dbc.Navbar(
      dbc.Container([
          # Brand/logo
          dbc.NavbarBrand("⬡ Hockey Stats", className="nhl-navbar-brand"),

          # Toggle button for mobile view
          dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),

          # Navigation links
          dbc.Collapse(
              dbc.Nav([
                  dbc.NavItem(dbc.NavLink("Home", href="/", active="exact")),
                  dbc.NavItem(dbc.NavLink("Player Stats", href="/player", active="exact")),
                  dbc.NavItem(dbc.NavLink("Team Stats", href="/team", active="exact")),
                  dbc.NavItem(dbc.NavLink("Game Stats", href="/game", active="exact")),
                  dbc.NavItem(dbc.NavLink("Opponent Stats", href="/opponent", active="exact")),
              ], className="me-auto", navbar=True),
              id="navbar-collapse",
              navbar=True,
              is_open=False,
          ),

          # Logout button
          dbc.NavItem(dbc.Button("Logout", id="logout-button", className="nhl-navbar-logout ms-2")),
      ], fluid=True),
      dark=True,
      className="nhl-navbar mb-0",
      sticky="top",
  )
  ```

  Note: `color` prop is removed (we control background entirely via CSS). `dark=True` keeps Bootstrap's `navbar-dark` class so text inherits white.

- [ ] **Step 2: Add `.nhl-navbar` CSS block to style.css**

  Add after the Bootstrap override block (after the `card-header` rule from Task 1):

  ```css
  /* ============================================================
     Navigation
     ============================================================ */
  .nhl-navbar {
    background-color: var(--nhl-bg-dark) !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0 24px;
    min-height: 52px;
  }

  .nhl-navbar-brand {
    color: #ffffff !important;
    font-weight: 900;
    font-size: 15px;
    letter-spacing: 0.5px;
    margin-right: 24px;
  }

  .nhl-navbar .nav-link {
    color: var(--nhl-text-muted) !important;
    font-size: 13px;
    font-weight: 500;
    padding: 0 14px !important;
    height: 52px;
    display: flex;
    align-items: center;
    border-bottom: 2px solid transparent;
    transition: color 0.2s, border-color 0.2s;
  }

  .nhl-navbar .nav-link:hover {
    color: #ffffff !important;
  }

  .nhl-navbar .nav-link.active {
    color: #ffffff !important;
    border-bottom: 2px solid var(--nhl-primary);
  }

  .nhl-navbar-logout {
    background: transparent !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: var(--nhl-text-muted) !important;
    font-size: 12px !important;
    padding: 4px 12px !important;
    border-radius: 4px !important;
  }

  .nhl-navbar-logout:hover {
    color: #ffffff !important;
    border-color: rgba(255, 255, 255, 0.5) !important;
  }

  /* Mobile navbar toggler */
  .nhl-navbar .navbar-toggler {
    border-color: rgba(255, 255, 255, 0.2);
  }

  @media (max-width: 768px) {
    .nhl-navbar .nav-link {
      height: auto;
      padding: 12px 14px !important;
      border-bottom: none;
      border-left: 2px solid transparent;
    }
    .nhl-navbar .nav-link.active {
      border-bottom: none;
      border-left: 2px solid var(--nhl-primary);
    }
  }
  ```

- [ ] **Step 3: Remove the old `.navbar-dark.bg-primary` rule from style.css**

  Delete this rule entirely (it's been replaced by `.nhl-navbar`):

  ```css
  .navbar-dark.bg-primary {
      background-color: #00205b !important; /* Maple Leafs blue */
  }
  ```

- [ ] **Step 4: Run app and verify black navigation**

  ```bash
  cd hockey_stats_webapp && python app.py
  ```

  Navigate to `http://localhost:8050`. Nav should be pure black. The active page link should have a blue underline. Logout button should be ghost-style on the right.

- [ ] **Step 5: Commit**

  ```bash
  git add hockey_stats_webapp/layouts/navigation.py hockey_stats_webapp/assets/css/style.css
  git commit -m "feat: apply NHL black navigation bar with blue active tab indicator"
  ```

---

## Task 3: Login Page — Full Dark Redesign

**Files:**
- Modify: `hockey_stats_webapp/app.py` — `create_login_layout()` function (~line 221)
- Modify: `hockey_stats_webapp/assets/css/style.css` — replace login CSS blocks

- [ ] **Step 1: Rewrite `create_login_layout()` in app.py**

  Replace the entire `create_login_layout()` function (lines 220–269) with:

  ```python
  def create_login_layout():
      return html.Div([
          html.Div([
              # Logo / Brand block
              html.Div([
                  html.Div("⬡", className="nhl-login-logo-icon"),
                  html.Div("HOCKEY STATS", className="nhl-login-logo-text"),
                  html.Div("Enter your team access code", className="nhl-login-subtitle"),
              ], className="nhl-login-brand"),

              # Login card
              html.Div([
                  html.Label("ACCESS CODE", className="nhl-login-label"),
                  dbc.InputGroup([
                      dbc.Input(
                          id="password-input",
                          type="password",
                          placeholder="Team access code",
                          className="nhl-login-input",
                      ),
                      dbc.Button(
                          html.I(id="password-toggle-icon", className="fas fa-eye"),
                          id="password-toggle",
                          className="nhl-login-toggle-btn",
                      ),
                  ], className="mb-3"),

                  html.Div(id="login-error", className="nhl-login-error mb-3"),

                  dbc.Button(
                      "Sign In",
                      id="login-button",
                      className="nhl-login-btn w-100",
                  ),
              ], className="nhl-login-card"),

              html.Div("© 2025 Hockey Stats Viewer", className="nhl-login-copyright"),
          ], className="nhl-login-inner")
      ], className="nhl-login-page")
  ```

  All element IDs (`password-input`, `password-toggle`, `password-toggle-icon`, `login-error`, `login-button`) are preserved — the callbacks will continue to work unchanged.

- [ ] **Step 2: Replace all login CSS in style.css**

  Remove the following blocks entirely (they reference old classes and inline styles):
  - `/* Login Page Styles */ .login-container { ... }` (lines ~242–247)
  - `/* Hockey-Themed Login Styles */` through `.hockey-puck-loader` (lines ~256–565)

  Replace with:

  ```css
  /* ============================================================
     Login Page
     ============================================================ */
  .nhl-login-page {
    background-color: var(--nhl-bg-dark);
    min-height: 100vh;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .nhl-login-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 24px;
    width: 100%;
    max-width: 400px;
  }

  .nhl-login-brand {
    text-align: center;
    margin-bottom: 40px;
  }

  .nhl-login-logo-icon {
    color: #ffffff;
    font-size: 36px;
    margin-bottom: 12px;
  }

  .nhl-login-logo-text {
    color: #ffffff;
    font-weight: 900;
    font-size: 22px;
    letter-spacing: 1px;
    font-family: 'Inter', sans-serif;
  }

  .nhl-login-subtitle {
    color: var(--nhl-text-muted);
    font-size: 13px;
    margin-top: 8px;
  }

  .nhl-login-card {
    background-color: var(--nhl-bg-dark-2);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 32px;
    width: 100%;
  }

  .nhl-login-label {
    display: block;
    color: var(--nhl-text-muted);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .nhl-login-input {
    background-color: var(--nhl-bg-dark) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 4px 0 0 4px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 12px !important;
  }

  .nhl-login-input::placeholder {
    color: var(--nhl-text-muted);
  }

  .nhl-login-input:focus {
    background-color: var(--nhl-bg-dark) !important;
    border-color: var(--nhl-primary) !important;
    box-shadow: 0 0 0 2px rgba(0, 85, 233, 0.25) !important;
    color: #ffffff !important;
    outline: none;
  }

  .nhl-login-toggle-btn {
    background-color: var(--nhl-bg-dark) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-left: none !important;
    border-radius: 0 4px 4px 0 !important;
    color: var(--nhl-text-muted) !important;
    padding: 0 14px !important;
    pointer-events: auto !important;
  }

  .nhl-login-toggle-btn:hover {
    color: #ffffff !important;
  }

  /* Disable the loading spinner on the toggle button */
  .nhl-login-toggle-btn.loading {
    color: var(--nhl-text-muted) !important;
  }
  .nhl-login-toggle-btn.loading::after {
    display: none !important;
  }

  .nhl-login-error {
    color: var(--nhl-negative);
    font-size: 13px;
    min-height: 20px;
  }

  .nhl-login-btn {
    background-color: var(--nhl-primary) !important;
    border: none !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    padding: 12px !important;
    transition: background-color 0.2s;
  }

  .nhl-login-btn:hover {
    background-color: var(--nhl-primary-hover) !important;
  }

  .nhl-login-copyright {
    color: var(--nhl-text-muted);
    font-size: 12px;
    margin-top: 24px;
  }

  @media (max-width: 480px) {
    .nhl-login-inner {
      padding: 32px 16px;
    }
    .nhl-login-card {
      padding: 24px 16px;
    }
  }
  ```

- [ ] **Step 3: Run app and verify login page**

  ```bash
  cd hockey_stats_webapp && python app.py
  ```

  Navigate to `http://localhost:8050/login`. Verify:
  - Full black background (no background image)
  - Dark card with subtle border
  - White text on input, blue Sign In button
  - Password toggle still works (click eye icon)
  - Entering a wrong code still shows error message in red

- [ ] **Step 4: Commit**

  ```bash
  git add hockey_stats_webapp/app.py hockey_stats_webapp/assets/css/style.css
  git commit -m "feat: redesign login page with NHL black treatment"
  ```

---

## Task 4: Footer Component — Dark Footer on All Pages

**Files:**
- Create: `hockey_stats_webapp/components/footer.py`
- Modify: `hockey_stats_webapp/components/__init__.py`
- Modify: `hockey_stats_webapp/assets/css/style.css` (add footer CSS)
- Modify: all 6 stats layout files + `main_layout.py`

- [ ] **Step 1: Create the footer component**

  Create `hockey_stats_webapp/components/footer.py`:

  ```python
  from dash import html


  def create_footer():
      return html.Footer([
          html.Div([
              html.Span("© 2025 Hockey Stats Viewer", className="nhl-footer-copy"),
              html.Div([
                  html.A("Home", href="/", className="nhl-footer-link"),
                  html.A("Players", href="/player", className="nhl-footer-link"),
                  html.A("Teams", href="/team", className="nhl-footer-link"),
                  html.A("Games", href="/game", className="nhl-footer-link"),
              ], className="nhl-footer-links"),
          ], className="nhl-footer-inner"),
      ], className="nhl-footer")
  ```

- [ ] **Step 2: Export from `components/__init__.py`**

  Open `hockey_stats_webapp/components/__init__.py`. Add:

  ```python
  from components.footer import create_footer
  ```

- [ ] **Step 3: Add footer CSS to style.css**

  Add after the login CSS block:

  ```css
  /* ============================================================
     Footer
     ============================================================ */
  .nhl-footer {
    background-color: var(--nhl-bg-dark-2);
    padding: 16px 24px;
    margin-top: auto;
  }

  .nhl-footer-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    max-width: 1440px;
    margin: 0 auto;
  }

  .nhl-footer-copy {
    color: var(--nhl-text-muted);
    font-size: 12px;
  }

  .nhl-footer-links {
    display: flex;
    gap: 16px;
  }

  .nhl-footer-link {
    color: var(--nhl-text-muted);
    font-size: 12px;
    text-decoration: none;
    transition: color 0.2s;
  }

  .nhl-footer-link:hover {
    color: #ffffff;
  }

  /* Remove old footer rule */
  footer {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
  }
  ```

- [ ] **Step 4: Add footer to `main_layout.py` (minimal — full rewrite happens in Task 5)**

  Open `hockey_stats_webapp/layouts/main_layout.py`. Add one import at the top:

  ```python
  from components.footer import create_footer
  ```

  Then remove the existing `html.Footer([...])` block (the last item inside `dbc.Container`, lines 68–72 in the original file), and append `create_footer()` *after* the closing of the top-level `dbc.Container(...)`, so the structure becomes:

  ```python
  return html.Div([
      create_navigation(),
      dbc.Container([
          # ... existing cards unchanged ...
      ], className="mb-0"),   # change mb-5 → mb-0 to close flush against footer
      create_footer(),
  ])
  ```

  Do not change the cards or add the hero yet — that happens in Task 5.

- [ ] **Step 5: Add footer to each stats layout file**

  For each of the 6 files below, add `from components.footer import create_footer` to the imports, then append `create_footer()` as the last child of the top-level `html.Div([...])`.

  **`hockey_stats_webapp/layouts/player_layout.py`** — find the top-level `return html.Div([` and add `create_footer()` as the final item before the closing `])`.

  **`hockey_stats_webapp/layouts/team_layout.py`** — same pattern.

  **`hockey_stats_webapp/layouts/game_layout.py`** — same pattern.

  **`hockey_stats_webapp/layouts/opponent_layout.py`** — same pattern.

  **`hockey_stats_webapp/layouts/recent_games_layout.py`** — same pattern.

  **`hockey_stats_webapp/layouts/performance_layout.py`** — same pattern.

- [ ] **Step 6: Run app and verify footer on every page**

  ```bash
  cd hockey_stats_webapp && python app.py
  ```

  Navigate to Home, Player Stats, Team Stats, Game Stats, Opponent Stats. Each page should have a `#1a1a1a` dark footer at the bottom with copyright text and nav links.

- [ ] **Step 7: Commit**

  ```bash
  git add hockey_stats_webapp/components/footer.py \
          hockey_stats_webapp/components/__init__.py \
          hockey_stats_webapp/assets/css/style.css \
          hockey_stats_webapp/layouts/main_layout.py \
          hockey_stats_webapp/layouts/player_layout.py \
          hockey_stats_webapp/layouts/team_layout.py \
          hockey_stats_webapp/layouts/game_layout.py \
          hockey_stats_webapp/layouts/opponent_layout.py \
          hockey_stats_webapp/layouts/recent_games_layout.py \
          hockey_stats_webapp/layouts/performance_layout.py
  git commit -m "feat: add dark footer component to all pages"
  ```

---

## Task 5: Home Page — Black Hero Banner + NHL Card Grid

**Files:**
- Modify: `hockey_stats_webapp/layouts/main_layout.py` (full rewrite of layout body)
- Modify: `hockey_stats_webapp/assets/css/style.css` (add hero + card CSS)

- [ ] **Step 1: Rewrite `main_layout.py` with NHL hero and card grid**

  Replace the full `create_main_layout()` body (keep imports and function signature):

  ```python
  from dash import html, dcc
  import dash_bootstrap_components as dbc
  from layouts.navigation import create_navigation
  from components.footer import create_footer


  def create_main_layout(team_context=None):
      team_name = team_context['team_name'] if team_context else "Hockey Stats"

      return html.Div([
          create_navigation(),

          # Black hero banner
          html.Div([
              html.H1(team_name, className="nhl-hero-title"),
              html.P("Your team's stats, powered by Google Sheets.", className="nhl-hero-subtitle"),
          ], className="nhl-hero"),

          # NHL card grid
          html.Div([
              dbc.Row([
                  dbc.Col(
                      html.Div([
                          html.Div("👤", className="nhl-card-icon"),
                          html.H3("Player Stats", className="nhl-card-title"),
                          html.P(
                              "Goals, assists, points, and more for every skater and goalie.",
                              className="nhl-card-desc"
                          ),
                          dbc.Button("View Players →", href="/player", className="nhl-btn-primary"),
                      ], className="nhl-card"),
                      md=4
                  ),
                  dbc.Col(
                      html.Div([
                          html.Div("🏒", className="nhl-card-icon"),
                          html.H3("Team Stats", className="nhl-card-title"),
                          html.P(
                              "Team-level performance, rankings, and breakdowns by period.",
                              className="nhl-card-desc"
                          ),
                          dbc.Button("View Teams →", href="/team", className="nhl-btn-secondary"),
                      ], className="nhl-card"),
                      md=4
                  ),
                  dbc.Col(
                      html.Div([
                          html.Div("📅", className="nhl-card-icon"),
                          html.H3("Game Stats", className="nhl-card-title"),
                          html.P(
                              "Game-by-game results, opponent analysis, and recent history.",
                              className="nhl-card-desc"
                          ),
                          dbc.Button("View Games →", href="/game", className="nhl-btn-secondary"),
                      ], className="nhl-card"),
                      md=4
                  ),
              ], className="g-3"),
          ], className="nhl-card-grid"),

          create_footer(),
      ])
  ```

- [ ] **Step 2: Add hero and card grid CSS to style.css**

  Add after the footer CSS block:

  ```css
  /* ============================================================
     Hero Banner
     ============================================================ */
  .nhl-hero {
    background-color: var(--nhl-bg-dark);
    padding: 40px 32px 32px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .nhl-hero-title {
    color: #ffffff;
    font-weight: 900;
    font-size: 28px;
    line-height: 1.2;
    margin-bottom: 8px;
  }

  .nhl-hero-subtitle {
    color: var(--nhl-text-muted);
    font-size: 14px;
    margin: 0;
  }

  /* ============================================================
     Home Card Grid
     ============================================================ */
  .nhl-card-grid {
    background-color: var(--nhl-bg-light-2);
    padding: 24px;
  }

  .nhl-card {
    background-color: var(--nhl-bg-light);
    border: 1px solid var(--nhl-border);
    border-radius: 8px;
    padding: 20px;
    box-shadow: rgba(0, 0, 0, 0.06) 0 2px 8px;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .nhl-card-icon {
    font-size: 24px;
    margin-bottom: 10px;
  }

  .nhl-card-title {
    color: var(--nhl-text-primary);
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 8px;
  }

  .nhl-card-desc {
    color: var(--nhl-text-secondary);
    font-size: 13px;
    line-height: 1.5;
    flex: 1;
    margin-bottom: 16px;
  }

  /* ============================================================
     Buttons — NHL variants
     ============================================================ */
  .nhl-btn-primary {
    background-color: var(--nhl-primary) !important;
    border: none !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    text-decoration: none;
    display: inline-block;
  }

  .nhl-btn-primary:hover {
    background-color: var(--nhl-primary-hover) !important;
    color: #ffffff !important;
  }

  .nhl-btn-secondary {
    background-color: var(--nhl-bg-light) !important;
    border: 1px solid var(--nhl-border) !important;
    border-radius: 8px !important;
    color: var(--nhl-text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    text-decoration: none;
    display: inline-block;
  }

  .nhl-btn-secondary:hover {
    background-color: var(--nhl-bg-light-2) !important;
    color: var(--nhl-text-primary) !important;
  }
  ```

- [ ] **Step 3: Run app and verify home page**

  ```bash
  cd hockey_stats_webapp && python app.py
  ```

  Go to `http://localhost:8050`. Should show:
  - Black hero banner with white team name
  - Three white cards on a `#f8f8f8` grid background
  - First card has blue button, others have outlined buttons
  - Dark footer at bottom

- [ ] **Step 4: Commit**

  ```bash
  git add hockey_stats_webapp/layouts/main_layout.py hockey_stats_webapp/assets/css/style.css
  git commit -m "feat: apply NHL hero banner and card grid to home page"
  ```

---

## Task 6: Stats Tables + Loading Spinner Color

**Files:**
- Modify: `hockey_stats_webapp/assets/css/style.css` (table CSS section)
- Modify: all stats layout files (update `dcc.Loading` color)

- [ ] **Step 1: Replace the DataTable CSS in style.css**

  Find the `/* DataTable Styles */` block (~line 231) and the `/* Table Styles */` block (~line 45). Replace both with:

  ```css
  /* ============================================================
     Stats Tables
     ============================================================ */

  /* Regular Bootstrap tables */
  .table {
    width: 100%;
    margin-bottom: 0;
    color: var(--nhl-text-primary);
    border-collapse: collapse;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
  }

  .table th {
    font-size: 11px;
    font-weight: 500;
    color: var(--nhl-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 9px 6px;
    border-bottom: 1px solid var(--nhl-border);
    text-align: left;
    vertical-align: bottom;
    white-space: nowrap;
  }

  .table td {
    padding: 9px 6px;
    vertical-align: middle;
    border-top: 1px solid var(--nhl-border-light);
    color: var(--nhl-text-secondary);
  }

  /* First column (rank / name) */
  .table td:first-child {
    color: var(--nhl-text-secondary);
  }

  /* Zebra stripe */
  .table-striped tbody tr:nth-of-type(even) {
    background-color: var(--nhl-bg-light-2);
  }

  .table-hover tbody tr:hover {
    background-color: rgba(0, 85, 233, 0.04);
  }

  /* Dash DataTable overrides */
  .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
    background-color: var(--nhl-bg-light-2);
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 500;
    color: var(--nhl-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    text-align: center;
    border-bottom: 1px solid var(--nhl-border);
  }

  .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    text-align: center;
    color: var(--nhl-text-secondary);
    border-bottom: 1px solid var(--nhl-border-light);
  }

  /* Make table-responsive horizontal scroll cleaner */
  .table-responsive {
    display: block;
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  ```

- [ ] **Step 2: Update `dcc.Loading` color in all stats layout files**

  In each stats layout file, find every occurrence of `color="#00205b"` inside `dcc.Loading(...)` and replace it with `color="#0055e9"`.

  Files to update:
  - `hockey_stats_webapp/layouts/player_layout.py`
  - `hockey_stats_webapp/layouts/team_layout.py`
  - `hockey_stats_webapp/layouts/game_layout.py`
  - `hockey_stats_webapp/layouts/opponent_layout.py`
  - `hockey_stats_webapp/layouts/recent_games_layout.py`
  - `hockey_stats_webapp/layouts/performance_layout.py`

  Also update the loading overlay text color in style.css:

  Find `.loading-overlay .loading-text` and `.loading-message` rules and update:
  ```css
  .loading-overlay .loading-text {
    color: var(--nhl-primary);
  }
  .loading-message {
    color: var(--nhl-primary);
  }
  ._dash-loading::after {
    color: var(--nhl-primary);
  }
  ```

- [ ] **Step 3: Update remaining `#00205b` color references in style.css**

  Search style.css for any remaining `#00205b`, `#001a4d`, `rgba(0, 32, 91`, `rgba(0, 32,91` strings and replace each:
  - `#00205b` → `var(--nhl-primary)` or `#0055e9`
  - `#001a4d` → `var(--nhl-primary-hover)` or `#0042bb`
  - `rgba(0, 32, 91, 0.1)` → `rgba(0, 85, 233, 0.1)`
  - `rgba(0, 32, 91, 0.25)` → `rgba(0, 85, 233, 0.25)`

  Remaining references are in: `.Select-option:hover`, `.Select-option.is-selected`, `.hockey-input:focus`, `.progress-bar`.

- [ ] **Step 4: Run app and verify table styling**

  ```bash
  cd hockey_stats_webapp && python app.py
  ```

  Navigate to Player Stats. Tables should show:
  - Grey uppercase column headers
  - Alternating `#f8f8f8` / white row stripe
  - NHS blue loading spinner (not Maple Leafs blue)

- [ ] **Step 5: Commit**

  ```bash
  git add hockey_stats_webapp/assets/css/style.css \
          hockey_stats_webapp/layouts/player_layout.py \
          hockey_stats_webapp/layouts/team_layout.py \
          hockey_stats_webapp/layouts/game_layout.py \
          hockey_stats_webapp/layouts/opponent_layout.py \
          hockey_stats_webapp/layouts/recent_games_layout.py \
          hockey_stats_webapp/layouts/performance_layout.py
  git commit -m "feat: apply NHL table styles and update loading spinner to NHL blue"
  ```

---

## Task 7: Filter Bar + Dropdown Colors + Final Cleanup

**Files:**
- Modify: `hockey_stats_webapp/assets/css/style.css` (filter bar, dropdown, progress bar, skeleton)

- [ ] **Step 1: Add `nhl-filter-card` class to unified_filter_bar.py**

  Open `hockey_stats_webapp/components/unified_filter_bar.py`. Find the `return dbc.Card([` call (~line 103) and add `className="nhl-filter-card"`:

  ```python
  return dbc.Card([
      dbc.CardHeader([
          html.H5("Filters", className="mb-0")
      ]),
      dbc.CardBody([
          dbc.Row(columns, className="g-3"),
          # ... rest unchanged
      ])
  ], className="nhl-filter-card mb-3")
  ```

- [ ] **Step 2: Add filter bar CSS to style.css**

  Add after the table CSS block:

  ```css
  /* ============================================================
     Filter Bar
     ============================================================ */
  .nhl-filter-card {
    border: none;
    border-bottom: 1px solid var(--nhl-border);
    border-radius: 0;
    background-color: var(--nhl-bg-light);
  }

  .nhl-filter-card .card-header {
    background-color: var(--nhl-bg-light);
    border-bottom: 1px solid var(--nhl-border-light);
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 600;
    color: var(--nhl-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .nhl-filter-card .card-body {
    padding: 12px 16px;
    background-color: var(--nhl-bg-light);
  }

  .form-label.fw-bold {
    font-size: 11px;
    font-weight: 600 !important;
    color: var(--nhl-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .form-select {
    border-color: var(--nhl-border) !important;
    border-radius: 4px !important;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: var(--nhl-text-primary);
  }

  .form-select:focus {
    border-color: var(--nhl-primary) !important;
    box-shadow: 0 0 0 2px rgba(0, 85, 233, 0.15) !important;
  }
  ```

- [ ] **Step 3: Update Dash Select dropdown CSS to NHL colors**

  Find the `/* Dropdown Styles */` block (~line 102) and update the border colors:

  ```css
  /* Dropdown Styles */
  .Select-control, .dash-dropdown .Select-control {
    border-radius: 4px;
    border: 1px solid var(--nhl-border);
    height: 44px;
    font-size: 13px;
    font-family: 'Inter', sans-serif;
    background-color: var(--nhl-bg-light);
  }

  .Select-menu-outer, .dash-dropdown .Select-menu-outer {
    border-bottom-right-radius: 4px;
    border-bottom-left-radius: 4px;
    border: 1px solid var(--nhl-border);
    border-top: none;
    font-size: 13px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    z-index: 1000;
  }

  .Select-value, .dash-dropdown .Select-value {
    line-height: 44px !important;
    padding-left: 10px;
  }

  .Select-placeholder, .dash-dropdown .Select-placeholder {
    line-height: 44px !important;
    padding-left: 10px;
    color: var(--nhl-text-muted);
  }

  .Select-input, .dash-dropdown .Select-input {
    height: 44px;
    padding-left: 10px;
  }

  .Select-option, .dash-dropdown .Select-option {
    padding: 10px;
    font-size: 13px;
    border-bottom: 1px solid var(--nhl-border-light);
  }

  .Select-option:hover, .dash-dropdown .Select-option:hover {
    background-color: rgba(0, 85, 233, 0.06);
  }

  .Select-option.is-selected, .dash-dropdown .Select-option.is-selected {
    background-color: rgba(0, 85, 233, 0.12);
    color: var(--nhl-primary);
  }
  ```

- [ ] **Step 4: Update progress bar and skeleton colors**

  Find `.progress-bar` rule and update:

  ```css
  .progress-bar {
    background: var(--nhl-primary);
    transition: width 0.3s ease;
  }
  ```

  Find `.dash-spinner` rule and update:

  ```css
  .dash-spinner {
    border-color: var(--nhl-primary) !important;
  }
  ```

- [ ] **Step 5: Final check — search for any remaining old blue values**

  ```bash
  grep -n "00205b\|001a4d\|rgba(0, 32, 91" hockey_stats_webapp/assets/css/style.css
  ```

  Expected output: no matches. If any appear, replace them using the mapping from Task 6 Step 3.

  Also check Python layout files:

  ```bash
  grep -rn "00205b\|001a4d" hockey_stats_webapp/layouts/ hockey_stats_webapp/components/ hockey_stats_webapp/app.py
  ```

  Expected output: no matches.

- [ ] **Step 6: Run app and do a full walkthrough**

  ```bash
  cd hockey_stats_webapp && python app.py
  ```

  Visit each page and confirm:
  - [ ] Login: black page, dark card, NHL blue button
  - [ ] Home: black nav, black hero, light card grid, dark footer
  - [ ] Player Stats: black nav, filter bar with NHL selects, Inter font tables, dark footer
  - [ ] Team Stats: same treatment
  - [ ] Game Stats: same treatment
  - [ ] Opponent Stats: same treatment
  - No Maple Leafs blue (#00205b) visible anywhere

- [ ] **Step 7: Commit**

  ```bash
  git add hockey_stats_webapp/assets/css/style.css \
          hockey_stats_webapp/components/unified_filter_bar.py
  git commit -m "feat: apply NHL colors to filter bar, dropdowns, and remaining components"
  ```

---

## Done

All 7 tasks complete. The app now matches the NHL.com black treatment:
- Inter font throughout
- Black nav with NHL blue active underline
- Login: full dark page with dark card
- Home: black hero + NHL card grid
- All stats pages: NHL table styles + dark footer
- All blue accents use `#0055e9` (NHL primary) instead of `#00205b` (Maple Leafs)
