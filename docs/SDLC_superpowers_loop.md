# SDLC loop — Superpowers profile for this repository

This profile adapts the upstream `obra/superpowers` development methodology without changing any functional skill responsibility.

## Loop

1. **Brainstorm / frame** — read `README.md`, `AGENTS.md`, relevant ADRs/TODOs and source artifacts; write an RFC when scope crosses multiple responsibilities.
2. **Design** — state invariants, exclusions, interfaces, evidence boundaries and acceptance criteria before implementation.
3. **Plan** — decompose into reversible file-level tasks with tests and human gates.
4. **Isolated branch** — branch from synchronized `dev`; never build directly on `main`.
5. **TDD / implementation** — write or update the test with each behavior; implement the minimum code that satisfies the contract.
6. **Spec-compliance review** — compare the diff against README/AGENTS/ADR/PRD, not against convenience.
7. **Code-quality review** — inspect security, failure modes, portability, duplication and maintainability.
8. **Request for feedback** — surface product/security/evidence decisions as explicit GitHub issues or PR checklist items; do not block reversible engineering on non-blocking human questions.
9. **Correction loop** — address blocking review findings and re-run verification.
10. **Verification before completion** — run `python scripts/check_release.py`, inspect CI, then merge to `dev`. Promote `dev` to `main` only after the branch is clean and the declared human gates are understood.

## Project-specific stop conditions

Stop or keep the PR unmerged when a change would:
- make enterprise research aware of candidate offers before matching;
- auto-promote harvested claims into product truth;
- let scoring override a hard gate;
- target a person before opportunity fit;
- let the UI become a second source of scoring/recommendation truth;
- claim a skill executed when no executor ran;
- close security, evidence or Gold Set TODOs without proof.
