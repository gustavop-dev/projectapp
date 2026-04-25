---
name: test-quality-gate
description: "Improve ProjectApp's test-quality gate by fixing the highest-value issues first with targeted test runs only."
---

# Test Quality Gate Workflow

## Rules
- Never run the full test suite.
- Read `docs/TESTING_QUALITY_STANDARDS.md` before refactoring tests.
- Prefer fixing representative fragile patterns that unlock multiple future files.
- Avoid production code changes unless test determinism genuinely requires them.

## Priorities
1. Gate-breaking errors
2. Determinism issues
3. Fragile E2E locators on core flows
4. High-value unit or integration tests
5. Warnings and style issues

## Validation Commands
- Backend: `source .venv/bin/activate && cd backend && pytest path/to/test_file.py -v`
- Frontend unit: `npm --prefix frontend test -- path/to/file.spec.js`
- Frontend E2E: `npm --prefix frontend run e2e -- path/to/spec.js`
- Gate script: `python3 scripts/test_quality_gate.py --repo-root . --report-path test-results/test-quality-report.json --frontend-unit-dir test --verbose`

## Output Contract
Provide:
- issue grouping by severity or pattern
- the first recommended phase of work
- exact targeted commands for the files you changed

---

# Test Quality Improvement Strategy (Detailed Reference)

## Goal

Create and execute a phased strategy to improve test quality by selecting a critical, meaningful subset of tests (backend + frontend) to refactor/fix first, rather than trying to fix everything.

## Non-negotiable Constraints

1. **Only run tests that were refactored or improved.** Do not run entire suites.
2. **Do not change production code** unless strictly necessary for test determinism.
3. **Do not add code comments** unless explicitly required.
4. **Prefer small, incremental changes** that reduce fragility and nondeterminism.

## Quality Standards Reference

Before refactoring any test, you **must consult**: `docs/TESTING_QUALITY_STANDARDS.md`

## Severity Levels

| Severity | Gate Impact | When to Fix |
|----------|-------------|-------------|
| **error** | Fails the gate | Phase 0-3 |
| **warning** | Lowers the score | Phase 4 |
| **info** | Style | Phase 5 |

## Selection Rules (Priority Order)

1. Tooling blockers (ESLint misconfiguration)
2. Core user journeys (auth, checkout, dashboard, documents)
3. Highest issue density files
4. Representative patterns (fix once, apply everywhere)
5. Warning-only files
6. Info/style issues

## Phases

### Phase 0 — Unblock the Gate
Fix ESLint/jest-dom rule mismatches.

### Phase 1 — Backend Determinism
Fix tests using `timezone.now` or other nondeterministic sources.

### Phase 2 — E2E Fragile Locators
Refactor critical Playwright specs to use stable locators.

### Phase 3 — High-Value Unit Tests
Refactor Jest tests with fragility/implementation coupling.

### Phase 4 — Warning Sweep
Eliminate all warning-level issues.

### Phase 5 — Info / Style Pass
Resolve all info-level findings for a clean gate report.

## Validation Commands

```bash
# Backend
pytest path/to/test_file.py

# Frontend Unit
npm test -- path/to/test_file.test.js

# Frontend E2E
npx playwright test path/to/spec.spec.js

# Quality Gate
python3 scripts/test_quality_gate.py --repo-root . --external-lint run --semantic-rules strict
```

## Deliverable

- A phased plan (Phase 0-5)
- Done conditions for each phase
- Per-phase test-run commands (only changed tests)
- Severity breakdown from initial gate run
