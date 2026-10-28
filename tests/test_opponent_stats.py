"""Regression tests for the vs-Opponent page fixes (2026-10-28).

Three defects, all in the opponent statistics path:

1. Phantom goalie stats — get_opponent_goalie_stats derived GP/W/L/T from
   the game ROSTER (Status == 'Present'), so a dressed backup who never
   played was credited with the game's result; and a shutout was counted
   for any game where that goalie's own attributed GA was 0, so the backup
   collected a shutout even in a 6-goals-against loss. Live proof (Waxers
   vs South Simcoe, 1 game, 1-6 loss): the page credited #31 with
   GP 1, L, SO 1 on 0 shots faced while #72 faced all 47 shots.
2. Leaders-only player tables — get_opponent_player_leaderboard only
   included skaters with a nonzero stat line, so skaters who dressed but
   had a quiet game vanished.
3. Missing stats — the opponent player tables never got this season's
   on-ice shot share (SF / SA / SF%) or the player's own shots.

The fix derives goalie stats from who was actually in net (GoalieOnIceId
attribution, mirroring calculate_goalie_stats), with a legacy fallback for
games where GoalieOnIceId was never logged, and lists every dressed
skater with the full stat set.

Run:  python -m pytest tests/test_opponent_stats.py
(DataService is exercised with a stub sheets service and overridden data
accessors, so no Google credentials are needed.)
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hockey_stats_webapp"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hockey_stats_webapp", "services"))

from data_service import DataService  # noqa: E402

TEAM = "your_team"
OPP = "opponent"
OPPONENT_NAME = "South Simcoe Storm"


class _StubSheets:
    """Serves the fixture events/roster; anything else is an empty frame."""

    def __init__(self, events_df, roster_df):
        self._events_df = events_df
        self._roster_df = roster_df

    def refresh_all_data(self):
        pass

    def get_events(self, force_refresh=False):
        return self._events_df

    def get_game_roster(self):
        return self._roster_df

    def __getattr__(self, name):
        return lambda *a, **k: pd.DataFrame()


class _OppService(DataService):
    """DataService with opponent games/players replaced by fixtures."""

    def __init__(self, games_df, players_df, events_df, roster_df):
        super().__init__(_StubSheets(events_df, roster_df))
        self._games_df = games_df
        self._players_df = players_df

    def get_opponent_games(self, opponent_name, team_id=None, game_type=None):
        return self._games_df

    def get_players(self, team_id=None):
        return self._players_df

    def _get_team_identifier_for_events(self, team_id):
        return TEAM


# ------------------------------------------------------------- fixtures ---

def _games(result="L", game_id="g1"):
    return pd.DataFrame([{
        "ID": game_id, "Opponent": OPPONENT_NAME, "Result": result,
        "Date": "2026-01-10", "TeamID": TEAM,
    }])


def _players(*rows):
    """Rows are (player_id, position, jersey_number)."""
    return pd.DataFrame([
        {"ID": pid, "Position": pos, "JerseyNumber": jersey, "TeamID": TEAM}
        for pid, pos, jersey in rows
    ])


def _roster(*rows):
    """Rows are (game_id, player_id, status)."""
    return pd.DataFrame(
        [{"GameID": g, "PlayerID": p, "Status": s} for g, p, s in rows],
        columns=["GameID", "PlayerID", "Status"],
    )


def _event(game, team, event_type="Shot", *, goal=False, primary="", a1="",
           a2="", goalie=None, on_ice="", sit="", ptype="", pdur=0):
    return {
        "GameID": game, "Period": 1, "EventType": event_type, "Team": team,
        "PrimaryPlayerID": primary, "AssistPlayer1ID": a1, "AssistPlayer2ID": a2,
        "IsGoal": goal, "GoalSituation": sit, "PenaltyType": ptype,
        "PenaltyDuration": pdur, "YourTeamPlayersOnIce": on_ice,
        "GoalieOnIceId": goalie, "IsPenaltyShot": False,
    }


def _opp_shots(game, goalie, count, goals=0):
    """`count` opponent shots on `goalie`, the first `goals` of them goals."""
    return [
        _event(game, OPP, goal= i < goals, goalie=goalie)
        for i in range(count)
    ]


def _by_id(stats_list):
    return {s["player"]["ID"]: s for s in stats_list}


# -------------------------------------------------------------- goalies ---

def test_dressed_backup_gets_no_phantom_line():
    """The South Simcoe case: #72 faced 47 shots (6 GA) in a loss; #31 was
    roster-Present but never played. Only #72 may appear."""
    players = _players(("g72", "G", 72), ("g31", "G", 31))
    roster = _roster(("g1", "g72", "Present"), ("g1", "g31", "Present"))
    events = pd.DataFrame(_opp_shots("g1", "g72", 47, goals=6))

    stats = _by_id(_OppService(_games("L"), players, events, roster)
                   .get_opponent_goalie_stats(OPPONENT_NAME, TEAM))

    assert set(stats) == {"g72"}  # backup absent entirely — no GP, no SO
    line = stats["g72"]
    assert line["games_played"] == 1
    assert line["losses"] == 1 and line["wins"] == 0 and line["ties"] == 0
    assert line["shots_against"] == 47
    assert line["goals_against"] == 6
    assert line["saves"] == 41
    assert line["save_percentage"] == pytest.approx(41 / 47)
    assert line["gaa"] == pytest.approx(6.0)
    assert line["shutouts"] == 0


def test_true_shutout_preserved():
    """Sole goalie, team allows nothing: the shutout is real and stays."""
    players = _players(("g72", "G", 72), ("g31", "G", 31))
    roster = _roster(("g1", "g72", "Present"))  # backup not rostered
    events = pd.DataFrame(_opp_shots("g1", "g72", 10, goals=0))

    stats = _by_id(_OppService(_games("W"), players, events, roster)
                   .get_opponent_goalie_stats(OPPONENT_NAME, TEAM))

    assert set(stats) == {"g72"}
    assert stats["g72"]["shutouts"] == 1
    assert stats["g72"]["wins"] == 1
    assert stats["g72"]["save_percentage"] == pytest.approx(1.0)


def test_split_game_no_shutout_for_either():
    """Both goalies play, team allows nothing: both get the GP and the win,
    but a split game is nobody's shutout."""
    players = _players(("g72", "G", 72), ("g31", "G", 31))
    roster = _roster(("g1", "g72", "Present"), ("g1", "g31", "Present"))
    events = pd.DataFrame(
        _opp_shots("g1", "g72", 5, goals=0) + _opp_shots("g1", "g31", 5, goals=0)
    )

    stats = _by_id(_OppService(_games("W"), players, events, roster)
                   .get_opponent_goalie_stats(OPPONENT_NAME, TEAM))

    assert set(stats) == {"g72", "g31"}
    for gid in ("g72", "g31"):
        assert stats[gid]["games_played"] == 1
        assert stats[gid]["wins"] == 1
        assert stats[gid]["shutouts"] == 0


def test_legacy_game_single_present_goalie_credited():
    """Old game with GoalieOnIceId never logged: the one rostered goalie
    gets the game and all of its events."""
    players = _players(("g72", "G", 72), ("g31", "G", 31))
    roster = _roster(("g1", "g72", "Present"))  # only one goalie rostered
    events = pd.DataFrame([
        _event("g1", OPP, goalie=None) for _ in range(6)
    ] + [
        _event("g1", OPP, goal=True, goalie=None) for _ in range(2)
    ])

    stats = _by_id(_OppService(_games("L"), players, events, roster)
                   .get_opponent_goalie_stats(OPPONENT_NAME, TEAM))

    assert set(stats) == {"g72"}
    line = stats["g72"]
    assert line["games_played"] == 1
    assert line["losses"] == 1
    assert line["shots_against"] == 8
    assert line["goals_against"] == 2
    assert line["gaa"] == pytest.approx(2.0)
    assert line["shutouts"] == 0


def test_legacy_game_two_present_goalies_credits_neither():
    """No attribution and two dressed goalies: honest blank beats a
    fabricated line for either of them."""
    players = _players(("g72", "G", 72), ("g31", "G", 31))
    roster = _roster(("g1", "g72", "Present"), ("g1", "g31", "Present"))
    events = pd.DataFrame([_event("g1", OPP, goalie=None) for _ in range(5)])

    stats = _OppService(_games("L"), players, events, roster) \
        .get_opponent_goalie_stats(OPPONENT_NAME, TEAM)

    assert stats == []


def test_blank_goalie_events_not_shared_by_all_goalies():
    """A blank-GoalieOnIceId event in an attributed game belongs to no one:
    it must not inflate the other goalie's shots against."""
    players = _players(("g72", "G", 72), ("g31", "G", 31))
    roster = _roster(("g1", "g72", "Present"), ("g1", "g31", "Present"))
    events = pd.DataFrame(
        _opp_shots("g1", "g72", 4, goals=0)
        + _opp_shots("g1", "g31", 3, goals=0)
        + [_event("g1", OPP, goalie="")]  # unattributed opponent shot
    )

    stats = _by_id(_OppService(_games("W"), players, events, roster)
                   .get_opponent_goalie_stats(OPPONENT_NAME, TEAM))

    assert stats["g72"]["shots_against"] == 4
    assert stats["g31"]["shots_against"] == 3


# -------------------------------------------------------------- skaters ---

def _skater_fixture():
    players = _players(
        ("f1", "F", 10), ("f2", "F", 11), ("f3", "F", 12), ("f4", "F", 13),
        ("d1", "D", 44), ("g72", "G", 72),
    )
    # f4 deliberately missing from the roster (roster gap) but scores.
    roster = _roster(
        ("g1", "f1", "Present"), ("g1", "f2", "Present"),
        ("g1", "f3", "Present"), ("g1", "d1", "Present"),
        ("g1", "g72", "Present"),
    )
    events = pd.DataFrame([
        # f1 scores, d1 assists; f2 also on ice
        _event("g1", TEAM, goal=True, primary="f1", a1="d1", goalie="g72",
               on_ice="f1,d1,f2"),
        # f1 shoots again
        _event("g1", TEAM, primary="f1", goalie="g72", on_ice="f1,f2,d1"),
        # two opponent shots with the same unit on ice
        _event("g1", OPP, goalie="g72", on_ice="f1,f2,d1"),
        _event("g1", OPP, goalie="g72", on_ice="f2,d1"),
        # f4 (not on the roster) scores
        _event("g1", TEAM, goal=True, primary="f4", goalie="g72", on_ice="f4"),
        # f2 takes a penalty
        _event("g1", TEAM, "Penalty", primary="f2", ptype="Tripping", pdur=2),
    ])
    return players, roster, events


def test_dressed_skater_with_zero_line_is_listed():
    """f3 dressed and did nothing at all — he still belongs in the table,
    with a full (zero) stat set including the Corsi fields."""
    players, roster, events = _skater_fixture()
    svc = _OppService(_games("W"), players, events, roster)

    forwards = _by_id(svc.get_opponent_player_leaderboard(
        OPPONENT_NAME, TEAM, position="F", limit=None))

    assert "f3" in forwards
    line = forwards["f3"]
    assert line["goals"] == 0 and line["assists"] == 0 and line["points"] == 0
    assert line["plus_minus"] == 0 and line["penalty_minutes"] == 0
    assert line["shots"] == 0
    assert line["on_ice_shots_for"] == 0
    assert line["on_ice_shots_against"] == 0
    assert line["on_ice_shot_share_pct"] == 0.0


def test_roster_gap_skater_with_stats_is_listed():
    """f4 has no roster row but scored — involvement in the events is
    enough to be listed."""
    players, roster, events = _skater_fixture()
    svc = _OppService(_games("W"), players, events, roster)

    forwards = _by_id(svc.get_opponent_player_leaderboard(
        OPPONENT_NAME, TEAM, position="F", limit=None))

    assert forwards["f4"]["goals"] == 1
    assert forwards["f4"]["points"] == 1


def test_skater_corsi_and_shots_values():
    """On-ice shot share comes from the same exact-membership computation
    as calculate_player_stats."""
    players, roster, events = _skater_fixture()
    svc = _OppService(_games("W"), players, events, roster)

    forwards = _by_id(svc.get_opponent_player_leaderboard(
        OPPONENT_NAME, TEAM, position="F", limit=None))
    defense = _by_id(svc.get_opponent_player_leaderboard(
        OPPONENT_NAME, TEAM, position="D", limit=None))

    # f1: own shots = goal + shot = 2; on ice for 2 SF and 1 SA
    assert forwards["f1"]["goals"] == 1
    assert forwards["f1"]["shots"] == 2
    assert forwards["f1"]["on_ice_shots_for"] == 2
    assert forwards["f1"]["on_ice_shots_against"] == 1
    assert forwards["f1"]["on_ice_shot_share_pct"] == pytest.approx(66.7)

    # f2: quiet offensively (PIM 2) but on ice both ways: 2 SF, 2 SA
    assert forwards["f2"]["penalty_minutes"] == 2
    assert forwards["f2"]["on_ice_shots_for"] == 2
    assert forwards["f2"]["on_ice_shots_against"] == 2
    assert forwards["f2"]["on_ice_shot_share_pct"] == pytest.approx(50.0)

    # d1: the assist, on ice for everything f1 was
    assert defense["d1"]["assists"] == 1
    assert defense["d1"]["on_ice_shots_for"] == 2
    assert defense["d1"]["on_ice_shots_against"] == 2


def test_no_limit_returns_full_roster():
    """limit=None means no cap: all four forwards come back."""
    players, roster, events = _skater_fixture()
    svc = _OppService(_games("W"), players, events, roster)

    forwards = svc.get_opponent_player_leaderboard(
        OPPONENT_NAME, TEAM, position="F", limit=None)

    assert {s["player"]["ID"] for s in forwards} == {"f1", "f2", "f3", "f4"}
