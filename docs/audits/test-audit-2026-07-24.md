# Test Audit — ProjectApp — 2026-07-24 (QA Campaign Round 8)

**Verdict: 🟡 The corpus has no safely-removable tests — the surviving junk is all REWRITE-class.**
Both operator-approved safe-cleanup batches (DELETE no-subject, MERGE exact duplicates)
came back **empty on inspection**, so **no test was deleted or merged**. The real debt —
~630 warning-level junk findings and 110 flows covered only by junk or not at all — is a
rewrite/rename effort, deliberately deferred to Round 9.

- **Scope**: Audit + safe cleanup (operator choice). `new-feature-checklist` applied as
  the rubric only. Report-first; the two cleanup batches were bounded to their two classes.
- **Branch**: `test/24072026-qa-campaign-round-8` (fresh off `main`, which already carries #124).
- **Tooling**: `scripts/test_quality_gate.py --semantic-rules strict` per suite +
  `scripts/flow_coverage_audit.py`. **AST bridge available** — `@babel/parser` was
  reinstalled (`npm ci`) before the frontend runs, so AST-based rules ran (not skipped).
- **First-ever run**: no prior `docs/audits/test-audit-*.md` existed.

---

## 1. Inventory (whole corpus)

| Suite | Files | Tests | Gate errors | Gate warnings | Info | Score |
|---|---:|---:|---:|---:|---:|---:|
| backend `content` | 185 | 3,883 | 0 | 1 | 440 | 99 |
| backend `accounts` | 67 | 1,153 | **72** | 59 | 243 | 91 |
| backend `projectapp` | 2 | 30 | 3 | 5 | 12 | 81 |
| backend `tests/` (top-level) | 2 | 67 | — | — | — | *(not app-scoped; unscanned)* |
| frontend unit (Jest) | 373 | ~4,694 | 0 | 295 | 0 | 99 |
| frontend E2E (Playwright) | 218 | ~966 | 0 | 566 | 37 | 83 |
| **Total** | **~847** | **~10,793** | **75** | **921** | **732** | — |

**Flow coverage** (`flow_coverage_audit.py`, reads `flow-definitions.json` = 299 flows):

| covered | partial | junk-only | missing | declaring `outcomes` |
|---:|---:|---:|---:|---:|
| 189 | 0 | **72** | 38 | **0 / 299** |

Also: 2 undeclared-but-tagged flows (`admin-proposal-activity-log`, `doc`), 1 untagged test,
and 8 modules declaring only `success` (no error/failure flow).

---

## 2. Class breakdown (test-audit's 7 classes)

| # | Class | Gate signal | Count | Default verdict | This round |
|---|---|---|---:|---|---|
| 1 | No interaction | `no_user_interaction` | 301 (E2E) | REWRITE | **deferred** |
| 2 | Lying tag | `flow_tag_mismatch` | 168 (E2E) | REWRITE | **deferred** |
| 3 | Weak assertion | `weak_assertion` 164 + `no_data_assertion` 43 + `tautological_selector` 1 | 208 | REWRITE | **deferred** |
| 4 | Duplicate | `duplicate_coverage` | 147 | MERGE | **0 merged** — see §3 |
| 5 | Tests the mock | `unverified_mock` 53 + `mock_call_contract_only` 14 | 67 (backend) | REWRITE | **deferred** |
| 6 | Implementation-coupled | `fragile_locator` 37 (+ `implementation_coupling` 0) | 37 (E2E) | REWRITE | **deferred** |
| 7 | No subject | *(no gate rule; barrels/constants/re-exports)* | **0** | DELETE | **empty** — see §3 |

**Structural findings outside the 7 classes** (backend, mostly `accounts`): `misplaced_file`
69 (67 accounts + 2 projectapp), `no_assertions` 4, `forbidden_token` 2, plus info-level
`missing_docstring` ~536, `test_too_short` 86, `too_many_assertions` 30, `test_too_long` 15,
`global_state_leak` 44, `nondeterministic` 10, `inline_payload` 15, `network_dependency` 2.

---

## 3. Triage of the two approved cleanup classes

### Class 4 — `duplicate_coverage` (147) → **0 mergeable**
The detector matches on **test name + structural shape, blind to the enclosing `describe`**.
Split precisely:

- **115 same-file** findings are the *same generic name* in **different** `describe` blocks —
  i.e. different subjects. Examples:
  - `stores/proposals.test.js` (51): `"handles error"` at L284/L306/L486/L539 belong to
    `fetchProposals` / `fetchProposal` / `updateProposal` / `deleteProposal` — four distinct
    actions. Merging deletes real coverage.
  - `composables/useDiagnosticPrompt.test.js` (8): the two describe blocks test **different
    composables** (`useDiagnosticCommercialPrompt` w/ `COMMERCIAL_KEY` vs
    `useDiagnosticTechnicalPrompt` w/ `TECHNICAL_KEY`).
  → **Verdict: RENAME to single-purpose names, not merge. Deferred (rewrite scope).**
- **32 cross-file** findings are structurally identical tests for **different components**
  (`DiagnosticPricingForm`↔`DiagnosticRadiographyForm`, `PrivacyPolicy`↔`TermsAndConditions`,
  `ViewMapFilterPanel`↔`ClientFilterPanel`). → **Verdict: KEEP (parallel coverage).**
- **True same-describe duplicates (identical body, same context): 0.**

### Class 7 — no-subject → **0 candidates**
No unit test targets a pure barrel/`index`/`constants`/re-export module, and no test file is
dominated by export-existence assertions (`toBeDefined`/`typeof`). Nothing to delete.

**Net: the destructive cleanup is a verified no-op.** This is the correct, evidence-backed
outcome — it confirms the corpus has no dead or duplicate tests, only tests that need
*strengthening/renaming*.

---

## 4. Coverage before/after

No tests were deleted or merged, so **coverage is unchanged** from the pre-audit baseline
(latest green `main` run `30061798461`, commit `1839a4a6` = #124). Enforced CI floors remain
the meaningful bound: backend `--cov-fail-under=92.5`; frontend statements ≥85 / branches ≥81
(`.github/workflows/ci.yml`). Flow coverage is likewise unchanged (189/299 qualifying).

---

## 5. Notable systemic findings

1. **CI gate scans only the `content` backend app.** `.testquality.yml` sets
   `backend_app_name: content` and `test-quality-gate.yml` passes no `--backend-app`, so the
   **72 error-level findings in `accounts`** (67 `misplaced_file` — tests outside the
   `models/services/views/…` folders in `py_allowed_folders`) and 3 in `projectapp` are
   **invisible to CI**. They only surface when the gate is run per-app.
2. **`duplicate_coverage` is a naming signal here, not duplication.** See §3. A campaign
   metric reading "146 duplicate unit tests" overstates deletable debt by ~100%.
3. **Flow schema migration pending.** 0 / 299 flows declare an explicit `outcomes` list, so
   `flow_coverage_audit.py` currently credits a flow on `success` alone; the
   `success/error/failure/display` model isn't yet in `flow-definitions.json`.
4. **Artifact divergence.** `docs/USER_FLOW_MAP.md` (v2.33, 173 documented flows) and
   `frontend/e2e/flow-definitions.json` (v2.60, 299 declared) are versioned independently and
   diverge in count.
5. **This corpus is the `test-audit` skill's own example.** The skill's motivating table
   (301 no-interaction E2E / 72 junk-only flows / 146 duplicate unit / 164 weak assertions)
   reproduces exactly here — the detectors are firing correctly.

---

## 6. Deferred follow-ups (Round 9 candidates), by leverage

1. **72 junk-only flows** — flows that report green but are covered only by
   `no_user_interaction` / `flow_tag_mismatch` tests. Highest leverage: they are actively
   misleading. Rewrite the E2E specs to perform real interaction + a data assertion.
2. **301 no-interaction + 168 lying-tag E2E tests** — rewrite to drive the UI and assert
   outcome; add `@outcome:` tags.
3. **115 non-single-purpose unit test names** — rename (prefix with the action/composable)
   so `duplicate_coverage` clears without losing coverage.
4. **208 weak/no-data assertions** (164 weak + 43 no-data + 1 tautological) — strengthen to
   value assertions.
5. **69 `misplaced_file` + 4 `no_assertions` + 2 `forbidden_token` in `accounts`/`projectapp`**
   — reorganize into `py_allowed_folders`, add assertions, rename; and consider gating these
   apps in CI (add `--backend-app accounts`/`projectapp` steps) so the debt can't regrow unseen.
6. **67 mock-only / 37 fragile-locator** — assert observable outcomes instead of spy calls;
   replace brittle locators with role/scoped locators.
7. **Flow hygiene** — migrate `flow-definitions.json` to explicit `outcomes`; reconcile it
   with `USER_FLOW_MAP.md`; resolve the 2 undeclared flows and 1 untagged test.

---

## 7. Method / reproducibility

```bash
# per-suite gate (backend once per app; frontend needs @babel/parser present)
python3 scripts/test_quality_gate.py --repo-root . --semantic-rules strict --suite backend --backend-app content
python3 scripts/test_quality_gate.py --repo-root . --semantic-rules strict --suite backend --backend-app accounts
python3 scripts/test_quality_gate.py --repo-root . --semantic-rules strict --suite backend --backend-app projectapp
python3 scripts/test_quality_gate.py --repo-root . --semantic-rules strict --suite frontend-unit
python3 scripts/test_quality_gate.py --repo-root . --semantic-rules strict --suite frontend-e2e
python3 scripts/flow_coverage_audit.py --repo-root . --json test-results/flow-audit.json
```

Note: the coverage skills document the gate's file-scope flag as `--files`, which does not
exist — the correct flag is `--include-file` (repeatable) / `--include-glob`.
