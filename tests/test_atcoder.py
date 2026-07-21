from pathlib import Path

import responses

from contest_discussions.atcoder import fetch_tasks

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
