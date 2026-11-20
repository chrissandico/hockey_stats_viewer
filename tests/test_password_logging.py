"""Tests pinning that password VALUES never reach the server logs.

The defect (found in the 2026-10-05 code review, still live until this
fix): the login path printed password values in plain text —

- app.py's login callback printed the submitted password twice
  (``print(f"password: {password}")`` and
  ``print(f"Attempting to verify password: {password}")``) and then
  dumped the whole verify_password result dict, which carried the
  matched password under its 'password' key.
- auth_service.verify_password printed every failed attempt
  (``WARNING: Invalid password attempt: '<value>'``).
- sheets_service.get_teams embedded the actual duplicated password
  values in its duplicate-password error message — printed, raised,
  and reachable from the login path's error handling.

With per-family parent codes about to be issued, every one of those
lines would have put a real family's code into the logs. The fix
keeps every non-sensitive diagnostic (team name, role, jersey,
success/failure) and removes only the values; verify_password's
result dicts no longer carry a 'password' key at all (repo-wide grep
showed no consumer of that key).

These tests are the regression fence:

1. An AST guard over app.py and auth_service.py: no print/logging
   call may reference the password variables (``password``,
   ``clean_pwd``) or dump the whole verify-result dict.
2. verify_password's returned dict literals must not contain a
   'password' key.
3. sheets_service must never interpolate the Teams sheet's Password
   values into its duplicate-password error (the ``.tolist()`` of
   the Password column), while keeping the error itself.
4. Behavioural: with a stub sheets service, a coach login, a parent
   login and a failed attempt must keep their secrets out of stdout
   and out of the returned dict, with all other fields unchanged.

Run:  python -m pytest tests/test_password_logging.py
"""
import ast
import os
import re
import sys

import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(HERE, "..", "hockey_stats_webapp")
sys.path.insert(0, os.path.join(APP_DIR, "services"))

from auth_service import AuthService  # noqa: E402

# Variables that hold a password VALUE in the auth path. A print/log
# call referencing either one interpolates the value into the output.
PASSWORD_VALUE_NAMES = {"password", "clean_pwd"}

# The verify_password result dicts. Printing one whole (a bare name
# as an argument or an f-string field) dumps every key it carries.
RESULT_DICT_NAMES = {"team_info", "info"}

LOG_METHODS = {"debug", "info", "warning", "error", "critical",
               "exception", "log"}


def _read(*parts):
    with open(os.path.join(*parts), "r", encoding="utf-8",
              newline="") as fh:
        return fh.read()


def _output_calls(tree):
    """Every print(...) or logging-style call in the module."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "print":
            yield node
        elif isinstance(func, ast.Attribute) and func.attr in LOG_METHODS:
            yield node


def _password_offences(source):
    """Descriptions of output calls that would leak a password value."""
    offences = []
    for call in _output_calls(ast.parse(source)):
        args = list(call.args) + [kw.value for kw in call.keywords]
        for arg in args:
            if isinstance(arg, ast.Name) and arg.id in RESULT_DICT_NAMES:
                offences.append(
                    f"line {call.lineno}: whole result dict "
                    f"'{arg.id}' passed to an output call")
            for node in ast.walk(arg):
                if (isinstance(node, ast.Name)
                        and node.id in PASSWORD_VALUE_NAMES):
                    offences.append(
                        f"line {call.lineno}: output call references "
                        f"password variable '{node.id}'")
                if (isinstance(node, ast.FormattedValue)
                        and isinstance(node.value, ast.Name)
                        and node.value.id in RESULT_DICT_NAMES):
                    offences.append(
                        f"line {call.lineno}: f-string dumps whole "
                        f"result dict '{node.value.id}'")
    return offences


@pytest.mark.parametrize("relpath", [
    ("app.py",),
    ("services", "auth_service.py"),
])
def test_no_password_values_in_output_calls(relpath):
    """If this fails, a password value is on its way back into the
    server logs — the exact leak this PR removed. Log the team, the
    role, the jersey, success/failure — never the value."""
    offences = _password_offences(_read(APP_DIR, *relpath))
    assert not offences, "; ".join(offences)


def test_verify_password_result_dicts_have_no_password_key():
    """The result dicts historically carried the matched password
    under 'password'. Nothing in the repo consumed that key, so it
    is gone; if it returns, any future dict dump leaks again."""
    tree = ast.parse(_read(APP_DIR, "services", "auth_service.py"))
    verify_fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "verify_password")
    for node in ast.walk(verify_fn):
        if isinstance(node, ast.Dict):
            keys = {k.value for k in node.keys
                    if isinstance(k, ast.Constant)
                    and isinstance(k.value, str)}
            assert "password" not in keys, (
                "verify_password result dict must not carry the "
                "password value")


def test_sheets_service_never_lists_password_values():
    """The duplicate-password error in get_teams used to embed the
    duplicated values themselves (``['Password'].tolist()``). The
    error must stay — duplicates are a real data problem — but it
    may only report counts, never values."""
    src = _read(APP_DIR, "services", "sheets_service.py")
    assert not re.search(r"\[\s*'Password'\s*\]\s*\.tolist\(\)", src), (
        "Teams Password values must not be interpolated into the "
        "duplicate-password error message")
    assert "Duplicate passwords found in Teams sheet" in src, (
        "the duplicate-password error itself must be kept")


class _StubSheets:
    """Minimal sheets service: one coach team, one parent code."""

    def get_teams(self, force_refresh=False):
        return pd.DataFrame([{
            "TeamID": "waxersu13a",
            "TeamName": "Waxers U13 A",
            "Password": "coach-secret-1",
        }])

    def get_parent_codes(self):
        return pd.DataFrame([{
            "ParentCode": "parent-secret-25",
            "TeamID": "waxersu13a",
            "JerseyNumber": "25",
            "PlayerID": "",
            "ChildName": "Test Child",
        }])


def test_coach_login_keeps_secret_out_of_logs_and_result(capsys):
    info = AuthService(_StubSheets()).verify_password("coach-secret-1")
    out = capsys.readouterr().out
    assert info and info["team_id"] == "waxersu13a"
    assert info["is_coach"] is True and info["is_parent"] is False
    assert "password" not in info
    assert "coach-secret-1" not in out


def test_parent_login_keeps_secret_out_of_logs_and_result(capsys):
    info = AuthService(_StubSheets()).verify_password("parent-secret-25")
    out = capsys.readouterr().out
    assert info and info["is_parent"] is True
    assert info["jersey_number"] == "25"
    assert "password" not in info
    assert "parent-secret-25" not in out


def test_failed_attempt_keeps_guess_out_of_logs(capsys):
    result = AuthService(_StubSheets()).verify_password("wrong-guess-9")
    out = capsys.readouterr().out
    assert result is False
    assert "wrong-guess-9" not in out
