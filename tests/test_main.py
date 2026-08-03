import pytest

from contest_discussions import main


def test_build_title_formats_correctly():
    task = {"problem_index": "F", "name": "Email Scheduling Optimization"}
    assert main.build_title("abc467", task) == "ABC 467 F - Email Scheduling Optimization"


def test_run_skips_tasks_that_already_have_a_discussion(monkeypatch):
    monkeypatch.setattr(
        main.atcoder, "find_recently_finished_abc_ids", lambda limit: ["abc467"]
    )
    monkeypatch.setattr(
        main.atcoder,
        "fetch_tasks",
        lambda contest_id: [
            {"id": "abc467_a", "contest_id": "abc467", "problem_index": "A", "name": "Obesity"},
            {"id": "abc467_b", "contest_id": "abc467", "problem_index": "B", "name": "Keep the Change"},
        ],
    )
    monkeypatch.setattr(
        main.github_client,
        "existing_discussion_titles",
        lambda token, *, fetch_all=False: {"ABC 467 A - Obesity"},
    )
    created = []
    monkeypatch.setattr(
        main.github_client,
        "create_discussion",
        lambda token, title, body: created.append(title) or "https://example.invalid",
    )

    main.run("fake-token")

    assert created == ["ABC 467 B - Keep the Change"]


def test_run_continues_after_a_single_task_creation_failure(monkeypatch):
    monkeypatch.setattr(
        main.atcoder, "find_recently_finished_abc_ids", lambda limit: ["abc467"]
    )
    monkeypatch.setattr(
        main.atcoder,
        "fetch_tasks",
        lambda contest_id: [
            {"id": "abc467_a", "contest_id": "abc467", "problem_index": "A", "name": "Obesity"},
            {"id": "abc467_b", "contest_id": "abc467", "problem_index": "B", "name": "Keep the Change"},
        ],
    )
    monkeypatch.setattr(
        main.github_client, "existing_discussion_titles", lambda token, *, fetch_all=False: set()
    )

    created = []

    def fake_create_discussion(token, title, body):
        if title == "ABC 467 A - Obesity":
            raise RuntimeError("boom")
        created.append(title)
        return "https://example.invalid"

    monkeypatch.setattr(main.github_client, "create_discussion", fake_create_discussion)

    main.run("fake-token")  # must not raise

    assert created == ["ABC 467 B - Keep the Change"]


def test_run_continues_after_a_single_contest_fetch_failure(monkeypatch):
    monkeypatch.setattr(
        main.atcoder, "find_recently_finished_abc_ids", lambda limit: ["abc466", "abc467"]
    )

    def fake_fetch_tasks(contest_id):
        if contest_id == "abc466":
            raise ValueError("no task table")
        return [{"id": "abc467_a", "contest_id": "abc467", "problem_index": "A", "name": "Obesity"}]

    monkeypatch.setattr(main.atcoder, "fetch_tasks", fake_fetch_tasks)
    monkeypatch.setattr(
        main.github_client, "existing_discussion_titles", lambda token, *, fetch_all=False: set()
    )

    created = []
    monkeypatch.setattr(
        main.github_client,
        "create_discussion",
        lambda token, title, body: created.append(title) or "https://example.invalid",
    )

    main.run("fake-token")  # must not raise

    assert created == ["ABC 467 A - Obesity"]


def test_run_raises_when_every_contest_fails_to_fetch(monkeypatch):
    # A systemic failure (e.g. AtCoder page structure changed) must surface
    # as a failed run, not a silent no-op success.
    monkeypatch.setattr(
        main.atcoder, "find_recently_finished_abc_ids", lambda limit: ["abc466", "abc467"]
    )

    def always_fails(contest_id):
        raise ValueError("no task table")

    monkeypatch.setattr(main.atcoder, "fetch_tasks", always_fails)
    monkeypatch.setattr(
        main.github_client, "existing_discussion_titles", lambda token, *, fetch_all=False: set()
    )

    with pytest.raises(RuntimeError):
        main.run("fake-token")


def test_run_uses_explicit_contest_id_when_given(monkeypatch):
    called_with = []
    pagination_modes = []
    monkeypatch.setattr(
        main.atcoder,
        "find_recently_finished_abc_ids",
        lambda limit: (_ for _ in ()).throw(AssertionError("should not be called")),
    )
    monkeypatch.setattr(
        main.atcoder,
        "fetch_tasks",
        lambda contest_id: called_with.append(contest_id) or [],
    )
    def fake_existing_discussion_titles(token, *, fetch_all=False):
        pagination_modes.append(fetch_all)
        return set()

    monkeypatch.setattr(
        main.github_client, "existing_discussion_titles", fake_existing_discussion_titles
    )

    main.run("fake-token", contest_id="abc468")

    assert called_with == ["abc468"]
    assert pagination_modes == [True]


def test_run_skips_duplicate_title_within_the_same_run(monkeypatch):
    # A task appearing twice in one contest's fetch (e.g. a page glitch) must
    # only produce one Discussion — the second attempt should see the title
    # already added to existing_titles by the first successful creation.
    duplicated_task = {
        "id": "abc467_a",
        "contest_id": "abc467",
        "problem_index": "A",
        "name": "Obesity",
    }
    monkeypatch.setattr(
        main.atcoder, "find_recently_finished_abc_ids", lambda limit: ["abc467"]
    )
    monkeypatch.setattr(
        main.atcoder,
        "fetch_tasks",
        lambda contest_id: [duplicated_task, duplicated_task],
    )
    monkeypatch.setattr(
        main.github_client, "existing_discussion_titles", lambda token, *, fetch_all=False: set()
    )

    call_count = 0

    def fake_create_discussion(token, title, body):
        nonlocal call_count
        call_count += 1
        return "https://example.invalid"

    monkeypatch.setattr(main.github_client, "create_discussion", fake_create_discussion)

    main.run("fake-token")

    assert call_count == 1


def test_main_exits_when_github_token_missing(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("sys.argv", ["main.py"])

    with pytest.raises(SystemExit):
        main.main()


def test_main_passes_token_and_contest_id_to_run(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "env-token")
    monkeypatch.setattr("sys.argv", ["main.py", "--contest-id", "abc999"])

    captured = {}

    def fake_run(token, contest_id=None):
        captured["token"] = token
        captured["contest_id"] = contest_id

    monkeypatch.setattr(main, "run", fake_run)

    main.main()

    assert captured == {"token": "env-token", "contest_id": "abc999"}
