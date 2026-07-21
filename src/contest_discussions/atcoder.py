"""Fetches contest/task metadata directly from the AtCoder website."""

import re

import requests
from selectolax.parser import HTMLParser

REQUEST_TIMEOUT_SECONDS = 10

_TASK_HREF_PATTERN = re.compile(r"^/contests/([^/]+)/tasks/([^/]+)$")


def fetch_tasks(contest_id: str) -> list[dict[str, str]]:
    """Fetches the task list for a contest from its AtCoder tasks page.

    Returns a list of dicts with keys: id, contest_id, problem_index, name.
    Raises ValueError if the task table cannot be found on the page.
    """
    url = f"https://atcoder.jp/contests/{contest_id}/tasks"
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    tree = HTMLParser(response.text)
    tbody = tree.css_first("tbody")

    if tbody is None:
        raise ValueError(f"No task table found on the tasks page for {contest_id}")

    tasks = []

    for row in tbody.css("tr"):
        task = _parse_row(row)

        if task is not None:
            tasks.append(task)

    return tasks


def _parse_row(row) -> dict[str, str] | None:
    cells = row.css("td")

    if len(cells) < 2:
        return None

    link = cells[0].css_first("a")

    if link is None or "href" not in link.attributes:
        return None

    match = _TASK_HREF_PATTERN.match(link.attributes["href"])

    if match is None:
        return None

    contest_id, task_id = match.groups()
    problem_index = cells[0].text(strip=True)
    name = cells[1].text(strip=True)

    if not problem_index or not name:
        return None

    return {
        "id": task_id,
        "contest_id": contest_id,
        "problem_index": problem_index,
        "name": name,
    }
