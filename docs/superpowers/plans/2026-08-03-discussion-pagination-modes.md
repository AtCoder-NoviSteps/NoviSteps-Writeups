# Discussion Pagination Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Limit automatic duplicate checks to the newest Discussion page while retaining complete checks for manual contest backfills.

**Architecture:** `existing_discussion_titles()` gains a keyword-only `fetch_all` flag that defaults to `False`. `run()` enables it only when the caller supplied `contest_id`; automatic discovery remains a single GraphQL page.

**Tech Stack:** Python 3.13, requests, pytest, responses.

## Global Constraints

- Keep the GraphQL page size at 100 Discussions.
- Preserve full pagination for `--contest-id` manual backfills.
- Keep automatic duplicate checks to exactly one GraphQL request.

---

### Task 1: Cover automatic and manual pagination behavior

**Files:**
- Modify: `tests/test_github_client.py`
- Modify: `tests/test_main.py`

**Interfaces:**
- Consumes: `existing_discussion_titles(token: str, *, fetch_all: bool = False) -> set[str]`
- Produces: Regression coverage for one-page automatic mode and full manual mode.

- [ ] **Step 1: Write the failing client tests**

```python
def test_existing_discussion_titles_returns_only_first_page_by_default():
    # Mock first page with hasNextPage=True, call without fetch_all,
    # then assert only the first title is returned and one request was made.

def test_existing_discussion_titles_paginates_when_fetch_all_is_requested():
    # Mock two pages, call with fetch_all=True, and assert both titles exist.
```

- [ ] **Step 2: Write the failing orchestration test**

```python
def test_run_uses_full_discussion_pagination_for_manual_contest(mocker):
    mock_titles = mocker.patch("contest_discussions.main.github_client.existing_discussion_titles")
    run("token", contest_id="abc467")
    mock_titles.assert_called_once_with("token", fetch_all=True)
```

- [ ] **Step 3: Run the focused tests and confirm they fail because `fetch_all` is unsupported**

Run: `python -m pytest tests/test_github_client.py tests/test_main.py -q`

- [ ] **Step 4: Commit the failing tests**

```bash
git add tests/test_github_client.py tests/test_main.py
git commit -m "test: cover discussion pagination modes"
```

### Task 2: Implement the two pagination modes

**Files:**
- Modify: `src/contest_discussions/github_client.py`
- Modify: `src/contest_discussions/main.py`
- Test: `tests/test_github_client.py`
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: `contest_id: str | None` from `run()`.
- Produces: `existing_discussion_titles(token, *, fetch_all=False)`.

- [ ] **Step 1: Add the keyword-only `fetch_all: bool = False` parameter**

```python
def existing_discussion_titles(token: str, *, fetch_all: bool = False) -> set[str]:
```

- [ ] **Step 2: Return after the first page unless `fetch_all` is true and `hasNextPage` is true**

```python
if not fetch_all or not page_info["hasNextPage"]:
    return titles
after = page_info["endCursor"]
```

- [ ] **Step 3: Have `run()` request full pagination only for a supplied contest ID**

```python
existing_titles = github_client.existing_discussion_titles(
    token, fetch_all=contest_id is not None
)
```

- [ ] **Step 4: Run the focused tests and confirm they pass**

Run: `python -m pytest tests/test_github_client.py tests/test_main.py -q`

- [ ] **Step 5: Commit the implementation**

```bash
git add src/contest_discussions/github_client.py src/contest_discussions/main.py
git commit -m "fix: limit automatic discussion duplicate checks"
```

### Task 3: Verify the completed change

**Files:**
- Verify only.

- [ ] **Step 1: Run the full suite**

Run: `python -m pytest -q`

- [ ] **Step 2: Inspect the final diff and status**

Run: `git diff origin/feature/contest-discussion-automation...HEAD --check && git status --short`

- [ ] **Step 3: Commit the approved design and plan documents**

```bash
git add docs/superpowers/specs/2026-08-03-pr-30-human-review-design.md \
        docs/superpowers/plans/2026-08-03-discussion-pagination-modes.md
git commit -m "docs: plan discussion pagination modes"
```
