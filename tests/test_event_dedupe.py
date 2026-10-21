"""Duplicate event rows: the sheet can hold two rows for one event ID
(a retried app upload appends a copy instead of updating the original),
and every viewer stat counts rows — a duplicated goal row showed a
0-4 game as 0-5 in Oct 2026. get_events now runs dedupe_event_rows,
which keeps the LAST row per ID (appends land below earlier copies,
so the last row is the newest version of the event).
"""
import pandas as pd

from hockey_stats_webapp.services.sheets_service import dedupe_event_rows


def _df(rows):
    return pd.DataFrame(rows, columns=["ID", "GameID", "IsGoal"])


def test_identical_duplicates_collapse():
    df = _df([["a", "188", "FALSE"], ["b", "188", "TRUE"], ["a", "188", "FALSE"]])
    out = dedupe_event_rows(df)
    assert list(out["ID"]) == ["b", "a"]
    assert len(out) == 2


def test_last_copy_wins_when_versions_differ():
    df = _df([["a", "2", "TRUE"], ["a", "2", "FALSE"]])
    out = dedupe_event_rows(df)
    assert len(out) == 1
    assert out.iloc[0]["IsGoal"] == "FALSE"


def test_no_duplicates_pass_through():
    df = _df([["a", "1", "FALSE"], ["b", "1", "TRUE"]])
    out = dedupe_event_rows(df)
    assert list(out["ID"]) == ["a", "b"]


def test_missing_id_column_and_empty_frame_are_untouched():
    df = pd.DataFrame([["x"]], columns=["Other"])
    assert len(dedupe_event_rows(df)) == 1
    empty = pd.DataFrame(columns=["ID", "GameID", "IsGoal"])
    assert len(dedupe_event_rows(empty)) == 0
