# Repository Workflow

## Golden rules
1) `main` is protected. No direct pushes. Work only via Pull Requests.
2) One task = one card/issue = one feature branch = one PR.
3) MVP rule: no auto-send / auto-confirm. Only DRAFT creation is allowed.
4) High-risk topics always require review (payments, bookings, cancellations, visas/sanctions, complaints, medical, policy changes).

## Branch naming
- `feat/a1-...` for feature work per card
- `fix/...` for bug fixes
- `chore/...` for repo maintenance

## PR requirements (mandatory)
- Must follow PR template: Card ID, how to verify, risk_color, requires_review, confidence.
- Keep changes scoped to the card.
- Resolve review conversations before merge.
- Squash merge preferred to keep history clean.

## Definition of Done (per card)
- Card DoD and manual test cases are satisfied.
- CI checks (when enabled) are green.
- Docs/README updated when behavior changes.

## No improvisation
If a requirement is unclear or conflicts with master prompt:
- Stop implementation
- Write a short question in the PR/issue
- Wait for approval from the lead/manager
