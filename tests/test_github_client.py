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
