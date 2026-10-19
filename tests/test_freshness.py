"""Freshness tests for the viewer cache stack (2026-10-19).

The viewer used to serve each page from four caches with independent
clocks (raw tabs 60 min, calculated games 5-60 min, leaderboards 30 min,
AI recaps forever), so new data took ~an hour to surface and one page
could mix snapshots. The fix:

- SheetsService: ONE shared freshness window (120 s). When it lapses, the
  next access reloads every tab together (one snapshot), and every reload
  bumps a data generation counter.
- DataService: computed caches (calculated games, leaderboards) are bound
  to that generation — a generation bump drops them.
- AISummaryService: recap cache keys carry a hash of the game digest, so
  a corrected game regenerates its recap instead of serving the old text.

Run:  python -m pytest tests/test_freshness.py
(No Google credentials needed: services are exercised with stubs.)
"""

import os
import sys
import time

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hockey_stats_webapp"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hockey_stats_webapp", "services"))

from sheets_service import SheetsService  # noqa: E402
from data_service import DataService  # noqa: E402
from ai_summary_service import AISummaryService  # noqa: E402

TAB_KEYS = ("teams", "parent_codes", "players", "games", "events", "game_roster")


# ---------------------------------------------------------------------------
# SheetsService: one shared epoch for all tabs
# ---------------------------------------------------------------------------

def _bare_sheets(ttl=120):
    """A SheetsService with no Google connection; refresh_all_data is faked
    to behave like the real one (fills every tab, stamps the epoch)."""
    svc = SheetsService.__new__(SheetsService)
    svc.cache = {}
    svc.last_refresh = {}
    svc.cache_ttl = ttl
    svc.data_epoch = None
    svc.data_generation = 0
    svc._refreshing_all = False
    svc.refresh_calls = 0

    def fake_refresh_all():
        svc.refresh_calls += 1
        for key in TAB_KEYS:
            svc.cache[key] = pd.DataFrame({"tab": [key]})
            svc._mark_refreshed(key)
        svc.data_epoch = time.time()

    svc.refresh_all_data = fake_refresh_all
    return svc


def test_first_access_loads_one_full_snapshot():
    svc = _bare_sheets()
    games = svc.get_games()
    assert svc.refresh_calls == 1
    assert games["tab"].iloc[0] == "games"
    # Every other tab came along in the same snapshot.
    for key in TAB_KEYS:
        assert key in svc.cache


def test_no_reload_inside_the_shared_window():
    svc = _bare_sheets()
    svc.get_games()
    svc.get_events()
    svc.get_players()
    assert svc.refresh_calls == 1


def test_epoch_lapse_reloads_all_tabs_together():
    svc = _bare_sheets(ttl=120)
    svc.get_games()
    # Corrupt one tab to prove the next reload restores ALL tabs, not just
    # the one being accessed (no mixed snapshots).
    svc.cache["events"] = pd.DataFrame()
    svc.data_epoch = time.time() - 121  # window lapsed

    svc.get_players()  # any access triggers the coordinated reload

    assert svc.refresh_calls == 2
    assert svc.cache["events"]["tab"].iloc[0] == "events"


def test_reload_bumps_generation_and_stamps_epoch():
    svc = _bare_sheets()
    assert svc.last_refresh_datetime is None
    svc.get_games()
    assert svc.data_generation > 0
    assert svc.last_refresh_datetime is not None


# ---------------------------------------------------------------------------
# DataService: computed caches bound to the sheets generation
# ---------------------------------------------------------------------------

class _GenStubSheets:
    """Minimal sheets stub carrying a controllable data_generation."""

    def __init__(self, generation=1):
        self.data_generation = generation

    def refresh_all_data(self):
        pass

    def __getattr__(self, name):
        return lambda *a, **k: pd.DataFrame()


def _data_service(generation=1):
    stub = _GenStubSheets(generation)
    return DataService(stub), stub


def test_computed_caches_survive_within_a_generation():
    ds, _stub = _data_service(generation=1)
    ds._games_calculated_cache["games_all"] = pd.DataFrame({"x": [1]})
    ds._leaderboard_cache["lb:points"] = ["p1"]
    ds._sync_with_sheets_generation()
    assert "games_all" in ds._games_calculated_cache
    assert "lb:points" in ds._leaderboard_cache
    assert ds._seen_generation == 1


def test_generation_bump_drops_all_computed_caches():
    ds, stub = _data_service(generation=1)
    ds._games_calculated_cache["games_all"] = pd.DataFrame({"x": [1]})
    ds._leaderboard_cache["lb:points"] = ["p1"]
    ds._sync_with_sheets_generation()

    stub.data_generation = 2  # raw snapshot reloaded
    ds._sync_with_sheets_generation()

    assert ds._games_calculated_cache == {}
    assert ds._leaderboard_cache == {}
    assert ds._seen_generation == 2


def test_leaderboard_entry_valid_until_generation_changes():
    ds, stub = _data_service(generation=1)
    ds._cache_leaderboard("lb:points", ["p1", "p2"])
    # Ancient timestamp: age alone must NOT invalidate anymore.
    ds._leaderboard_cache_time["lb:points"] = 0
    assert ds._get_cached_leaderboard("lb:points") == ["p1", "p2"]

    stub.data_generation = 2
    assert ds._get_cached_leaderboard("lb:points") is None


# ---------------------------------------------------------------------------
# AISummaryService: recap cache keyed by the game's data
# ---------------------------------------------------------------------------

def _digest(goals_for):
    return {
        "game": {
            "ID": "183",
            "Date": "2026-10-09",
            "Opponent": "Orillia Terriers",
            "GoalsFor": goals_for,
            "GoalsAgainst": 10,
            "Result": "L",
        },
        "is_completed": True,
        "special_teams": {"pp_pct": "0%", "pp_goals": 0, "pp_opportunities": 2,
                          "pp_shots_per_opp": 1.5, "pk_pct": "50%"},
        "possession": {"shots_for": 20, "shots_against": 35, "shot_share_pct": "36%"},
        "top_scorers": ["#9 Smith (1G)"],
    }


@pytest.fixture()
def ai_service(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return AISummaryService(cache_dir=str(tmp_path))


def test_recap_cached_for_unchanged_game(ai_service):
    text1 = ai_service.generate_summary(_digest(1), mode="coach")
    assert len(ai_service._cache) == 1
    key = next(iter(ai_service._cache))
    game_id, mode, fingerprint = key.split(":")
    assert (game_id, mode) == ("183", "coach")
    assert len(fingerprint) == 16

    text2 = ai_service.generate_summary(_digest(1), mode="coach")
    assert text2 == text1
    assert len(ai_service._cache) == 1  # cache hit, no regeneration


def test_corrected_game_regenerates_recap(ai_service):
    original = ai_service.generate_summary(_digest(1), mode="coach")
    corrected = ai_service.generate_summary(_digest(2), mode="coach")
    assert corrected != original
    assert "2-10" in corrected
    assert len(ai_service._cache) == 2  # old key orphaned, new one generated


def test_legacy_unfingerprinted_recap_is_never_served(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cache_file = tmp_path / "summaries_cache.json"
    cache_file.write_text('{"183:coach": "STALE RECAP FROM BEFORE THE FIX"}')
    svc = AISummaryService(cache_dir=str(tmp_path))
    text = svc.generate_summary(_digest(1), mode="coach")
    assert text != "STALE RECAP FROM BEFORE THE FIX"
    assert "1-10" in text
