# コンテスト Discussion 自動投稿

## 目的

毎週の AtCoder Beginner Contest (ABC) 終了後、問題ごとの GitHub Discussion
を作成する。GitHub Actions の標準 `GITHUB_TOKEN` に `discussions: write`
権限を与え、Writeups リポジトリ内だけで実行する。

## スケジュール

GitHub Actions の cron は UTC で評価される。自動実行は `50 23 * * 6`
（日曜日 08:50 JST）で、コンテスト終了直後ではなく AtCoder Problems の
コンテスト情報が反映されるまでの余裕を持たせている。

## データ取得

- 終了済み ABC の特定には軽量な Problems API の `contests.json` を使う。
- 問題一覧は AtCoder のコンテスト別 tasks ページから直接取得する。
  Problems API の問題データはコンテスト終了後に遅れることがあるためである。

## 重複防止と手動 backfill

Discussion タイトル `ABC {番号} {問題記号} - {問題名}` が General カテゴリに
既に存在する場合は作成しない。通常の自動実行では最新100件だけを確認する。
`--contest-id abcNNN` で過去コンテストを手動 backfill する場合は、古い
Discussion も確認できるよう全ページを取得する。

## 障害時の扱い

個別の取得・作成失敗は残りの問題の処理を止めず、次回実行で再試行できる。
ただし、対象コンテストの取得が全件失敗した場合、または Discussion 作成を
1件以上試みて全件失敗した場合は、GitHub Actions を失敗させる。

## 実運用確認

2026-08-08 に PR ブランチから `abc464` を直接実行し、Discussion #38〜#44
の7件を作成した。同じ入力で再実行しても新規作成は発生せず、重複防止も確認した。
これは AtCoder 取得・GitHub GraphQL 作成・重複防止の E2E である。

GitHub Actions の `workflow_dispatch` による確認は、ワークフローファイルが
`main` に入った後に実施する。
