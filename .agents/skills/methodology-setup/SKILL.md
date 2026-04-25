---
name: methodology-setup
description: "Initialize or refresh ProjectApp memory-bank files when the user asks for it or when verified repo/runtime guidance has drifted after major changes."
---

# Methodology Setup / Refresh

## When To Use
- The user explicitly asks to update memory files.
- Project structure, runtime surfaces, or recurring workflow guidance changed materially.
- The existing memory files are obviously stale and the task requires refreshing them.

## Workflow
1. Read the current memory files before changing them.
2. Inspect the real codebase and count or verify only the facts you update.
3. Update only the relevant memory files; do not churn unrelated sections.
4. Keep runtime guidance aligned with the actual repo layout:
   - `AGENTS.md` scopes
   - `.agents/skills/*`
   - `.codex/config.toml`
   - compatibility surfaces under `.claude/` and `.windsurf/` when they matter

## Core Files
- `docs/methodology/product_requirement_docs.md`
- `docs/methodology/technical.md`
- `docs/methodology/architecture.md`
- `docs/methodology/error-documentation.md`
- `docs/methodology/lessons-learned.md`
- `tasks/tasks_plan.md`
- `tasks/active_context.md`

---

## When to Use (Extended Reference)

- **New project**: First-time setup of the Memory Bank system
- **Refresh**: After major feature additions, when counts drift, or after methodology updates

## Step 1: Ensure Directory Structure

```bash
mkdir -p docs/methodology
mkdir -p docs/literature
mkdir -p tasks/rfc
```

## Step 2: Deep-Dive Codebase

Run verification commands to get exact counts:

```bash
# Models
find backend/ -name "*.py" -path "*/models*" ! -name "__init__.py" -not -path "*/venv/*" | wc -l

# Components
find frontend/components/ -name "*.vue" | wc -l

# Pages
find frontend/pages/ -name "*.vue" | wc -l

# Stores
find frontend/stores/ -name "*.js" ! -path "*/services/*" | wc -l

# Composables
find frontend/composables/ -name "*.js" | wc -l

# Backend tests
find backend/ -name "test_*.py" -not -path "*/venv/*" | wc -l

# Frontend unit tests
find frontend/test/ -name "*.spec.*" -o -name "*.test.*" | wc -l

# E2E tests
find frontend/e2e/ -name "*.spec.*" | wc -l

# URL patterns
grep -c "path(" backend/content/urls.py
grep -c "path(" backend/accounts/urls.py 2>/dev/null

# Service file sizes
ls -la backend/content/services/
```

## Step 3: Create / Refresh Memory Files

Update or create the 7 core memory files with verified data:

| # | File | Content |
|---|------|---------|
| 1 | `docs/methodology/product_requirement_docs.md` | PRD: overview, problems, features, users, business rules |
| 2 | `docs/methodology/technical.md` | Stack versions, dev setup, env config, design patterns, testing strategy |
| 3 | `docs/methodology/architecture.md` | Mermaid diagrams: system overview, request flow, ER diagram, deployment |
| 4 | `tasks/tasks_plan.md` | Feature status, known issues, testing status with exact counts |
| 5 | `tasks/active_context.md` | Current state, recent focus, active decisions, next steps |
| 6 | `docs/methodology/error-documentation.md` | Error tracking |
| 7 | `docs/methodology/lessons-learned.md` | Architecture patterns, code conventions, deployment, testing insights |

## Step 4: Cross-Reference

Verify every claim matches the codebase:
- Model counts match `find` output
- Component/page/store counts match
- Test file counts match
- FK relationships match model source code
- URL pattern counts match

Fix any discrepancies found.
