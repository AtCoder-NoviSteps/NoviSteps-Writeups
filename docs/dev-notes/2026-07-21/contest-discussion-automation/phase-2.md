# Phase 2: `atcoder.py` — 問題一覧の取得ロジック

**目的:** `https://atcoder.jp/contests/{contest_id}/tasks` をスクレイピングして、そのコンテストの問題一覧 (`problem_index`, `name` など) を取得する。共同開発者が提供した PoC (`fetch_tasks_from_atcoder.py`) をベースに、テスト可能な形にリファクタしつつエラーハンドリングを追加する。

**参考:** PoC は `docs/dev-notes/2026-06-18/toggle-neutral-badge/fetch_tasks_from_atcoder.py` で共有されたもの (作業後に削除済み)。ロジックの骨格 (最初の `tbody` から各行の1列目 `<a href="/contests/{id}/tasks/{id}">` と2列目テキストを抽出) を踏襲する。

---

### Task 1: テスト用HTML固定データを用意

**Files:**
- Create: `tests/fixtures/abc_tasks_sample.html`

- [ ] **Step 1: AtCoderのタスク表を模したHTMLを作成**

実際の `atcoder.jp/contests/abc467/tasks` の構造 (1列目: 問題記号へのリンク、2列目: 問題名) を模したサンプル。

```html
<html>
<body>
<table>
<tbody>
<tr>
<td><a href="/contests/abc467/tasks/abc467_a">A</a></td>
<td><a href="/contests/abc467/tasks/abc467_a">Obesity</a></td>
<td>100</td>
<td>1 sec</td>
<td>1024 MB</td>
</tr>
<tr>
<td><a href="/contests/abc467/tasks/abc467_b">B</a></td>
<td><a href="/contests/abc467/tasks/abc467_b">Keep the Change</a></td>
<td>150</td>
<td>2 sec</td>
<td>1024 MB</td>
</tr>
<tr>
<td><a href="/contests/abc467/tasks/abc467_f">F</a></td>
<td><a href="/contests/abc467/tasks/abc467_f">Email Scheduling Optimization</a></td>
<td>500</td>
<td>2 sec</td>
<td>1024 MB</td>
</tr>
</tbody>
</table>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add tests/fixtures/abc_tasks_sample.html
git commit -m "test: add AtCoder tasks page HTML fixture"
```

---

### Task 2: `fetch_tasks` の失敗するテストを書く

**Files:**
- Create: `tests/test_atcoder.py`

- [ ] **Step 1: テストを書く**

```python
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
```

- [ ] **Step 2: 実行して失敗を確認**

Run: `uv run pytest tests/test_atcoder.py -v`
Expected: `ModuleNotFoundError: No module named 'contest_discussions.atcoder'` で FAIL

---

### Task 3: `fetch_tasks` を実装

**Files:**
- Create: `src/contest_discussions/atcoder.py`

- [ ] **Step 1: 実装**

```python
"""Fetches contest/task metadata directly from the AtCoder website."""

import re

import requests
from selectolax.parser import HTMLParser

REQUEST_TIMEOUT_SECONDS = 10

_TASK_HREF_PATTERN = re.compile(r"^/contests/([^/]+)/tasks/([^/]+)$")


def fetch_tasks(contest_id: str) -> list[dict[str, str]]:
    """Fetches the task list for a contest from its AtCoder tasks page.

    Returns a list of dicts with keys: id, contest_id, problem_index, name.
    Raises ValueError if the task table cannot be found on the page.
    """
    url = f"https://atcoder.jp/contests/{contest_id}/tasks"
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    tree = HTMLParser(response.text)
    tbody = tree.css_first("tbody")

    if tbody is None:
        raise ValueError(f"No task table found on the tasks page for {contest_id}")

    tasks = []

    for row in tbody.css("tr"):
        task = _parse_row(row)

        if task is not None:
            tasks.append(task)

    return tasks


def _parse_row(row) -> dict[str, str] | None:
    cells = row.css("td")

    if len(cells) < 2:
        return None

    link = cells[0].css_first("a")

    if link is None or "href" not in link.attributes:
        return None

    match = _TASK_HREF_PATTERN.match(link.attributes["href"])

    if match is None:
        return None

    contest_id, task_id = match.groups()
    problem_index = cells[0].text(strip=True)
    name = cells[1].text(strip=True)

    if not problem_index or not name:
        return None

    return {
        "id": task_id,
        "contest_id": contest_id,
        "problem_index": problem_index,
        "name": name,
    }
```

- [ ] **Step 2: テストを実行して成功を確認**

Run: `uv run pytest tests/test_atcoder.py -v`
Expected: 3 tests PASS

- [ ] **Step 3: Commit**

```bash
git add src/contest_discussions/atcoder.py tests/test_atcoder.py
git commit -m "feat: fetch task list from AtCoder tasks page"
```
