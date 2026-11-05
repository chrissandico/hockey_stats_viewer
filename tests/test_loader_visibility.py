"""Tests pinning the loader's on-screen placement during recompute.

The defect (verified in the real app 2026-11-05): switching the Games
window showed a blank page for the whole ~30s recompute — no Luffy,
no percentage, no progress bar — even though the identical loader
worked on initial page load. Root cause is in Dash 2.13 itself:
dcc.Loading renders its spinner inside an absolutely-positioned
overlay that spans the FULL height of the wrapped content and
flex-centers the spinner in it. The shell Loading (#main-loading)
wraps the entire page, so on a built page (measured 3,414px tall on a
phone) the spinner lands in the middle of the page height — 1,980px
down, below the fold — while the hidden content leaves a blank top.
On initial load the content is still short, so the centred spinner
happens to land on screen, which is why the bug hid behind "works on
load, missing on switch".

The fix pins the spinner element to the viewport in style.css. These
tests pin the three contracts that together keep the experience
visible on every load:

1. The spinner rule in style.css pins the spinner to the viewport
   (position: fixed, placed under the navbar, horizontally centred).
2. app.py still declares exactly ONE dcc.Loading — the shell loader
   (PR #15's one-loader rule) — with id "main-loading".
3. zamboni-loader.js still anchors the percentage readout inside the
   spinner element itself (PRs #18-#20), so the readout rides with
   the pinned spinner wherever it is placed.

Run:  python -m pytest tests/test_loader_visibility.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(HERE, "..", "hockey_stats_webapp")


def _read(*parts):
    with open(os.path.join(*parts), "r", encoding="utf-8",
              newline="") as fh:
        return fh.read()


def _spinner_rule_block(css):
    """The declaration block of the rule that styles Dash's spinner
    classes (.dash-default-spinner / .dash-sk-circle /
    .dash-dot-spinner) with the Zamboni art."""
    start = css.index(".dash-default-spinner,")
    open_brace = css.index("{", start)
    close_brace = css.index("}", open_brace)
    return css[open_brace:close_brace]


def test_spinner_is_pinned_to_the_viewport():
    """If this rule ever loses the fixed positioning, Dash centers the
    spinner in the full page height again and it leaves the screen on
    every tall page — the Games-window switch goes back to a blank
    wait with no Luffy, no percentage and no bar."""
    block = _spinner_rule_block(_read(APP_DIR, "assets", "css",
                                      "style.css"))
    assert re.search(r"position:\s*fixed\s*!important", block), (
        "spinner must be position:fixed so Dash's full-height overlay "
        "centering cannot push it below the fold")
    assert re.search(r"top:\s*84px", block), (
        "spinner sits just under the sticky navbar")
    assert re.search(r"left:\s*50%", block)
    assert "translateX(-50%)" in block, (
        "spinner stays horizontally centred in the viewport")
    assert re.search(r"z-index:\s*\d+", block), (
        "spinner must paint above page content while pinned")


def test_app_still_has_exactly_one_loading_component():
    """PR #15's rule: one loader for the whole app. A second
    dcc.Loading (e.g. wrapped around a page section to 'fix' this)
    would defeat the single shared Luffy experience."""
    app_py = _read(APP_DIR, "app.py")
    assert app_py.count("dcc.Loading(") == 1
    assert 'id="main-loading"' in app_py


def test_percentage_readout_still_anchors_inside_the_spinner():
    """The readout is appended INSIDE the spinner element (found via
    #main-loading first), so when the spinner is pinned to the
    viewport the percentage text and gold bar ride with it."""
    js = _read(APP_DIR, "assets", "js", "zamboni-loader.js")
    assert "getElementById('main-loading')" in js
    assert "appendChild" in js
    assert "zamboni-pct" in js
