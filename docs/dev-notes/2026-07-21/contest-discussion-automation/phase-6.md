# Phase 6: GitHub Actions ワークフロー配線 + 手動E2E検証

**目的:** cron + `workflow_dispatch` で `contest_discussions.main` を実行する本番ワークフローを用意し、実際に1回動かして end-to-end で確認する。

**注意:** このフェーズの最終ステップは実際に公開リポジトリへ Discussion を作成する。**ユーザーの明示的な許可を得てから実行すること。**

---

### Task 1: 本番ワークフローの作成

**Files:**
- Create: `.github/workflows/post_discussions.yml`
- Delete: `.github/workflows/smoke_test_discussion.yml` (Phase 1 で作成した検証用ワークフロー)

- [ ] **Step 1: ワークフローを作成**

cron は「ABCは毎週土曜21:00 JST開始・100分」という前提で、終了 (22:40 JST = 13:40 UTC) の10分後に設定する。開催時間が変則的な回もあるため、`CONTESTS_TO_CHECK` による取りこぼし救済 (Phase 3) が効いてくる。

**注意:** `astral-sh/setup-uv@v3` の `python-version` 入力がこのバージョンでサポートされているか、実装時に確認すること。未対応の場合は `actions/setup-python` を別ステップで追加するか `uv python install 3.13` を実行する。

```yaml
name: Post contest discussions

on:
  schedule:
    - cron: '50 13 * * 6'
  workflow_dispatch:
    inputs:
      contest_id:
        description: 'Contest ID to backfill (e.g. abc467). Leave empty for automatic detection.'
        required: false

permissions:
  contents: read
  discussions: write

jobs:
  post-discussions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: uv sync

      - name: Post discussions
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          CONTEST_ID: ${{ github.event.inputs.contest_id }}
        run: |
          if [ -n "$CONTEST_ID" ]; then
            uv run python -m contest_discussions.main --contest-id "$CONTEST_ID"
          else
            uv run python -m contest_discussions.main
          fi
```

- [ ] **Step 2: 検証用ワークフローを削除**

```bash
git rm .github/workflows/smoke_test_discussion.yml
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/post_discussions.yml
git commit -m "ci: add scheduled workflow to post ABC contest discussions"
```

---

### Task 2 (ユーザー確認必須・手動): 実際に1回動かして確認

- [ ] **Step 1: push**

```bash
git push -u origin <branch-name>
```

- [ ] **Step 2: 既に Discussion が存在しない過去のABC (または amount 上限内で自然に検出される最新ABC) を対象に手動実行**

```bash
gh workflow run post_discussions.yml
gh run watch
```

- [ ] **Step 3: 結果を確認**

- NoviSteps-Writeups の Discussions ページで、実際に問題ごとのDiscussionが作成されたことを確認する
- タイトル・本文が既存の手動投稿と同じ形式になっているか目視確認する
- ワークフローのログで、重複スキップ (`title in existing_titles`) が正しく機能しているか確認する

- [ ] **Step 4: 問題があれば修正してから Phase 7 へ**
