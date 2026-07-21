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
        lambda token: {"ABC 467 A - Obesity"},
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
    monkeypatch.setattr(main.github_client, "existing_discussion_titles", lambda token: set())

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
    monkeypatch.setattr(main.github_client, "existing_discussion_titles", lambda token: set())

    created = []
    monkeypatch.setattr(
        main.github_client,
        "create_discussion",
        lambda token, title, body: created.append(title) or "https://example.invalid",
    )

    main.run("fake-token")  # must not raise

    assert created == ["ABC 467 A - Obesity"]


def test_run_uses_explicit_contest_id_when_given(monkeypatch):
    called_with = []
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
    monkeypatch.setattr(main.github_client, "existing_discussion_titles", lambda token: set())

    main.run("fake-token", contest_id="abc468")

    assert called_with == ["abc468"]
