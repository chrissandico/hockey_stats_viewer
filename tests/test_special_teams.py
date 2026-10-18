"""Regression tests for the GoalSituation perspective fix (2026-10-18).

Canonical definition (WEB_APP_STATS_SPEC.md in hockey_stats_app, Column K):
GoalSituation records OUR team's manpower state at the event, whoever scored:
  'Power Play'   = WE have the advantage  (opponent goal under it = SH goal against)
  'Penalty Kill' = WE are short-handed    (opponent goal under it = PP goal allowed)
  'Even Strength' / '' = equal skaters / not recorded (counts as even strength)

The same two fixtures exist in the Flutter app's test suite
(test/special_teams_test.dart) and must produce identical numbers.

Run:  python -m pytest tests/test_special_teams.py
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


class _StubSheets:
    """Any accessor returns an empty DataFrame; refresh calls are no-ops."""

    def refresh_all_data(self):
        pass

    def __getattr__(self, name):
        return lambda *a, **k: pd.DataFrame()


class _TestService(DataService):
    """DataService with data plumbing replaced by fixtures."""

    def __init__(self, events_df, game=None):
        super().__init__(_StubSheets())
        self._events_df = events_df
        self._game = game or {"ID": "g1", "TeamID": TEAM, "GoalsFor": 0, "GoalsAgainst": 0}

    def get_events(self):
        return self._events_df

    def get_game_by_id(self, game_id, team_id=None):
        return self._game

    def _get_team_identifier_for_events(self, team_id):
        return team_id


def _row(event_type, team, *, goal=False, sit="", player="x", ptype="", pdur=0,
         on_ice="", game="g1", period=1):
    return {
        "EventID": f"e{id(object())}",
        "GameID": game,
        "Period": period,
        "EventType": event_type,
        "Team": team,
        "PrimaryPlayerId": player,
        "IsGoal": goal,
        "GoalSituation": sit,
        "PenaltyType": ptype,
        "PenaltyDuration": pdur,
        "YourTeamPlayersOnIce": on_ice,
        "OpponentPlayersOnIce": "",
        "IsPenaltyShot": False,
    }


def _pen(team, **kw):
    return _row("Penalty", team, ptype="Tripping", pdur=2, **kw)


def _goal(team, sit, **kw):
    return _row("Shot", team, goal=True, sit=sit, **kw)


def _shot(team, sit, **kw):
    return _row("Shot", team, goal=False, sit=sit, **kw)


def canonical_game():
    """Fixture 1: PP goal + PP shot, SH goal against, 2 PK opps (1 synthetic),
    PP goal allowed, SH goal for, ES goal against."""
    return pd.DataFrame([
        _pen(OPP, player="opp9"),                                            # PP opp
        _goal(TEAM, "Power Play", on_ice="p88,p19"),                         # our PP goal
        _shot(TEAM, "Power Play"),                                           # our PP shot
        _goal(OPP, "Power Play", on_ice="p88,p19"),                          # their SH goal
        _row("Penalty", TEAM, player="", ptype="Unspecified", pdur=2),       # synthetic PK opp
        _pen(TEAM, player="p88"),                                            # real PK opp
        _goal(OPP, "Penalty Kill", on_ice="p88,p19"),                        # their PP goal
        _goal(TEAM, "Penalty Kill", on_ice="p88"),                           # our SH goal
        _goal(OPP, "Even Strength", on_ice="p88,p19"),                       # their ES goal
    ])


def phil_game():
    """Fixture 2: Phil's game (Waxers vs Orillia) logged under the canonical
    definition: PP 1/2, four kills, two PP goals allowed, one SH goal against."""
    rows = [_pen(OPP, player="opp1"), _pen(OPP, player="opp2"),
            _goal(TEAM, "Power Play")]
    rows += [_pen(TEAM, player=f"p{i}") for i in range(4)]
    rows += [_goal(OPP, "Penalty Kill"), _goal(OPP, "Penalty Kill"),
             _goal(OPP, "Power Play")]  # last one is their SH goal
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- summary ---

def test_fixture1_summary_matches_hockey_truth():
    svc = _TestService(canonical_game())
    s = svc._special_teams_summary_from_events(canonical_game(), TEAM)
    assert s["pp_goals"] == 1
    assert s["pp_opportunities"] == 1
    assert s["pp_percentage"] == 100.0
    assert s["pp_shots"] == 2
    assert s["pk_opportunities"] == 2
    assert s["pk_goals_conceded"] == 1        # only their PP goal
    assert s["pk_percentage"] == 50.0
    assert s["pk_shots_allowed"] == 1
    assert s["sh_goals_for"] == 1
    assert s["sh_goals_against"] == 1         # NOT folded into PK conceded
    assert s["net_special_teams_goals"] == 0
    assert s["combined_st_index"] == 150.0


def test_fixture2_phil_game():
    s = _TestService(phil_game())._special_teams_summary_from_events(phil_game(), TEAM)
    assert s["pp_goals"] == 1
    assert s["pp_opportunities"] == 2
    assert s["pp_percentage"] == 50.0
    assert s["pk_opportunities"] == 4
    assert s["pk_goals_conceded"] == 2
    assert s["pk_percentage"] == 50.0
    assert s["sh_goals_against"] == 1
    assert s["net_special_teams_goals"] == -2
    assert s["combined_st_index"] == 100.0


# -------------------------------------------------------------- plus/minus ---

def test_plus_minus_attribution_canonical_game():
    svc = _TestService(canonical_game())
    # p88: PP goal 0, SH against -1, PP against 0, SH for +1, ES against -1
    assert svc.calculate_plus_minus_for_events("p88", canonical_game(), TEAM) == -1
    # p19 not on ice for the SH goal for: 0 -1 +0 -1
    assert svc.calculate_plus_minus_for_events("p19", canonical_game(), TEAM) == -2


def test_plus_minus_rule_table_and_penalty_shot():
    events = pd.DataFrame([
        _goal(TEAM, "Power Play", on_ice="p88"),       # our PP goal: 0
        _goal(TEAM, "Penalty Kill", on_ice="p88"),     # our SH goal: +1
        _goal(OPP, "Penalty Kill", on_ice="p88"),      # their PP goal: 0
        _goal(OPP, "Power Play", on_ice="p88"),        # their SH goal: -1
        _goal(OPP, "", on_ice="p88"),                  # unrecorded = ES: -1
        {**_goal(OPP, "Even Strength", on_ice="p88"), "IsPenaltyShot": True},  # PS: 0
    ])
    svc = _TestService(events)
    assert svc.calculate_plus_minus_for_events("p88", events, TEAM) == -1


# ------------------------------------------------------------ game summary ---

def test_game_summary_opponent_pp_and_synthetic_pim():
    svc = _TestService(canonical_game())
    summary = svc.get_game_summary("g1", TEAM)
    assert summary["your_team_pp_goals"] == 1
    # Their PP goal is the one stamped 'Penalty Kill' (we were short-handed)
    assert summary["opponent_pp_goals"] == 1
    assert summary["your_team_pp_opps"] == 1
    assert summary["opponent_pp_opps"] == 2
    assert summary["opponent_pp_pct"] == pytest.approx(0.5)
    # PIM: the synthetic mode penalty (blank player, 'Unspecified') is excluded
    assert summary["your_team_pim"] == 2
    assert summary["opponent_pim"] == 2
