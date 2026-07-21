# Phase 7: リファクタサイクル (AGENTS.md 必須ステップ)

**目的:** AtCoderNoviSteps の `AGENTS.md` が定める「全フェーズ完了後の必須リファクタサイクル」を実施する。

---

### Task 1: 学びの言語化

- [ ] **Step 1: 実装中に判明した非自明な制約・詰まりどころを `plan.md` に追記する**

例: `GITHUB_TOKEN` の `discussions: write` 権限が実際に機能したか / しなかったか (Phase 1 の検証結果)、AtCoderのページ構造で PoC と異なった点、など。

- [ ] **Step 2: 残タスクがあれば `plan.md` に書く**

例: `CONTESTS_TO_CHECK` の値が実運用で適切だったか、cron時刻の調整が必要かどうか。

---

### Task 2: phase-N.md の破棄

- [ ] **Step 1: phase-1.md 〜 phase-7.md を削除**

```bash
git rm docs/dev-notes/2026-07-21/contest-discussion-automation/phase-*.md
git commit -m "docs: discard phase files after implementation"
```

---

### Task 3: CodeRabbit レビュー (実施可能な場合のみ)

**注記:** `coderabbit review --plain` は通常PRに対して実行する。このリポジトリは今回が最初のPRになる可能性が高く、CodeRabbit が未連携の場合は本タスクをスキップし、その旨を `plan.md` に記録する。

- [ ] **Step 1: PRを作成後、実行**

```bash
coderabbit review --plain
```

- [ ] **Step 2: `critical` / `high` / `potential_issue` (medium) の指摘を `plan.md` の `## CodeRabbit Findings` セクションに転記する**

- [ ] **Step 3: どの指摘を直すかはユーザーが判断する。ここでは一方的に直さない。**

`nitpick` レベルの指摘はPRのCIに任せる。
