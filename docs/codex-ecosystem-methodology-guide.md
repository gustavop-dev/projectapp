# ProjectApp Codex Methodology Guide

ProjectApp uses a Codex-native repo runtime and keeps Claude/Windsurf only as compatibility layers.

## Canonical Runtime

| Surface | Location | Purpose |
|---------|----------|---------|
| Persistent instructions | `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md` | Repo rules and scoped conventions |
| Reusable workflows | `.agents/skills/<skill>/SKILL.md` | Native project skills |
| Skill metadata | `.agents/skills/<skill>/agents/openai.yaml` | Optional display and invocation policy |
| Project config | `.codex/config.toml` | Project-scoped Codex defaults |
| Long-lived project context | `docs/methodology/*`, `tasks/*` | Memory bank and current-state docs |
| Compatibility surfaces | `CLAUDE.md`, `.claude/`, `.windsurf/` | Mixed-tool team support only |

## Mental Model
- `AGENTS.md`: persistent repo instructions.
- `SKILL.md`: reusable workflow.
- `MCP`: external systems and tools.
- `plugin`: optional packaging format for sharing skills across repos; not part of ProjectApp's day-to-day runtime.
- `automations`: scheduled Codex app tasks.
- `GitHub Action`: CI entrypoint if Codex is later added to CI.

## Project Layout

```text
projectapp/
├── AGENTS.md
├── CLAUDE.md
├── .codex/
│   └── config.toml
├── .agents/
│   └── skills/
│       ├── plan/
│       ├── implement/
│       ├── debug/
│       ├── debugme/
│       ├── methodology-setup/
│       ├── test-quality-gate/
│       ├── backend-test-coverage/
│       ├── frontend-unit-test-coverage/
│       ├── frontend-e2e-test-coverage/
│       ├── e2e-user-flows-check/
│       ├── new-feature-checklist/
│       ├── fix-broken-tests/
│       ├── git-commit/
│       ├── git-sync/
│       ├── deploy-and-check/
│       └── blog-ai-weekly/
├── backend/
│   ├── AGENTS.md
│   └── CLAUDE.md
├── frontend/
│   ├── AGENTS.md
│   └── CLAUDE.md
├── .claude/
└── .windsurf/
```

## Skill Inventory

### Canonical skills
- `plan`
- `implement`
- `debug`
- `methodology-setup`
- `test-quality-gate`
- `backend-test-coverage`
- `frontend-unit-test-coverage`
- `frontend-e2e-test-coverage`
- `e2e-user-flows-check`
- `new-feature-checklist`
- `fix-broken-tests`
- `git-commit`
- `git-sync`
- `deploy-and-check`
- `blog-ai-weekly`

### Compatibility alias
- `debugme`

### Not part of the canonical runtime
The old plugin-only aliases are intentionally not carried forward as native repo skills:
- `backend-test-coverage-goal`
- `frontend-unit-test-coverage-goal`
- `frontend-e2e-test-coverage-goal`
- `not-forget-fake-data-and-test`
- `human`

## Working Rules
1. Put durable repo rules in `AGENTS.md`, not in skills.
2. Put repeatable procedures in `.agents/skills/`.
3. Update memory files only when the task actually changes architecture, runtime guidance, or verified project context.
4. Keep Claude/Windsurf materials aligned with the Codex-native source of truth, but do not let them redefine it.
5. If the team later needs cross-repo distribution, package the existing `.agents/skills/` tree as a plugin then; do not make the plugin the runtime again.

## Daily Usage
- Planning: `Use $plan to ...`
- Implementation: `Use $implement to ...`
- Diagnosis: `Use $debug to investigate ...`
- Memory refresh: `Use $methodology-setup to refresh ...`

## Security Policy For Operational Skills
- `deploy-and-check`, `git-commit`, `git-sync`, and `blog-ai-weekly` are manual-only.
- Keep `disable-model-invocation: true` in their `SKILL.md` files.
- Keep `policy.allow_implicit_invocation: false` in their `agents/openai.yaml` files.
