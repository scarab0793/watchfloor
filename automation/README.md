# WatchFloor feed collector — staging only

This experimental collector fetches public RSS/Atom feeds and stores recent candidate headlines in `automation/candidates.json`. It does not write `index.html`, `hu.html`, translations or the live website. Candidate content is unverified and must not be presented as verified reporting.

Run locally: `python automation/collect.py`.

The workflow is intentionally pinned to the feature branch for checkout and push. GitHub scheduled workflows only run from the repository default branch, so **the twice-daily schedule is not active until explicitly deployed to main**. Use workflow_dispatch for manual testing if GitHub permits it on the branch, or test locally. Feed URLs are initial guesses and require live verification; individual feed errors are logged.

Before production: validate feeds, normalize canonical URLs, improve deduplication by headline, add source trust/claim labeling and editorial checks, then integrate the existing HTML generator. Never auto-merge this branch into main without review.
