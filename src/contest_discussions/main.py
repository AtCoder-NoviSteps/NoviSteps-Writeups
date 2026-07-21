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
    """Posts a Discussion for every task missing one, across the target contests.

    Per-contest fetch failures and per-task creation failures are caught and
    logged, not raised — one bad contest or task must not stop the others.
    """
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
                print(
                    f"Failed to create discussion for '{title}': {error}",
                    file=sys.stderr,
                )
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
