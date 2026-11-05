"""Tests for the Last N games filter (2026-11-05).

The historical failure mode for this feature is a surface silently
ignoring the filter, so the acceptance tests assert hand-computed
WINDOW values (on a fixture where Last-2 differs from All), never just
"the numbers changed".

Canonical window (services/data_service.py, _select_last_n_game_ids):
the N most recent COMPLETED games — the viewer's existing definition:
date on/before today AND stats recorded — with Exhibition games
excluded, ordered by parsed date DESC with game ID DESC as the
within-day tiebreak (doubleheaders).

Run:  python -m pytest tests/test_last_n_games.py
(DataService is exercised with stub sheets services and fixture frames,
so no Google credentials are needed.)
"""

import os
import sys
from datetime import date, timedelta

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hockey_stats_webapp"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hockey_stats_webapp", "services"))

from data_service import DataService  # noqa: E402
from components.last_n_filter import (  # noqa: E402
    normalize_last_n_choice, last_n_window_label,
)

TEAM = "your_team"
OPP = "opponent"


def _d(days_ago):
    return (date.today() - timedelta(days=days_ago)).isoformat()


def _f(days_ahead):
    return (date.today() + timedelta(days=days_ahead)).isoformat()


# ------------------------------------------------------------ stubbing ---

class _StubSheets:
    """Serves fixture events/roster; anything else is an empty frame.

    data_generation is a stable 1, as in production between reloads, so
    the generation-bound computed caches behave realistically (a stub
    without it makes every read look like a new snapshot).
    """

    def __init__(self, events_df=None, roster_df=None, games_df=None, players_df=None):
        self._events_df = events_df if events_df is not None else pd.DataFrame()
        self._roster_df = roster_df if roster_df is not None else pd.DataFrame()
        self._games_df = games_df if games_df is not None else pd.DataFrame()
        self._players_df = players_df if players_df is not None else pd.DataFrame()
        self.cache = {}
        self.data_generation = 1
        self.last_refresh_datetime = None

    def refresh_all_data(self):
        pass

    def get_events(self, force_refresh=False):
        return self._events_df

    def get_game_roster(self):
        return self._roster_df

    def get_games(self):
        return self._games_df

    def get_players(self):
        return self._players_df

    def __getattr__(self, name):
        return lambda *a, **k: pd.DataFrame()


class _FixtureService(DataService):
    """DataService whose get_games is replaced by the acceptance fixture.

    The stub get_games honours the same contract as the real one
    (team/type filtering, non-Exhibition by default, window applied via
    the canonical selector); the REAL get_games is exercised separately
    in the cache tests below.
    """

    def __init__(self, games_df, players_df, events_df, roster_df):
        super().__init__(_StubSheets(events_df, roster_df))
        self._games_df = games_df
        self._players_df = players_df

    def get_games(self, team_id=None, game_type=None, last_n=None):
        games = self._games_df
        if team_id:
            games = games[games["TeamID"] == team_id]
        if game_type:
            games = games[games["GameType"] == game_type]
        else:
            games = games[games["GameType"] != "E"]
        if last_n is not None:
            ids = self._select_last_n_game_ids(games, last_n)
            games = games[games["ID"].isin(ids)]
        return games.copy()

    def get_players(self, team_id=None):
        return self._players_df

    def _get_team_identifier_for_events(self, team_id):
        return TEAM


class _RealGamesService(DataService):
    """DataService with the REAL get_games (sheets stub feeds raw rows)."""

    def __init__(self, games_df, players_df, events_df, roster_df):
        super().__init__(_StubSheets(events_df, roster_df, games_df, players_df))

    def _get_team_identifier_for_events(self, team_id):
        return TEAM


class _BareService(DataService):
    """Minimal service for selector-only tests (frames passed directly)."""

    def __init__(self):
        super().__init__(_StubSheets())

    def _get_team_identifier_for_events(self, team_id):
        return TEAM


# ------------------------------------------------- acceptance fixture ----
# Four completed games. Last-2 window = {g3, g4}.
#   g1 (R, oldest):  W 3-1. p10 2G. ST: PP opp (no goal), PK opp (PP goal
#                    against — that is g1's only goal against).
#   g2 (R):          W 2-0. p19 2G, one assisted by p10. Goalie shutout.
#   g3 (T):          L 2-3. p10 1G, p19 1G assisted by p10.
#   g4 (R, newest):  W 4-2. p10 3G (first a PP goal), p19 1G. PP opp used.
# Goalie p30 faces 10/8/12/5 shots with 1/0/3/2 goals against.

def _ev(game, team, etype="Shot", *, goal=False, primary="", a1="", sit="",
        goalie=None, ptype=""):
    return {
        "EventID": f"{game}-{team}-{etype}-{primary}-{goal}-{sit}-{abs(hash((game, primary, sit, goal))) % 997}",
        "GameID": game, "Period": 1, "EventType": etype, "Team": team,
        "PrimaryPlayerID": primary, "PrimaryPlayerId": primary,
        "AssistPlayer1ID": a1, "AssistPlayer2ID": "",
        "IsGoal": goal, "GoalSituation": sit, "PenaltyType": ptype,
        "PenaltyDuration": 2 if etype == "Penalty" else 0,
        "YourTeamPlayersOnIce": "", "OpponentPlayersOnIce": "",
        "GoalieOnIceId": goalie, "IsPenaltyShot": False,
    }


def _acceptance():
    games = pd.DataFrame([
        {"ID": "g1", "TeamID": TEAM, "Date": _d(56), "GameType": "R", "Opponent": "A",
         "GoalsFor": 3, "GoalsAgainst": 1, "Result": "W"},
        {"ID": "g2", "TeamID": TEAM, "Date": _d(46), "GameType": "R", "Opponent": "B",
         "GoalsFor": 2, "GoalsAgainst": 0, "Result": "W"},
        {"ID": "g3", "TeamID": TEAM, "Date": _d(39), "GameType": "T", "Opponent": "C",
         "GoalsFor": 2, "GoalsAgainst": 3, "Result": "L"},
        {"ID": "g4", "TeamID": TEAM, "Date": _d(33), "GameType": "R", "Opponent": "D",
         "GoalsFor": 4, "GoalsAgainst": 2, "Result": "W"},
    ])
    players = pd.DataFrame([
        {"ID": "p10", "Position": "F", "JerseyNumber": 10, "TeamID": TEAM,
         "FirstName": "Sam", "LastName": "Ten"},
        {"ID": "p19", "Position": "F", "JerseyNumber": 19, "TeamID": TEAM,
         "FirstName": "Pat", "LastName": "Nine"},
        {"ID": "p30", "Position": "G", "JerseyNumber": 30, "TeamID": TEAM,
         "FirstName": "Gail", "LastName": "Net"},
    ])
    roster = pd.DataFrame(
        [{"GameID": g, "PlayerID": p, "Status": "Present"}
         for g in ("g1", "g2", "g3", "g4") for p in ("p10", "p19", "p30")],
        columns=["GameID", "PlayerID", "Status"],
    )
    rows = []
    rows += [_ev("g1", TEAM, goal=True, primary="p10"),
             _ev("g1", TEAM, goal=True, primary="p10"),
             _ev("g1", TEAM, goal=True, primary="p19")]
    rows += [_ev("g1", OPP, goal=True, sit="Penalty Kill", goalie="p30")]
    rows += [_ev("g1", OPP, goalie="p30") for _ in range(9)]
    rows += [_ev("g1", OPP, "Penalty", primary="opp9", ptype="Tripping")]
    rows += [_ev("g1", TEAM, primary="p10", sit="Power Play")]
    rows += [_ev("g1", TEAM, "Penalty", primary="p10", ptype="Tripping")]
    rows += [_ev("g2", TEAM, goal=True, primary="p19", a1="p10"),
             _ev("g2", TEAM, goal=True, primary="p19")]
    rows += [_ev("g2", OPP, goalie="p30") for _ in range(8)]
    rows += [_ev("g3", TEAM, goal=True, primary="p10"),
             _ev("g3", TEAM, goal=True, primary="p19", a1="p10")]
    rows += [_ev("g3", OPP, goal=True, goalie="p30") for _ in range(3)]
    rows += [_ev("g3", OPP, goalie="p30") for _ in range(9)]
    rows += [_ev("g4", OPP, "Penalty", primary="opp9", ptype="Tripping")]
    rows += [_ev("g4", TEAM, goal=True, primary="p10", sit="Power Play"),
             _ev("g4", TEAM, goal=True, primary="p10"),
             _ev("g4", TEAM, goal=True, primary="p10"),
             _ev("g4", TEAM, goal=True, primary="p19")]
    rows += [_ev("g4", OPP, goal=True, goalie="p30") for _ in range(2)]
    rows += [_ev("g4", OPP, goalie="p30") for _ in range(3)]
    events = pd.DataFrame(rows)
    events["IsGoal"] = events["IsGoal"].astype(bool)
    return games, players, events, roster


@pytest.fixture()
def svc():
    games, players, events, roster = _acceptance()
    return _FixtureService(games, players, events, roster)


# --------------------------------------------------------- selector ------

def _grow(gid, date_str, gtype="R", gf=2, ga=1):
    return {"ID": gid, "TeamID": TEAM, "Date": date_str, "GameType": gtype,
            "Opponent": "X", "GoalsFor": gf, "GoalsAgainst": ga}


def test_selector_future_fixtures_never_selected():
    """The U13 Select trap from the 2026-11-05 data audit: the team's five
    most recent sheet rows by date are UNPLAYED future fixtures; it has
    only 3 completed games. Last 5 must return exactly those 3, newest
    first — a naive date-sort + head(5) returns the fixtures instead."""
    bare = _BareService()
    rows = [_grow(166, _d(60)), _grow(171, _d(50)), _grow(189, _d(40))]
    rows += [_grow(gid, _f(ahead), gf=0, ga=0)
             for gid, ahead in [(172, 2), (181, 9), (182, 16), (190, 23), (191, 44)]]
    games = pd.DataFrame(rows)
    assert bare._select_last_n_game_ids(games, 5) == [189, 171, 166]
    # The Recent Games page's own count range (2-10) is equally safe.
    assert bare._select_last_n_game_ids(games, 10) == [189, 171, 166]


def test_selector_exhibition_excluded_window_reaches_past_it():
    bare = _BareService()
    games = pd.DataFrame([
        _grow(1, _d(30)), _grow(2, _d(20), gtype="E"), _grow(3, _d(10)),
    ])
    # The Exhibition is the middle game by date; Last 2 skips it and
    # reaches back to game 1.
    assert bare._select_last_n_game_ids(games, 2) == [3, 1]


def test_selector_same_day_doubleheader_id_tiebreak():
    bare = _BareService()
    games = pd.DataFrame([
        _grow(50, _d(10)), _grow(51, _d(10)), _grow(49, _d(20)),
    ])
    assert bare._select_last_n_game_ids(games, 2) == [51, 50]


def test_selector_date_wins_over_id_inversion():
    bare = _BareService()
    games = pd.DataFrame([_grow(99, _d(30)), _grow(3, _d(5))])
    assert bare._select_last_n_game_ids(games, 2) == [3, 99]


def test_selector_fewer_than_n_returns_all_completed():
    bare = _BareService()
    games = pd.DataFrame([_grow(7, _d(9)), _grow(8, _d(3))])
    assert bare._select_last_n_game_ids(games, 5) == [8, 7]


def test_selector_none_means_no_restriction():
    bare = _BareService()
    games = pd.DataFrame([_grow(7, _d(9)), _grow(8, _d(3))])
    assert bare._select_last_n_game_ids(games, None) is None
    frame = bare.get_last_n_games_frame(games, None)
    assert frame["ID"].tolist() == [8, 7]


def test_normalize_last_n_clamps_and_defaults():
    assert DataService._normalize_last_n(None) is None
    assert DataService._normalize_last_n(0) == 1
    assert DataService._normalize_last_n(99) == 30
    assert DataService._normalize_last_n("abc") is None
    assert DataService._normalize_last_n("5") == 5


# ------------------------------------------------------- acceptance ------

def test_team_stats_window_values(svc):
    all_stats = svc.calculate_team_stats(TEAM)
    assert (all_stats["games_played"], all_stats["wins"], all_stats["losses"],
            all_stats["goals_for"], all_stats["goals_against"]) == (4, 3, 1, 11, 6)
    win = svc.calculate_team_stats(TEAM, last_n=2)
    assert (win["games_played"], win["wins"], win["losses"],
            win["goals_for"], win["goals_against"]) == (2, 1, 1, 6, 5)


def test_team_stats_by_game_type_parts_sum_to_windowed_headline(svc):
    by_type = svc.calculate_team_stats_by_game_type(TEAM, last_n=2)
    assert (by_type["R"]["games_played"], by_type["R"]["goals_for"],
            by_type["R"]["goals_against"]) == (1, 4, 2)
    assert (by_type["T"]["games_played"], by_type["T"]["goals_for"],
            by_type["T"]["goals_against"]) == (1, 2, 3)
    assert by_type["P"]["games_played"] == 0
    parts_gp = sum(by_type[c]["games_played"] for c in ("R", "T", "P"))
    parts_gf = sum(by_type[c]["goals_for"] for c in ("R", "T", "P"))
    assert parts_gp == by_type["ALL"]["games_played"] == 2
    assert parts_gf == by_type["ALL"]["goals_for"] == 6


def test_special_teams_window_values(svc):
    st_all = svc.calculate_special_teams_stats(TEAM)
    assert (st_all["pp_opportunities"], st_all["pp_goals"]) == (2, 1)
    assert st_all["pp_percentage"] == pytest.approx(50.0)
    assert (st_all["pk_opportunities"], st_all["pk_goals_conceded"]) == (1, 1)
    st = svc.calculate_special_teams_stats(TEAM, last_n=2)
    assert (st["pp_opportunities"], st["pp_goals"]) == (1, 1)
    assert st["pp_percentage"] == pytest.approx(100.0)
    assert st["pk_opportunities"] == 0


def test_special_teams_by_game_type_window_buckets(svc):
    by_type = svc.calculate_special_teams_stats_by_game_type(TEAM, last_n=2)
    # Window = {g3 (T), g4 (R)}: only g4 carries a power play.
    assert (by_type["R"]["pp_opportunities"], by_type["R"]["pp_goals"]) == (1, 1)
    assert by_type["T"]["pp_opportunities"] == 0
    unwindowed = svc.calculate_special_teams_stats_by_game_type(TEAM)
    assert unwindowed["R"]["pp_opportunities"] == 2


def test_player_stats_window_values(svc):
    all_stats = svc.calculate_player_stats("p10", TEAM)
    assert (all_stats["games_played"], all_stats["goals"],
            all_stats["assists"], all_stats["points"]) == (4, 6, 2, 8)
    win = svc.calculate_player_stats("p10", TEAM, last_n=2)
    assert (win["games_played"], win["goals"],
            win["assists"], win["points"]) == (2, 4, 1, 5)


def test_goalie_stats_window_values(svc):
    all_stats = svc.calculate_goalie_stats("p30", TEAM)
    assert (all_stats["games_played"], all_stats["wins"], all_stats["losses"],
            all_stats["shutouts"]) == (4, 3, 1, 1)
    assert (all_stats["shots_against"], all_stats["goals_against"],
            all_stats["saves"]) == (35, 6, 29)
    assert all_stats["save_percentage"] == pytest.approx(29 / 35)
    assert all_stats["gaa"] == pytest.approx(1.5)
    win = svc.calculate_goalie_stats("p30", TEAM, last_n=2)
    assert (win["games_played"], win["wins"], win["losses"],
            win["shutouts"]) == (2, 1, 1, 0)
    assert (win["shots_against"], win["goals_against"], win["saves"]) == (17, 5, 12)
    assert win["save_percentage"] == pytest.approx(12 / 17)
    assert win["gaa"] == pytest.approx(2.5)


def test_leaderboard_window_values(svc):
    def points_by_player(board):
        return {e["player"].get("ID"): e["points"] for e in board}

    assert points_by_player(svc.get_team_leaderboard(stat="points", team_id=TEAM)) == \
        {"p10": 8, "p19": 5, "p30": 0}
    assert points_by_player(svc.get_team_leaderboard(stat="points", team_id=TEAM, last_n=2)) == \
        {"p10": 5, "p19": 2, "p30": 0}


def test_player_game_log_windowed(svc):
    log = svc.get_player_game_log("p10", TEAM, last_n=2)
    assert [e["game"]["ID"] for e in log] == ["g4", "g3"]


# ------------------------------------------------------------ caches -----

def test_leaderboard_cache_isolation_interleaved(svc):
    """All / Last-5 / All must each return their own variant's numbers:
    the window is part of the leaderboard cache key."""
    def p10_points(**kw):
        board = svc.get_team_leaderboard(stat="points", team_id=TEAM, **kw)
        return {e["player"].get("ID"): e["points"] for e in board}["p10"]

    assert p10_points() == 8
    assert p10_points(last_n=2) == 5
    assert p10_points() == 8
    assert svc._get_leaderboard_cache_key("points", None, TEAM, None, None) != \
        svc._get_leaderboard_cache_key("points", None, TEAM, None, 2)


def test_get_games_cache_keys_include_last_n():
    """The REAL get_games: windowed frames cache under their own key and
    never contaminate the full frame (or vice versa)."""
    games, players, events, roster = _acceptance()
    raw = games.drop(columns=["GoalsFor", "GoalsAgainst", "Result"])
    real = _RealGamesService(raw, players, events, roster)

    full = real.get_games(TEAM)
    assert sorted(full["ID"].tolist()) == ["g1", "g2", "g3", "g4"]
    win = real.get_games(TEAM, last_n=2)
    assert sorted(win["ID"].tolist()) == ["g3", "g4"]
    full_again = real.get_games(TEAM)
    assert sorted(full_again["ID"].tolist()) == ["g1", "g2", "g3", "g4"]
    keys = set(real._games_calculated_cache.keys())
    assert "games_your_team_None" in keys
    assert "games_your_team_None_last2" in keys


# --------------------------------------------------------- UI helpers ----

def test_normalize_last_n_choice_presets_and_custom():
    assert normalize_last_n_choice("all", None) is None
    assert normalize_last_n_choice(None, None) is None
    assert normalize_last_n_choice("2", None) == 2
    assert normalize_last_n_choice("10", None) == 10
    assert normalize_last_n_choice("custom", 7) == 7
    assert normalize_last_n_choice("custom", None) is None
    assert normalize_last_n_choice("custom", 0) == 1
    assert normalize_last_n_choice("custom", 45) == 30


def test_last_n_window_label_actual_count():
    assert last_n_window_label(None) == ""
    assert last_n_window_label(5) == "Last 5 Games"
    assert last_n_window_label(5, actual=5) == "Last 5 Games"
    assert last_n_window_label(5, actual=3) == "Last 5 Games (only 3 played)"


# ------------------------------------------------------ recent games -----

def test_recent_games_layout_uses_canonical_selector():
    """The Recent Games page used to carry its own sort-by-date + head(N)
    selection in both callbacks (no within-day tiebreak). It must select
    through the canonical selector now. (The page is currently unrouted
    and unimportable for an unrelated pre-existing reason — a missing
    game-type-filter factory — so this is a source-level guard.)"""
    path = os.path.join(os.path.dirname(__file__), "..",
                        "hockey_stats_webapp", "layouts", "recent_games_layout.py")
    with open(path, encoding="utf-8") as f:
        source = f.read()
    assert "DateSortable" not in source
    assert source.count("get_last_n_games_frame") == 2
