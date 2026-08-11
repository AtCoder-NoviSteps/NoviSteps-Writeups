# Phase 3: `atcoder.py` — 終了済み最新コンテストの判定ロジック

**目的:** AtCoder Problems の軽量な `contests.json` から、終了済みの ABC のうち直近 `CONTESTS_TO_CHECK` 件の contest_id を特定する。cron が1回失敗しても次回実行で取りこぼしを埋め合わせられるよう、複数件を対象にする (設計根拠は `plan.md` 参照)。

---

### Task 1: テスト用JSON固定データを用意

**Files:**
- Create: `tests/fixtures/contests_sample.json`

- [ ] **Step 1: 固定データを作成**

`now = 2026-07-21T00:00:00Z` (epoch `1784592000`) を基準に、終了済みのABC3件・未来のABC1件・ABC以外1件を含める。

**注意:** `start_epoch_second + duration_second` が必ず `now` (`1784592000`) 以下になるように、abc465/466/467 は3週間隔で `now` より前の日付にしてある。abc468 だけ `now` より後 (未来) にして、未終了として除外されることを確認する。

```json
[
  {
    "id": "abc465",
    "start_epoch_second": 1782392400,
    "duration_second": 6000,
    "title": "AtCoder Beginner Contest 465",
    "rate_change": "~ 1999"
  },
  {
    "id": "abc466",
    "start_epoch_second": 1782997200,
    "duration_second": 6000,
    "title": "AtCoder Beginner Contest 466",
    "rate_change": "~ 1999"
  },
  {
    "id": "abc467",
    "start_epoch_second": 1783602000,
    "duration_second": 6000,
    "title": "AtCoder Beginner Contest 467",
    "rate_change": "~ 1999"
  },
  {
    "id": "abc468",
    "start_epoch_second": 1784811600,
    "duration_second": 6000,
    "title": "AtCoder Beginner Contest 468",
    "rate_change": "~ 1999"
  },
  {
    "id": "arc199",
    "start_epoch_second": 1782997200,
    "duration_second": 7200,
    "title": "AtCoder Regular Contest 199",
    "rate_change": "All"
  }
]
```

- [ ] **Step 2: Commit**

```bash
git add tests/fixtures/contests_sample.json
git commit -m "test: add AtCoder Problems contests.json fixture"
```

---

### Task 2: 失敗するテストを書く

**Files:**
- Modify: `tests/test_atcoder.py`

- [ ] **Step 1: テストを追加**

```python
import json
from datetime import datetime, timezone

from contest_discussions.atcoder import find_recently_finished_abc_ids

# 以下を test_atcoder.py の末尾に追加


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
```

- [ ] **Step 2: 実行して失敗を確認**

Run: `uv run pytest tests/test_atcoder.py -v`
Expected: `ImportError: cannot import name 'find_recently_finished_abc_ids'` で FAIL

---

### Task 3: `find_recently_finished_abc_ids` を実装

**Files:**
- Modify: `src/contest_discussions/atcoder.py`

- [ ] **Step 1: 実装を追加**

```python
# atcoder.py の先頭に追加
from datetime import datetime, timezone

CONTESTS_JSON_URL = "https://kenkoooo.com/atcoder/resources/contests.json"

_ABC_ID_PATTERN = re.compile(r"^abc\d{3}$")


def find_recently_finished_abc_ids(
    now: datetime | None = None, limit: int = 3
) -> list[str]:
    """Returns up to `limit` most recently finished ABC contest_ids, oldest first."""
    if now is None:
        now = datetime.now(timezone.utc)

    response = requests.get(CONTESTS_JSON_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    contests = response.json()

    now_epoch = now.timestamp()
    finished_abc = [
        contest
        for contest in contests
        if _ABC_ID_PATTERN.match(contest["id"])
        and contest["start_epoch_second"] + contest["duration_second"] <= now_epoch
    ]
    finished_abc.sort(key=lambda contest: contest["start_epoch_second"])

    return [contest["id"] for contest in finished_abc[-limit:]]
```

- [ ] **Step 2: テストを実行して成功を確認**

Run: `uv run pytest tests/test_atcoder.py -v`
Expected: 5 tests PASS (Phase 2 の3件 + 今回の2件)

- [ ] **Step 3: Commit**

```bash
git add src/contest_discussions/atcoder.py tests/test_atcoder.py
git commit -m "feat: find recently finished ABC contest ids"
```
