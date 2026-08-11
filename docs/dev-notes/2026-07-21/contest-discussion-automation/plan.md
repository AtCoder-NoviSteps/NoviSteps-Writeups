# コンテスト議論自動投稿 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ABC (AtCoder Beginner Contest) が終了した直後に、各問題ごとの GitHub Discussion を自動作成する。

**Architecture:** NoviSteps-Writeups リポジトリ単独で完結する GitHub Actions (cron) から Python スクリプトを実行する。AtCoder の問題ページを直接スクレイピングして問題一覧を取得し、GitHub GraphQL API (`createDiscussion`) で Discussion を作成する。NoviSteps 本体 (AtCoderNoviSteps) のコード・DB・シークレットには一切触れない。

**Tech Stack:** Python 3.13 (uv管理) / requests / selectolax / pytest / responses (HTTPモック) / GitHub Actions

---

## 概要

現在、NoviSteps-Writeups の Discussion (感想・気づき投稿用) は ABC の問題ごとに手動 (または個別のアドホックな操作) で作成されている。これを自動化する。

当初案は NoviSteps 本体 (AtCoderNoviSteps) の管理画面「タスクインポート」実行時にフックする設計だったが、共同開発者のレビューで以下の指摘を受け、設計を変更した。

- 管理画面からの実行はUIから想像しづらく、テスト・デバッグの難易度が高い
- 本体アプリに GitHub 書き込み用シークレットを持たせると攻撃面が増える
- 本来のゴールは「タスクインポート時」ではなく「コンテスト終了後すぐに投稿」なので、コンテストの開催スケジュールに合わせた cron の方が目的に忠実

## 設計根拠

- **起点を Writeups リポジトリの GitHub Actions (cron) にする**: NoviSteps 本体から完全に切り離すことで、シークレット管理・テスト・デバッグが Writeups リポジトリ単独で完結する。
- **データ取得元は AtCoder の問題ページを直接スクレイピング**: 共同開発者が動作確認済みの PoC (`fetch_tasks_from_atcoder.py`) をベースにする。kenkoooo Problems API (`problems.json`) は全コンテスト分を含み巨大なため個別コンテスト取得に不向き。一方 `contests.json` は軽量なため、「終了済み最新コンテストの特定」にのみ利用する。
- **GITHUB_TOKEN (Actions 標準トークン) を使う、専用 PAT は作らない**: GitHub Actions の `permissions: discussions: write` で GraphQL `createDiscussion` mutation が実行できる。同一リポジトリ内への書き込みなので、追加のシークレット発行は不要 (Phase 1 で実際に動作検証する)。
- **Discussion タイトルは `ABC {回数} {problem_index} - {name}` 形式**: 既存の手動投稿 (`ABC 467 F - Email Scheduling Optimization` など) と一致させる。`name` は問題ページの2列目テキストをそのまま使うため、正規表現によるパースが不要。
- **重複防止はタスク単位**: 「直近 N 件の終了済み ABC」それぞれについて、Discussion タイトルが既存かどうかを個別にチェックしてから作成する。コンテスト単位 (「このコンテストは投稿済みか」) ではなく問題単位でチェックすることで、途中で失敗したコンテスト (一部の問題だけ投稿済み) も次回実行で自動的に埋められる。
- **失敗時の扱い**: 1問題分の Discussion 作成に失敗しても他の問題の処理は継続する (ログのみ記録)。

## 却下した代替案

| 案 | 却下理由 |
|---|---|
| NoviSteps 本体の管理画面タスクインポート時にフック (当初案) | UIから見えない副作用になる、本体に書き込み用シークレットを持たせる必要がある、テストの難易度が高い |
| kenkoooo Problems API (`problems.json`) から問題名を取得 | 全コンテスト分を含み巨大でAPI応答が重い。個別コンテスト取得用のエンドポイントが存在しない |
| コンテスト単位の重複チェック (「このコンテストは投稿済みか」を1回だけ判定) | 一部の問題だけ投稿に失敗した場合、次回実行で残りが永久にスキップされてしまう |
| 専用 Fine-grained PAT をリポジトリシークレットとして発行 | Actions 標準の `GITHUB_TOKEN` + `permissions: discussions: write` で足りる可能性が高く、余計なシークレット管理を増やしたくない (動作しない場合のみ Phase 1 でフォールバック) |

## ファイル構成

```
NoviSteps-Writeups/
├── pyproject.toml
├── uv.lock
├── src/
│   └── contest_discussions/
│       ├── __init__.py
│       ├── constants.py       # REPOSITORY_ID, GENERAL_CATEGORY_ID, DISCUSSION_BODY, CONTESTS_TO_CHECK
│       ├── atcoder.py         # fetch_tasks(), find_recently_finished_abc_ids()
│       ├── github_client.py   # existing_discussion_titles(), create_discussion()
│       └── main.py            # 全体のオーケストレーション + CLI エントリポイント
├── tests/
│   ├── fixtures/
│   │   └── abc467_tasks.html  # atcoder.jp のタスク表HTMLの実物サンプル (テスト用)
│   ├── test_atcoder.py
│   ├── test_github_client.py
│   └── test_main.py
└── .github/
    └── workflows/
        └── post_discussions.yml
```

## フェーズ一覧

1. [Phase 1](phase-1.md): プロジェクト初期化 + GITHUB_TOKEN の Discussion 書き込み権限を検証
2. [Phase 2](phase-2.md): `atcoder.py` — 問題一覧の取得ロジック
3. [Phase 3](phase-3.md): `atcoder.py` — 終了済み最新コンテストの判定ロジック
4. [Phase 4](phase-4.md): `github_client.py` — 既存Discussion確認・作成
5. [Phase 5](phase-5.md): `main.py` — オーケストレーション + CLI
6. [Phase 6](phase-6.md): GitHub Actions ワークフロー配線 + 手動E2E検証
7. [Phase 7](phase-7.md): リファクタサイクル (AGENTS.md 必須ステップ)

各フェーズは低リスク (ローカルで完結するテスト) から高リスク (実際にDiscussionを作成するE2E検証) の順に並べている。
