"""Resilience tests for the 2026-10-19 portal outage fix.

Root cause of the outage: the Google service account is limited to 60
Sheets reads/minute. Both gunicorn workers construct their services at
startup; booting together they burst through the quota, init failed with
a 429, and app.py then skipped registering the dashboard/game/opponent
callbacks entirely - Dash cannot add callbacks later, so those workers
served empty pages forever (logins still worked, because the login
callback re-initialized the services, too late to matter).

These tests pin the two fixes:
1. Callback registration is unconditional and the services resolve lazily
   (ServiceRegistry + LazyService), so a poisoned start heals on use.
2. Sheets reads retry with backoff on 429 (SheetsService).
"""

import os
import subprocess
import sys

import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_WEBAPP = os.path.join(_HERE, "..", "hockey_stats_webapp")
sys.path.insert(0, os.path.abspath(_WEBAPP))
sys.path.insert(0, os.path.abspath(os.path.join(_WEBAPP, "services")))

import sheets_service as sheets_mod
from service_registry import LazyService, ServiceRegistry, ServiceUnavailableError
from sheets_service import SheetsService


# --------------------------------------------------------------------------
# ServiceRegistry
# --------------------------------------------------------------------------

class _FlakyFactory:
    def __init__(self, failures_before_success):
        self.failures = failures_before_success
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("init boom (429)")
        return ("sheets", "auth", "data")


def test_registry_recovers_after_failed_start():
    factory = _FlakyFactory(failures_before_success=1)
    reg = ServiceRegistry(factory, retry_interval=30)
    assert reg.ensure(force=True) is False
    assert reg.ready is False
    assert reg.data_service is None
    # A later attempt succeeds - the worker heals instead of staying poisoned.
    assert reg.ensure(force=True) is True
    assert reg.ready is True
    assert reg.data_service == "data"


def test_registry_throttles_retries():
    factory = _FlakyFactory(failures_before_success=99)
    reg = ServiceRegistry(factory, retry_interval=3600)
    assert reg.ensure() is False
    assert reg.ensure() is False
    # Throttled: the factory was NOT hammered by the second call.
    assert factory.calls == 1
    # ...but a forced attempt (e.g. from the login callback) always tries.
    assert reg.ensure(force=True) is False
    assert factory.calls == 2


def test_registry_ensure_is_idempotent_when_ready():
    factory = _FlakyFactory(failures_before_success=0)
    reg = ServiceRegistry(factory)
    assert reg.ensure() is True
    assert reg.ensure() is True
    assert factory.calls == 1


# --------------------------------------------------------------------------
# LazyService
# --------------------------------------------------------------------------

class _RealDataService:
    def get_players(self):
        return "players!"

    sheets_service = "sheets-attr"


def test_lazy_service_unavailable_before_init():
    reg = ServiceRegistry(_FlakyFactory(99), retry_interval=3600)
    proxy = LazyService(reg, "data_service")
    # Truthiness mirrors availability so `if not data_service:` guards in
    # the layouts render their graceful empty states.
    assert bool(proxy) is False
    with pytest.raises(ServiceUnavailableError):
        proxy.get_players()


def test_lazy_service_delegates_after_recovery():
    state = {"fail": True}

    def factory():
        if state["fail"]:
            raise RuntimeError("429")
        return ("sheets", "auth", _RealDataService())

    reg = ServiceRegistry(factory, retry_interval=0)
    proxy = LazyService(reg, "data_service")
    assert bool(proxy) is False
    state["fail"] = False
    # Access nudges a recovery attempt and then delegates.
    assert proxy.get_players() == "players!"
    assert proxy.sheets_service == "sheets-attr"
    assert bool(proxy) is True


# --------------------------------------------------------------------------
# SheetsService 429 retry
# --------------------------------------------------------------------------

class _Fake429Response:
    status_code = 429


class RateLimitError(Exception):
    """Duck-typed stand-in for gspread's APIError on a 429."""

    def __init__(self):
        super().__init__("{'code': 429, 'message': 'Quota exceeded'}")
        self.response = _Fake429Response()


class _FlakyWorksheet:
    def __init__(self, failures, records=None):
        self.failures = failures
        self.records = records if records is not None else [{"A": 1}]
        self.calls = 0

    def get_all_records(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise RateLimitError()
        return self.records


@pytest.fixture
def sleeps(monkeypatch):
    recorded = []
    monkeypatch.setattr(sheets_mod.time, "sleep", recorded.append)
    monkeypatch.setattr(sheets_mod.random, "uniform", lambda a, b: 0.0)
    monkeypatch.setattr(sheets_mod, "_RATE_LIMIT_DELAYS", (5, 7, 9))
    return recorded


def _bare_sheets():
    svc = SheetsService.__new__(SheetsService)
    svc.credentials_path = "unused"
    svc.sheet_id = "unused"
    svc.cache_ttl = 120
    svc.cache = {}
    svc.last_refresh = {}
    svc.data_epoch = None
    svc.data_generation = 0
    svc._refreshing_all = False
    return svc


def test_read_retries_with_backoff_then_succeeds(sleeps):
    svc = _bare_sheets()
    ws = _FlakyWorksheet(failures=2)
    out = svc._get_records(ws, "Games")
    assert out == [{"A": 1}]
    assert ws.calls == 3
    assert sleeps == [5, 7]  # the configured backoff schedule, in order


def test_read_gives_up_after_schedule(sleeps):
    svc = _bare_sheets()
    ws = _FlakyWorksheet(failures=99)
    with pytest.raises(RateLimitError):
        svc._get_records(ws, "Games")
    assert ws.calls == 4  # initial attempt + 3 retries
    assert sleeps == [5, 7, 9]


def test_non_429_errors_are_not_retried(sleeps):
    svc = _bare_sheets()

    class _Boom:
        def get_all_records(self):
            raise ValueError("some other failure")

    with pytest.raises(ValueError):
        svc._get_records(_Boom(), "Games")
    assert sleeps == []


def test_full_load_survives_a_429_per_tab(sleeps):
    """End-to-end: every tab 429s once during the coordinated reload and
    the snapshot still loads completely."""
    svc = _bare_sheets()
    game_rows = [{"ID": "1", "Date": "2026-01-01", "Opponent": "X",
                  "Location": "Y", "TeamID": "t1", "GameType": "R"}]
    event_rows = [{"ID": "9", "GameID": "1", "Team": "t1", "IsGoal": "FALSE"}]
    worksheets = {
        "Games": _FlakyWorksheet(1, game_rows),
        "Events": _FlakyWorksheet(1, event_rows),
        "Players": _FlakyWorksheet(1, [{"ID": "p1"}]),
        "GameRoster": _FlakyWorksheet(1, [{"GameID": "1"}]),
        "Teams": _FlakyWorksheet(1, [{"TeamID": "t1", "TeamName": "Team One",
                                     "Password": "t1"}]),
        "ParentCodes": _FlakyWorksheet(1, [{"Code": "c1"}]),
    }
    svc._get_worksheet = lambda name: worksheets[name]
    games = svc.get_games()
    assert len(games) == 1
    assert svc.data_epoch is not None
    assert worksheets["Games"].calls == 2


# --------------------------------------------------------------------------
# App wiring: a poisoned start still registers every callback
# --------------------------------------------------------------------------

def test_app_registers_all_callbacks_when_init_fails():
    """Import app.py with no Google credentials available (the poisoned
    worker scenario) and verify the dashboard/game/opponent callbacks are
    registered anyway."""
    webapp_dir = os.path.abspath(_WEBAPP)
    script = (
        "import app\n"
        "keys = sorted(app.app.callback_map.keys())\n"
        "print('INITIALIZED:', app.services_initialized)\n"
        "for k in keys:\n"
        "    print('CB:', k)\n"
    )
    env = dict(os.environ)
    env.pop("GOOGLE_CREDENTIALS", None)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=webapp_dir, env=env, capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert "INITIALIZED: False" in result.stdout
    for expected in ("dashboard-kpi-row", "game-list-container",
                     "opponent-selection-dropdown", "player-selected-store"):
        assert expected in result.stdout, f"{expected} callback not registered"
