# Phase 1: プロジェクト初期化 + GITHUB_TOKEN 権限検証

**目的:** uv プロジェクトの雛形を作り、「Actions 標準の `GITHUB_TOKEN` + `permissions: discussions: write` で Discussion 作成が可能」という設計上の前提を、実際にワークフローを1回動かして検証する。ここで検証できなければ、後続フェーズの認証方式を PAT に差し替える必要があるため、最初に確認する。

**注意:** このフェーズの最終ステップ (ワークフローの手動実行) は、公開リポジトリに実際の Discussion を作成する。**ユーザーの明示的な許可を得てから実行すること。** 無断でリモートに push したりワークフローを実行したりしない。

---

### Task 1: uv プロジェクトの初期化

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: pyproject.toml を作成**

```toml
[project]
name = "contest-discussions"
version = "0.1.0"
description = "Automatically create GitHub Discussions for each ABC problem after the contest ends."
readme = "README.md"
requires-python = ">=3.13,<4.0"
dependencies = [
    "requests>=2.32",
    "selectolax>=0.4.6",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "responses>=0.25",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
```

- [ ] **Step 2: 依存関係をインストール**

Run: `uv sync`
Expected: `uv.lock` が生成され、`.venv/` が作成される

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: initialize uv project for contest discussion automation"
```

---

### Task 2: パッケージ雛形の作成

**Files:**
- Create: `src/contest_discussions/__init__.py`

- [ ] **Step 1: 空の `__init__.py` を作成**

```python
```

- [ ] **Step 2: Commit**

```bash
git add src/contest_discussions/__init__.py
git commit -m "chore: add contest_discussions package skeleton"
```

---

### Task 3: 定数モジュールの作成

**Files:**
- Create: `src/contest_discussions/constants.py`

- [ ] **Step 1: 定数を定義**

```python
"""Fixed IDs and text for the NoviSteps-Writeups repository.

See: https://github.com/AtCoder-NoviSteps/NoviSteps-Writeups
"""

# `gh api graphql -f query='query { repository(owner: "AtCoder-NoviSteps", name: "NoviSteps-Writeups") { id } }'`
REPOSITORY_ID = "R_kgDOTNgHyw"

# "General" discussion category.
# `gh api graphql -f query='query { repository(owner: "AtCoder-NoviSteps", name: "NoviSteps-Writeups") { discussionCategories(first: 10) { nodes { id name } } } }'`
GENERAL_CATEGORY_ID = "DIC_kwDOTNgHy84DAe9x"

DISCUSSION_BODY = "問題の感想や気づきを投稿・共有するスペースです"

# 週次 cron が1回失敗しても次回実行で埋め合わせられるよう、直近何件のABCを
# 重複チェック対象にするか。3件あれば3週分の取りこぼしまでカバーできる。
CONTESTS_TO_CHECK = 3
```

- [ ] **Step 2: Commit**

```bash
git add src/contest_discussions/constants.py
git commit -m "feat: add repository/category constants"
```

---

### Task 4: GITHUB_TOKEN の Discussion 書き込み権限を検証するワークフロー

**Files:**
- Create: `.github/workflows/smoke_test_discussion.yml`

- [ ] **Step 1: workflow_dispatch のみで動く検証用ワークフローを作成**

```yaml
name: Smoke test - GITHUB_TOKEN discussions:write

on:
  workflow_dispatch:

permissions:
  discussions: write

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - name: Create a throwaway test discussion
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh api graphql -f query='
          mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
            createDiscussion(input: {
              repositoryId: $repositoryId,
              categoryId: $categoryId,
              title: $title,
              body: $body
            }) {
              discussion { id url }
            }
          }' \
            -f repositoryId="R_kgDOTNgHyw" \
            -f categoryId="DIC_kwDOTNgHy84DAe9x" \
            -f title="[smoke test] GITHUB_TOKEN discussions:write check (safe to delete)" \
            -f body="Created by CI to verify that the default GITHUB_TOKEN can create Discussions. Safe to delete."
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/smoke_test_discussion.yml
git commit -m "ci: add smoke test workflow for GITHUB_TOKEN discussions permission"
```

- [ ] **Step 3 (ユーザー確認必須・手動): push してワークフローを実行**

ここは実際に公開リポジトリへ push し、ワークフローを実行して Discussion を1件作成する。**必ずユーザーに実行してよいか確認してから進めること。**

```bash
git push -u origin <branch-name>
gh workflow run smoke_test_discussion.yml
gh run watch
```

- [ ] **Step 4: 結果を確認**

- 成功した場合: NoviSteps-Writeups の Discussions に "[smoke test] ..." が作成されているので、`gh api graphql` の `deleteDiscussion` mutation か GitHub UI から削除する。以降のフェーズは `GITHUB_TOKEN` + `permissions: discussions: write` の方針で進める。
- 失敗した場合 (権限エラー等): `plan.md` の「却下した代替案」を更新し、Fine-grained PAT をリポジトリシークレット (`GITHUB_DISCUSSIONS_TOKEN` 等) として発行する方針に切り替える。Phase 4/6 の認証部分をその前提で書き直す。

- [ ] **Step 5: 検証用ワークフローを削除 (恒久ワークフローに置き換えるため)**

Phase 6 で正式なワークフローに差し替えるため、このスモークテスト用ファイルは Phase 6 で削除する (このフェーズでは残しておいてよい)。
