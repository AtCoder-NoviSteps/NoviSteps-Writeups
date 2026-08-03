# PR #30 Human Review Follow-up Design

## Scope

Address the human reviewer feedback for the contest-discussion automation while
preserving the already-pushed Copilot fixes. Do not trigger a live workflow or
create a GitHub Discussion as part of this work.

## Decisions

- Validate an explicitly supplied contest ID as lowercase `abc` followed by
  digits before any AtCoder or GitHub request. Automatic discovery already
  returns only ABC IDs.
- Count failed Discussion creations. If a run attempted one or more creations
  and every creation failed, raise `RuntimeError` after processing all tasks so
  GitHub Actions reports the operational failure. Partial failures remain
  non-blocking to preserve retry-on-next-run behavior.
- Run on Sunday 08:50 JST (`50 23 * * 6` in GitHub Actions' UTC-only cron) so
  `contests.json` has substantially more time to reflect the Saturday ABC.
- Pin each third-party GitHub Action to the reviewed full commit SHA and retain
  the version as a comment.
- Keep durable operational rationale in the existing automation plan: task
  data is deliberately scraped from AtCoder because Problems data can lag;
  `contests.json` is only used for contest discovery; a live E2E run remains
  pending explicit authorization.

## Testing

Add regression tests for malformed manual contest IDs and all-create-failed
runs. Validate workflow syntax/content statically and run the full Python test
suite after dependencies are available.
