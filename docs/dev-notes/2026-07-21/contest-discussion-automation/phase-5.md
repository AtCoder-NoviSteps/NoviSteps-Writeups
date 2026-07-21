# Phase 5: `main.py` — オーケストレーション + CLI

**目的:** Phase 2〜4 で作った部品を繋げ、「終了済み最新ABCを探す → 問題一覧を取る → 未投稿のものだけDiscussionを作る」を1本のスクリプトにする。タイトル組み立て、タスク単位のスキップ・エラー握りつぶし (継続) ロジックがこのフェーズの核心。

---

### Task 1: 失敗するテストを書く

**Files:**
- Create: `tests/test_main.py`

- [ ] **Step 1: テストを書く**

`atcoder` / `github_client` をモジュール単位でモンキーパッチし、`main.run()` のオーケストレーションだけを検証する。

```python
from contest_discussions import main


def test_build_title_formats_correctly():
    task = {"problem_index": "F", "name": "Email Scheduling Optimization"}
    assert main.build_title("abc467", task) == "ABC 467 F - Email Scheduling Optimization"


def test_run_skips_tasks_that_already_have_a_discussion(monkeypatch):
    monkeypatch.setattr(
        main.atcoder, "find_recently_finished_abc_ids", lambda limit: ["abc467"]
    )
    monkeypatch.setattr(
        main.atcoder,
        "fetch_tasks",
        lambda contest_id: [
            {"id": "abc467_a", "contest_id": "abc467", "problem_index": "A", "name": "Obesity"},
            {"id": "abc467_b", "contest_id": "abc467", "problem_index": "B", "name": "Keep the Change"},
        ],
    )
    monkeypatch.setattr(
        main.github_client,
        "existing_discussion_titles",
        lambda token: {"ABC 467 A - Obesity"},
    )
    created = []
    monkeypatch.setattr(
        main.github_client,
        "create_discussion",
        lambda token, title, body: created.append(title) or "https://example.invalid",
    )

    main.run("fake-token")

    assert created == ["ABC 467 B - Keep the Change"]


def test_run_continues_after_a_single_task_creation_failure(monkeypatch):
    monkeypatch.setattr(
        main.atcoder, "find_recently_finished_abc_ids", lambda limit: ["abc467"]
    )
    monkeypatch.setattr(
        main.atcoder,
        "fetch_tasks",
        lambda contest_id: [
            {"id": "abc467_a", "contest_id": "abc467", "problem_index": "A", "name": "Obesity"},
            {"id": "abc467_b", "contest_id": "abc467", "problem_index": "B", "name": "Keep the Change"},
        ],
    )
    monkeypatch.setattr(main.github_client, "existing_discussion_titles", lambda token: set())

    created = []

    def fake_create_discussion(token, title, body):
        if title == "ABC 467 A - Obesity":
            raise RuntimeError("boom")
        created.append(title)
        return "https://example.invalid"

    monkeypatch.setattr(main.github_client, "create_discussion", fake_create_discussion)

    main.run("fake-token")  # must not raise

    assert created == ["ABC 467 B - Keep the Change"]


def test_run_continues_after_a_single_contest_fetch_failure(monkeypatch):
    monkeypatch.setattr(
        main.atcoder, "find_recently_finished_abc_ids", lambda limit: ["abc466", "abc467"]
    )

    def fake_fetch_tasks(contest_id):
        if contest_id == "abc466":
            raise ValueError("no task table")
        return [{"id": "abc467_a", "contest_id": "abc467", "problem_index": "A", "name": "Obesity"}]

    monkeypatch.setattr(main.atcoder, "fetch_tasks", fake_fetch_tasks)
    monkeypatch.setattr(main.github_client, "existing_discussion_titles", lambda token: set())

    created = []
    monkeypatch.setattr(
        main.github_client,
        "create_discussion",
        lambda token, title, body: created.append(title) or "https://example.invalid",
    )

    main.run("fake-token")  # must not raise

    assert created == ["ABC 467 A - Obesity"]


def test_run_uses_explicit_contest_id_when_given(monkeypatch):
    called_with = []
    monkeypatch.setattr(
        main.atcoder,
        "find_recently_finished_abc_ids",
        lambda limit: (_ for _ in ()).throw(AssertionError("should not be called")),
    )
    monkeypatch.setattr(
        main.atcoder,
        "fetch_tasks",
        lambda contest_id: called_with.append(contest_id) or [],
    )
    monkeypatch.setattr(main.github_client, "existing_discussion_titles", lambda token: set())

    main.run("fake-token", contest_id="abc468")

    assert called_with == ["abc468"]
```

- [ ] **Step 2: 実行して失敗を確認**

Run: `uv run pytest tests/test_main.py -v`
Expected: `ModuleNotFoundError: No module named 'contest_discussions.main'` で FAIL

---

### Task 2: `main.py` を実装

**Files:**
- Create: `src/contest_discussions/main.py`

- [ ] **Step 1: 実装**

```python
"""Orchestrates finding recently finished ABC contests and posting Discussions
for any problems that don't have one yet."""

import argparse
import os
import sys

from contest_discussions import atcoder, github_client
from contest_discussions.constants import CONTESTS_TO_CHECK, DISCUSSION_BODY


def build_title(contest_id: str, task: dict) -> str:
    number = int(contest_id[3:])
    return f"ABC {number} {task['problem_index']} - {task['name']}"


def run(token: str, contest_id: str | None = None) -> None:
    contest_ids = (
        [contest_id]
        if contest_id
        else atcoder.find_recently_finished_abc_ids(limit=CONTESTS_TO_CHECK)
    )

    if not contest_ids:
        print("No finished ABC contests found.")
        return

    existing_titles = github_client.existing_discussion_titles(token)

    for cid in contest_ids:
        try:
            tasks = atcoder.fetch_tasks(cid)
        except Exception as error:
            print(f"Failed to fetch tasks for {cid}: {error}", file=sys.stderr)
            continue

        for task in tasks:
            title = build_title(cid, task)

            if title in existing_titles:
                continue

            try:
                url = github_client.create_discussion(token, title, DISCUSSION_BODY)
            except Exception as error:
                print(f"Failed to create discussion for '{title}': {error}", file=sys.stderr)
                continue

            print(f"Created: {url}")
            existing_titles.add(title)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post ABC contest discussions to NoviSteps-Writeups."
    )
    parser.add_argument(
        "--contest-id",
        default=None,
        help="Contest ID to backfill (e.g. abc467). If omitted, automatically "
        "detects recently finished ABCs.",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise SystemExit("GITHUB_TOKEN environment variable is not set.")

    run(token, contest_id=args.contest_id)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: テストを実行して成功を確認**

Run: `uv run pytest tests/test_main.py -v`
Expected: 5 tests PASS

- [ ] **Step 3: 全テストを実行**

Run: `uv run pytest -v`
Expected: Phase 2〜5 の全テストが PASS

- [ ] **Step 4: Commit**

```bash
git add src/contest_discussions/main.py tests/test_main.py
git commit -m "feat: orchestrate finding and posting ABC discussions"
```
