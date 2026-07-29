"""Minimal GitHub GraphQL client for the NoviSteps-Writeups Discussions API."""

import requests

from contest_discussions.constants import GENERAL_CATEGORY_ID, REPOSITORY_ID

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
REQUEST_TIMEOUT_SECONDS = 10

_EXISTING_TITLES_QUERY = """
query($repositoryId: ID!, $categoryId: ID!, $after: String) {
  node(id: $repositoryId) {
    ... on Repository {
      discussions(categoryId: $categoryId, first: 100, after: $after, orderBy: {field: CREATED_AT, direction: DESC}) {
        nodes { title }
        pageInfo { hasNextPage endCursor }
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
    """Returns all Discussion titles in the General category.

    Discussions are fetched in pages of 100 to ensure older titles are also
    considered during backfills.
    Network/HTTP failures propagate as requests.RequestException (e.g.
    requests.HTTPError, requests.Timeout) — callers should catch that.
    """
    titles = set()
    after = None

    while True:
        data = _post_graphql(
            token,
            _EXISTING_TITLES_QUERY,
            {
                "repositoryId": REPOSITORY_ID,
                "categoryId": GENERAL_CATEGORY_ID,
                "after": after,
            },
        )
        discussions = data["node"]["discussions"]
        titles.update(node["title"] for node in discussions["nodes"])

        page_info = discussions["pageInfo"]
        if not page_info["hasNextPage"]:
            return titles

        after = page_info["endCursor"]
        if after is None:
            raise RuntimeError("GitHub GraphQL API returned no cursor for the next page")


def create_discussion(token: str, title: str, body: str) -> str:
    """Creates a Discussion in the General category and returns its URL.

    Network/HTTP failures propagate as requests.RequestException (e.g.
    requests.HTTPError, requests.Timeout) — callers should catch that.
    """
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
