# Phase 4: `github_client.py` — 既存Discussion確認・作成

**目的:** GitHub GraphQL API を使って (1) "General" カテゴリの既存Discussionタイトル一覧を取得する関数、(2) 新規Discussionを作成する関数を実装する。

GraphQL のスキーマは `gh api graphql` で事前に introspection 済み:
- `createDiscussion` mutation の入力: `repositoryId`, `categoryId`, `title`, `body` (すべて必須)
- `Repository.discussions` の引数: `categoryId`, `first`, `orderBy` など

---

### Task 1: 失敗するテストを書く

**Files:**
- Create: `tests/test_github_client.py`

- [ ] **Step 1: テストを書く**

```python
import responses

from contest_discussions.github_client import (
    GITHUB_GRAPHQL_URL,
    create_discussion,
    existing_discussion_titles,
)


@responses.activate
def test_existing_discussion_titles_returns_titles():
    responses.post(
        GITHUB_GRAPHQL_URL,
        json={
            "data": {
                "node": {
                    "discussions": {
                        "nodes": [
                            {"title": "ABC 467 A - Obesity"},
                            {"title": "ABC 467 B - Keep the Change"},
                        ]
                    }
                }
            }
        },
    )

    titles = existing_discussion_titles("fake-token")

    assert titles == {"ABC 467 A - Obesity", "ABC 467 B - Keep the Change"}


@responses.activate
def test_existing_discussion_titles_raises_on_graphql_errors():
    responses.post(
        GITHUB_GRAPHQL_URL,
        json={"errors": [{"message": "Bad credentials"}]},
    )

    try:
        existing_discussion_titles("fake-token")
        assert False, "expected RuntimeError"
    except RuntimeError as error:
        assert "Bad credentials" in str(error)


@responses.activate
def test_create_discussion_returns_url():
    responses.post(
        GITHUB_GRAPHQL_URL,
        json={
            "data": {
                "createDiscussion": {
                    "discussion": {
                        "id": "D_test123",
                        "url": "https://github.com/AtCoder-NoviSteps/NoviSteps-Writeups/discussions/23",
                    }
                }
            }
        },
    )

    url = create_discussion("fake-token", "ABC 467 G - Many Sweets Problem", "body text")

    assert url == "https://github.com/AtCoder-NoviSteps/NoviSteps-Writeups/discussions/23"
```

- [ ] **Step 2: 実行して失敗を確認**

Run: `uv run pytest tests/test_github_client.py -v`
Expected: `ModuleNotFoundError: No module named 'contest_discussions.github_client'` で FAIL

---

### Task 2: `github_client.py` を実装

**Files:**
- Create: `src/contest_discussions/github_client.py`

- [ ] **Step 1: 実装**

```python
"""Minimal GitHub GraphQL client for the NoviSteps-Writeups Discussions API."""

import requests

from contest_discussions.constants import GENERAL_CATEGORY_ID, REPOSITORY_ID

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
REQUEST_TIMEOUT_SECONDS = 10

_EXISTING_TITLES_QUERY = """
query($repositoryId: ID!, $categoryId: ID!) {
  node(id: $repositoryId) {
    ... on Repository {
      discussions(categoryId: $categoryId, first: 100, orderBy: {field: CREATED_AT, direction: DESC}) {
        nodes { title }
      }
    }
  }
}
"""

_CREATE_DISCUSSION_MUTATION = """
mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
  createDiscussion(input: {
    repositoryId: $repositoryId,
    categoryId: $categoryId,
    title: $title,
    body: $body
  }) {
    discussion { id url }
  }
}
"""


def existing_discussion_titles(token: str) -> set[str]:
    """Returns the titles of the most recent Discussions in the General category.

    Only the first 100 (no pagination) — accepted limitation given weekly ABC
    volume; revisit if the General category ever accumulates enough non-contest
    discussions to push older unposted contest titles out of this window.
    """
    data = _post_graphql(
        token,
        _EXISTING_TITLES_QUERY,
        {"repositoryId": REPOSITORY_ID, "categoryId": GENERAL_CATEGORY_ID},
    )
    nodes = data["node"]["discussions"]["nodes"]

    return {node["title"] for node in nodes}


def create_discussion(token: str, title: str, body: str) -> str:
    """Creates a Discussion in the General category and returns its URL."""
    data = _post_graphql(
        token,
        _CREATE_DISCUSSION_MUTATION,
        {
            "repositoryId": REPOSITORY_ID,
            "categoryId": GENERAL_CATEGORY_ID,
            "title": title,
            "body": body,
        },
    )

    return data["createDiscussion"]["discussion"]["url"]


def _post_graphql(token: str, query: str, variables: dict) -> dict:
    response = requests.post(
        GITHUB_GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()

    if "errors" in payload:
        raise RuntimeError(f"GitHub GraphQL API returned errors: {payload['errors']}")

    return payload["data"]
```

- [ ] **Step 2: テストを実行して成功を確認**

Run: `uv run pytest tests/test_github_client.py -v`
Expected: 3 tests PASS

- [ ] **Step 3: Commit**

```bash
git add src/contest_discussions/github_client.py tests/test_github_client.py
git commit -m "feat: add GitHub GraphQL client for discussion query/creation"
```
