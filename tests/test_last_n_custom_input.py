"""Regression tests for the Last N custom-number path.

The defect (verified live 2026-11-05, fixed in PR #24): selecting
"Custom…" in the real app NEVER showed the numeric input, so a custom
window was unreachable. The visibility of the input was an output of
the store-sync callback, which only fires when the store changes — but
selecting Custom with an empty box resolved to the current store
value, the write callback's equality guard swallowed it as no_update,
the store never changed, and the sync never fired. Chicken-and-egg.
PR #23's tests invoked the pure helpers and missed it; these tests
instead pull the REAL registered callbacks out of a real Dash app's
callback_map and drive them in the exact sequence the browser fires
them, which is as close to the running app as pytest gets.

Run:  python -m pytest tests/test_last_n_custom_input.py
"""
import os
import sys

import dash
import pytest
from dash import html, no_update

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hockey_stats_webapp"))

from components.last_n_filter import (  # noqa: E402
    LAST_N_CUSTOM_ID, LAST_N_CUSTOM_WRAP_ID, LAST_N_PRESET_ID,
    LAST_N_STORE_ID, create_last_n_filter_component, create_last_n_store,
    register_last_n_callbacks,
)


@pytest.fixture()
def cbs():
    """The real callbacks, keyed by what they output."""
    app = dash.Dash(__name__)
    app.layout = html.Div([create_last_n_store(),
                           create_last_n_filter_component()])
    register_last_n_callbacks(app)

    by_output = {}
    for key, spec in app.callback_map.items():
        fn = spec["callback"]
        # Dash wraps registered callbacks with a context adapter that
        # needs a live request; __wrapped__ is the real function the
        # browser's calls ultimately run.
        by_output.setdefault(key, getattr(fn, "__wrapped__", fn))
    return {
        "write": by_output[f"{LAST_N_STORE_ID}.data"],
        "sync": by_output[f"..{LAST_N_PRESET_ID}.value...{LAST_N_CUSTOM_ID}.value.."],
        "toggle": by_output[f"{LAST_N_CUSTOM_WRAP_ID}.style"],
    }


def _find_input(component, target_id):
    if getattr(component, "id", None) == target_id:
        return component
    for child in getattr(component, "children", None) or []:
        if isinstance(child, (list, tuple)):
            for sub in child:
                found = _find_input(sub, target_id)
                if found is not None:
                    return found
        else:
            found = _find_input(child, target_id)
            if found is not None:
                return found
    return None


def test_visibility_is_owned_by_the_preset_selection(cbs):
    """Exactly one callback writes the wrap style, and it is keyed on
    the preset value — not on the store. (The original bug: the store
    sync owned it, and the store doesn't change when Custom is picked,
    so the input could never appear.)"""
    app = dash.Dash(__name__)
    app.layout = html.Div([create_last_n_store(),
                           create_last_n_filter_component()])
    register_last_n_callbacks(app)
    owners = [k for k in app.callback_map
              if k == f"{LAST_N_CUSTOM_WRAP_ID}.style"]
    assert len(owners) == 1
    spec = app.callback_map[owners[0]]
    inputs = [i["id"] + "." + i["property"] for i in
              (spec["inputs"] if isinstance(spec["inputs"], list)
               else [spec["inputs"]])]
    assert inputs == [f"{LAST_N_PRESET_ID}.value"]


def test_custom_flow_end_to_end(cbs):
    """The browser sequence for Dashboard custom=7."""
    # 1. User opens the dropdown and picks "Custom…" (box still empty).
    #    The visibility callback fires off the preset change alone.
    assert cbs["toggle"]("custom") == {"display": "inline"}
    #    The write callback sees custom + empty: mid-gesture, it must
    #    NOT resolve to All and must not touch the store.
    assert cbs["write"]("custom", None, None) is no_update

    # 2. User types 7 and confirms: a non-preset store value appears.
    assert cbs["write"]("custom", 7, None) == 7

    # 3. The sync agrees the control already shows the right state.
    assert cbs["sync"](7, "custom", 7) == (no_update, no_update)
    #    Visibility is still on while the user is in custom mode.
    assert cbs["toggle"]("custom") == {"display": "inline"}


def test_fresh_page_with_custom_store_reveals_input(cbs):
    """Cross-page arrival: a fresh control (defaults to All) syncs to a
    stored custom window, and the preset change reveals the input."""
    assert cbs["sync"](7, "all", None) == ("custom", 7)
    assert cbs["toggle"]("custom") == {"display": "inline"}


def test_typed_preset_value_does_not_snap_mid_gesture(cbs):
    """Typing 3 (a value that is also a preset) must not flip the
    control to the "Last 3 Games" preset and hide the box mid-typing."""
    assert cbs["write"]("custom", 3, None) == 3
    assert cbs["sync"](3, "custom", 3) == (no_update, no_update)
    assert cbs["toggle"]("custom") == {"display": "inline"}
    # ...but a fresh control still represents stored 3 as the preset.
    assert cbs["sync"](3, "all", None) == ("3", None)


def test_out_of_range_is_clamped_and_box_rewritten(cbs):
    assert cbs["write"]("custom", 45, None) == 30
    # Sync rewrites the visible box to the clamped value.
    assert cbs["sync"](30, "custom", 45) == ("custom", 30)
    assert cbs["write"]("custom", 0, None) == 1


def test_custom_input_has_no_min_max_attributes():
    """min/max attrs on Dash's number input swallow out-of-range
    values before the callbacks run (45 silently did nothing when the
    attrs were present). Clamping lives in the write callback."""
    component = create_last_n_filter_component()
    number_input = _find_input(component, LAST_N_CUSTOM_ID)
    assert number_input is not None
    assert getattr(number_input, "min", None) is None
    assert getattr(number_input, "max", None) is None


def test_switching_back_to_all_hides_input(cbs):
    assert cbs["write"]("all", 7, 7) is None
    assert cbs["sync"](None, "custom", 7) == ("all", 7)
    assert cbs["toggle"]("all") == {"display": "none"}


def test_preset_selection_still_writes_store(cbs):
    assert cbs["write"]("5", None, None) == 5
    assert cbs["write"]("all", None, 5) is None
    # Guard intact: resolving to the current value is a no-op.
    assert cbs["write"]("5", None, 5) is no_update
