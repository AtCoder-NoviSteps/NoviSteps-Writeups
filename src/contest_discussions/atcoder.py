"""Fetches contest schedule metadata from the AtCoder Problems API and
per-contest task lists directly from the AtCoder website.
"""

import re
from datetime import datetime, timezone

import requests
from selectolax.parser import HTMLParser

REQUEST_TIMEOUT_SECONDS = 10

CONTESTS_JSON_URL = "https://kenkoooo.com/atcoder/resources/contests.json"

_TASK_HREF_PATTERN = re.compile(r"^/contests/([^/]+)/tasks/([^/]+)$")
_ABC_ID_PATTERN = re.compile(r"^abc\d{3}$")


def fetch_tasks(contest_id: str) -> list[dict[str, str]]:
    """Fetches the task list for a contest from its AtCoder tasks page.

    Returns a list of dicts with keys: id, contest_id, problem_index, name.
    Raises ValueError if the task table cannot be found on the page.
    Network/HTTP failures propagate as requests.RequestException (e.g.
    requests.HTTPError, requests.Timeout) — callers should catch that.
    """
    url = f"https://atcoder.jp/contests/{contest_id}/tasks"
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    # Parse from bytes so selectolax's own charset sniffing applies, instead of
    # trusting requests' Content-Type-derived (and sometimes absent) encoding.
    tree = HTMLParser(response.content)
    tbody = tree.css_first("tbody")

    if tbody is None:
        raise ValueError(f"No task table found on the tasks page for {contest_id}")

    tasks = []

    for row in tbody.css("tr"):
        task = _parse_row(row, contest_id)

        if task is not None:
            tasks.append(task)

    return tasks


def _parse_row(row, contest_id: str) -> dict[str, str] | None:
    cells = row.css("td")

    if len(cells) < 2:
        return None

    link = cells[0].css_first("a")

    if link is None or "href" not in link.attributes:
        return None

    match = _TASK_HREF_PATTERN.match(link.attributes["href"])

    if match is None:
        return None

    href_contest_id, task_id = match.groups()

    if href_contest_id != contest_id:
        return None

    problem_index = link.text(strip=True)
    name = cells[1].text(strip=True)

    if not problem_index or not name:
        return None

    return {
        "id": task_id,
        "contest_id": contest_id,
        "problem_index": problem_index,
        "name": name,
    }


def find_recently_finished_abc_ids(
    now: datetime | None = None, limit: int = 3
) -> list[str]:
    """Returns up to `limit` most recently finished ABC contest_ids, oldest first.

    `now` must be timezone-aware (defaults to the current UTC time).
    Network/HTTP failures propagate as requests.RequestException (e.g.
    requests.HTTPError, requests.Timeout) — callers should catch that.
    Assumes well-formed contests.json entries; a missing "id"/"start_epoch_second"/
    "duration_second" key raises KeyError.
    """
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

    if limit <= 0:
        return []

    return [contest["id"] for contest in finished_abc[-limit:]]
