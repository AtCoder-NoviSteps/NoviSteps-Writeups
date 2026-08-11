import json
from datetime import datetime, timezone
from pathlib import Path

import responses
import pytest

from contest_discussions.atcoder import fetch_tasks, find_recently_finished_abc_ids

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@responses.activate
def test_fetch_tasks_parses_task_table():
    html = (FIXTURES_DIR / "abc_tasks_sample.html").read_text(encoding="utf-8")
    responses.get("https://atcoder.jp/contests/abc467/tasks", body=html)

    tasks = fetch_tasks("abc467")

    assert tasks == [
        {
            "id": "abc467_a",
            "contest_id": "abc467",
            "problem_index": "A",
            "name": "Obesity",
        },
        {
            "id": "abc467_b",
            "contest_id": "abc467",
            "problem_index": "B",
            "name": "Keep the Change",
        },
        {
            "id": "abc467_f",
            "contest_id": "abc467",
            "problem_index": "F",
            "name": "Email Scheduling Optimization",
        },
    ]


@responses.activate
def test_fetch_tasks_raises_when_no_task_table_found():
    responses.get(
        "https://atcoder.jp/contests/abc999/tasks",
        body="<html><body>Not Found</body></html>",
    )

    try:
        fetch_tasks("abc999")
        assert False, "expected ValueError"
    except ValueError as error:
        assert "abc999" in str(error)


@responses.activate
def test_fetch_tasks_skips_malformed_rows():
    html = """
    <table><tbody>
    <tr><td>broken row without link</td></tr>
    <tr>
      <td><a href="/contests/abc467/tasks/abc467_a">A</a></td>
      <td><a href="/contests/abc467/tasks/abc467_a">Obesity</a></td>
    </tr>
    </tbody></table>
    """
    responses.get("https://atcoder.jp/contests/abc467/tasks", body=html)

    tasks = fetch_tasks("abc467")

    assert len(tasks) == 1
    assert tasks[0]["problem_index"] == "A"


@responses.activate
def test_find_recently_finished_abc_ids_returns_oldest_first():
    contests = json.loads((FIXTURES_DIR / "contests_sample.json").read_text(encoding="utf-8"))
    responses.get("https://kenkoooo.com/atcoder/resources/contests.json", json=contests)

    now = datetime(2026, 7, 21, tzinfo=timezone.utc)
    result = find_recently_finished_abc_ids(now=now, limit=3)

    # abc468 is in the future, arc199 is not an ABC -> excluded.
    # Among the finished ABCs (465, 466, 467), the 3 most recent, oldest first.
    assert result == ["abc465", "abc466", "abc467"]


@responses.activate
def test_find_recently_finished_abc_ids_respects_limit():
    contests = json.loads((FIXTURES_DIR / "contests_sample.json").read_text(encoding="utf-8"))
    responses.get("https://kenkoooo.com/atcoder/resources/contests.json", json=contests)

    now = datetime(2026, 7, 21, tzinfo=timezone.utc)
    result = find_recently_finished_abc_ids(now=now, limit=1)

    assert result == ["abc467"]


@responses.activate
def test_find_recently_finished_abc_ids_returns_empty_for_zero_limit():
    contests = json.loads((FIXTURES_DIR / "contests_sample.json").read_text(encoding="utf-8"))
    responses.get("https://kenkoooo.com/atcoder/resources/contests.json", json=contests)

    now = datetime(2026, 7, 21, tzinfo=timezone.utc)
    result = find_recently_finished_abc_ids(now=now, limit=0)

    assert result == []


@responses.activate
def test_find_recently_finished_abc_ids_rejects_naive_datetime():
    contests = json.loads((FIXTURES_DIR / "contests_sample.json").read_text(encoding="utf-8"))
    responses.get("https://kenkoooo.com/atcoder/resources/contests.json", json=contests)

    with pytest.raises(ValueError, match="timezone-aware"):
        find_recently_finished_abc_ids(now=datetime(2026, 7, 21), limit=3)
