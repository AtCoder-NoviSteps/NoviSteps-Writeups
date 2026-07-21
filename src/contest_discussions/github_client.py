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
    Network/HTTP failures propagate as requests.RequestException (e.g.
    requests.HTTPError, requests.Timeout) — callers should catch that.
    """
    data = _post_graphql(
        token,
        _EXISTING_TITLES_QUERY,
        {"repositoryId": REPOSITORY_ID, "categoryId": GENERAL_CATEGORY_ID},
    )
    nodes = data["node"]["discussions"]["nodes"]

    return {node["title"] for node in nodes}


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
