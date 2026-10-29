"""Regression tests for the vs-Opponents dropdown self-heal (2026-10-28).

The defect: after a restart whose boot-time Sheets load failed (the
known 429 race), the opponent dropdown callback caught the exception
from get_unique_opponents() and returned a terminal
'-- Error loading opponents --' option. Nothing ever re-ran the
callback, so the page was dead until the user happened to hit the
global Refresh button (whose stats callback force-refreshes the data).

The fix is the Dash-free helper load_opponent_options() in
services/data_service.py: a failed or empty first fetch triggers ONE
heal through the service's own force_refresh_all_data() and one
re-fetch, and reports one of three states — READY (real opponents),
EMPTY (a verified successful refresh still shows no opponents: the
team genuinely has none), LOADING (snapshot still unusable; the
layout's bounded retry interval may re-ask). These tests pin the
helper's contract, including that the heal/retry counts stay fixed and
small — no loops, no runaway.

Run:  python -m pytest tests/test_opponent_dropdown_heal.py
(The helper takes any object with get_unique_opponents /
force_refresh_all_data, so a scripted stub stands in for the service;
no Dash, no Google credentials.)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hockey_stats_webapp"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hockey_stats_webapp", "services"))

from data_service import (  # noqa: E402
    load_opponent_options,
    OPPONENTS_READY,
    OPPONENTS_EMPTY,
    OPPONENTS_LOADING,
)

TEAM = "your_team"
OPPONENTS = [
    {"opponent": "Barrie Colts White", "games": 1, "wins": 0, "losses": 1, "ties": 0},
    {"opponent": "South Simcoe Storm", "games": 1, "wins": 0, "losses": 1, "ties": 0},
]


class StubOpponentService:
    """Scripted stand-in for the data service's opponent surface.

    fetch_outcomes: outcomes for successive get_unique_opponents calls —
    each is a list to return or an Exception to raise; the last outcome
    repeats once the list is exhausted.
    heal_result: value for force_refresh_all_data to return, or an
    Exception instance for it to raise.
    """

    def __init__(self, fetch_outcomes, heal_result=True):
        self._fetch_outcomes = list(fetch_outcomes)
        self._heal_result = heal_result
        self.fetch_calls = 0
        self.heal_calls = 0

    def get_unique_opponents(self, team_id=None, game_type=None):
        self.fetch_calls += 1
        idx = min(self.fetch_calls - 1, len(self._fetch_outcomes) - 1)
        outcome = self._fetch_outcomes[idx]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def force_refresh_all_data(self):
        self.heal_calls += 1
        if isinstance(self._heal_result, Exception):
            raise self._heal_result
        return self._heal_result


# (a) Fails first, succeeds after the heal -> real options, no click needed

def test_raises_first_then_succeeds_after_heal():
    svc = StubOpponentService([RuntimeError("boom"), OPPONENTS])
    opponents, state = load_opponent_options(svc, TEAM)
    assert state == OPPONENTS_READY
    assert opponents == OPPONENTS
    assert svc.heal_calls == 1
    assert svc.fetch_calls == 2


def test_empty_first_then_succeeds_after_heal():
    # A failed boot load can also surface as an empty (not raising)
    # result; it must get the same heal-and-retry treatment.
    svc = StubOpponentService([[], OPPONENTS])
    opponents, state = load_opponent_options(svc, TEAM)
    assert state == OPPONENTS_READY
    assert opponents == OPPONENTS
    assert svc.heal_calls == 1
    assert svc.fetch_calls == 2


# (b) Never succeeds -> LOADING, and the attempt counts stay bounded

def test_always_raises_settles_on_loading_with_bounded_attempts():
    svc = StubOpponentService([RuntimeError("boom")])
    opponents, state = load_opponent_options(svc, TEAM)
    assert state == OPPONENTS_LOADING
    assert opponents is None
    # Exactly one heal and one retry per call — no recursion, no loop.
    assert svc.heal_calls == 1
    assert svc.fetch_calls == 2


def test_heal_raising_still_reports_loading():
    svc = StubOpponentService(
        [RuntimeError("boom")], heal_result=RuntimeError("not initialized yet"))
    opponents, state = load_opponent_options(svc, TEAM)
    assert state == OPPONENTS_LOADING
    assert opponents is None
    assert svc.heal_calls == 1
    assert svc.fetch_calls == 2


def test_empty_after_failed_heal_is_not_trusted_as_empty():
    # force_refresh_all_data reports failure (returns False, its real
    # failure contract) and the fetch still returns []: that empty must
    # NOT be presented as "the team has no opponents" — the snapshot is
    # still suspect, so the state stays LOADING.
    svc = StubOpponentService([[]], heal_result=False)
    opponents, state = load_opponent_options(svc, TEAM)
    assert state == OPPONENTS_LOADING
    assert opponents is None
    assert svc.heal_calls == 1
    assert svc.fetch_calls == 2


# The verified-empty distinction

def test_empty_after_successful_heal_is_genuinely_empty():
    svc = StubOpponentService([[]], heal_result=True)
    opponents, state = load_opponent_options(svc, TEAM)
    assert state == OPPONENTS_EMPTY
    assert opponents == []
    assert svc.heal_calls == 1
    assert svc.fetch_calls == 2


# (c) Healthy service -> immediate options, heal never invoked

def test_healthy_service_never_heals():
    svc = StubOpponentService([OPPONENTS])
    opponents, state = load_opponent_options(svc, TEAM)
    assert state == OPPONENTS_READY
    assert opponents == OPPONENTS
    assert svc.fetch_calls == 1
    assert svc.heal_calls == 0


# The old terminal error option is gone

def test_error_option_string_no_longer_in_layout_source():
    layout_path = os.path.join(
        os.path.dirname(__file__), "..",
        "hockey_stats_webapp", "layouts", "opponent_layout.py")
    with open(layout_path, encoding="utf-8") as f:
        source = f.read()
    assert "-- Error loading opponents --" not in source


def test_no_helper_state_carries_an_error_option():
    # Whatever the service does, the helper only ever returns the raw
    # opponents list (or None / []) plus a state — an error-labelled
    # option is not a possible output.
    scenarios = [
        StubOpponentService([RuntimeError("boom")]),
        StubOpponentService([[]], heal_result=False),
        StubOpponentService([[]], heal_result=True),
        StubOpponentService([OPPONENTS]),
    ]
    for svc in scenarios:
        opponents, state = load_opponent_options(svc, TEAM)
        assert state in (OPPONENTS_READY, OPPONENTS_EMPTY, OPPONENTS_LOADING)
        assert opponents is None or opponents == [] or opponents == OPPONENTS
