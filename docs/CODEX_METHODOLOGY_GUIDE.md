# ProjectApp Codex Methodology Guide

ProjectApp uses a **Codex-native repo runtime**. Claude Code and Windsurf are maintained as compatibility layers only — they must stay aligned with the Codex-native source of truth, not redefine it.

---

## Canonical Runtime

| Surface | Location | Purpose |
|---------|----------|---------|
| Persistent instructions | `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md` | Repo rules and scoped conventions |
| Reusable workflows | `.agents/skills/<skill>/SKILL.md` | Native project skills |
| Skill metadata | `.agents/skills/<skill>/agents/openai.yaml` | Display name + invocation policy |
| Project config | `.codex/config.toml` | Project-scoped Codex defaults |
| Long-lived context | `docs/methodology/*`, `tasks/*` | Memory bank and current state |
| Compatibility only | `CLAUDE.md`, `.claude/`, `.windsurf/` | Mixed-tool team support |

---

## Mental Model

| Concept | What It Is |
|---------|-----------|
| `AGENTS.md` | Persistent repo instructions — durable rules, architecture invariants, conventions |
| `SKILL.md` | Reusable workflow — a repeatable procedure an agent can invoke |
| `MCP` | External systems and tools integrated at runtime |
| `plugin` | Optional packaging format for sharing skills *across* repos (not ProjectApp's daily runtime) |
| `automations` | Scheduled Codex app tasks |
| `GitHub Action` | CI entrypoint if Codex is added to CI pipelines |

---

## Project Layout

```
projectapp/
├── AGENTS.md                    ← canonical root instructions
├── CLAUDE.md                    ← compatibility mirror
├── .codex/
│   └── config.toml              ← project-scoped Codex defaults
├── .agents/
│   └── skills/                  ← 17 native skills
│       ├── plan/
│       │   ├── SKILL.md
│       │   └── agents/openai.yaml
│       ├── implement/
│       ├── debug/
│       ├── debugme/             ← legacy alias
│       ├── methodology-setup/
│       ├── test-quality-gate/
│       ├── backend-test-coverage/
│       ├── frontend-unit-test-coverage/
│       ├── frontend-e2e-test-coverage/
│       ├── e2e-user-flows-check/
│       ├── new-feature-checklist/
│       ├── fix-broken-tests/
│       ├── human/
│       ├── git-commit/          ← manual-only
│       ├── git-sync/            ← manual-only
│       ├── deploy-and-check/    ← manual-only
│       └── blog-ai-weekly/      ← manual-only
├── backend/
│   ├── AGENTS.md
│   └── CLAUDE.md
├── frontend/
│   ├── AGENTS.md
│   └── CLAUDE.md
├── .claude/                     ← Claude Code compatibility
│   ├── settings.json
│   ├── settings.local.json
│   ├── commands/
│   └── skills/                  ← mirrors .agents/skills/
└── .windsurf/                   ← Windsurf compatibility
    ├── rules/
    └── workflows/
```

---

## Skill Inventory

### Core workflows (13)

| Skill | Trigger | Description |
|-------|---------|-------------|
| `plan` | `$plan` | Create a decision-complete implementation plan |
| `implement` | `$implement` | Execute a feature or fix using existing architecture |
| `debug` | `$debug` | Read-only diagnosis: gather evidence, rank root causes |
| `methodology-setup` | `$methodology-setup` | Initialize or refresh memory-bank files |
| `test-quality-gate` | `$test-quality-gate` | Fix highest-value test quality issues |
| `backend-test-coverage` | `$backend-test-coverage` | Reach 100% pytest coverage |
| `frontend-unit-test-coverage` | `$frontend-unit-test-coverage` | Reach 100% Jest coverage |
| `frontend-e2e-test-coverage` | `$frontend-e2e-test-coverage` | Playwright flow coverage |
| `e2e-user-flows-check` | `$e2e-user-flows-check` | Audit E2E coverage gaps |
| `new-feature-checklist` | `$new-feature-checklist` | Validate fake data and test coverage |
| `fix-broken-tests` | `$fix-broken-tests` | Fix a provided set of failing tests |
| `human` | `$human` | Respond in conversational Spanish (non-technical) |
| `debugme` | `$debugme` | Legacy alias → delegates to `$debug` |

### Manual-only operational skills (4)

These have `disable-model-invocation: true` in SKILL.md and `allow_implicit_invocation: false` in openai.yaml.

| Skill | What It Does |
|-------|-------------|
| `git-commit` | Inspect changes, generate message, commit + push |
| `git-sync` | Fetch/pull with rebase, handle dirty trees |
| `deploy-and-check` | Full production deploy: pull → build → restart → verify |
| `blog-ai-weekly` | Create bilingual AI blog post from 10 news sources |

---

## Working Rules

1. Put durable repo rules in `AGENTS.md`, not in skills.
2. Put repeatable procedures in `.agents/skills/`.
3. Update memory files only when a task actually changes architecture, runtime guidance, or verified project context. Never churn memory on routine code edits.
4. Keep Claude/Windsurf materials aligned with the Codex-native source of truth — they must not redefine it.
5. If cross-repo distribution is needed later, package the existing `.agents/skills/` tree as a plugin — do not make the plugin the runtime again.

---

## Daily Usage

```
$plan     → outline approach before coding
$implement → build or fix a feature
$debug    → diagnose a bug without touching code
$human    → explain something conversationally in Spanish
```

Full invocation pattern: `Use $<skill> to <description of task>.`

---

## Security Policy: Operational Skills

Operational skills are gated by two independent safeguards:

```yaml
# SKILL.md frontmatter
disable-model-invocation: true

# agents/openai.yaml
policy:
  allow_implicit_invocation: false
```

Both guards must be present and must never be removed without explicit user confirmation.

---

## Compatibility Surfaces (Claude Code + Windsurf)

The `.claude/` and `.windsurf/` directories are **read-only mirrors** of the Codex runtime. They must stay in sync but must not be the authoritative source.

| Codex (canonical) | Claude Code (mirror) | Windsurf (mirror) |
|-------------------|----------------------|-------------------|
| `AGENTS.md` | `CLAUDE.md` | `.windsurf/rules/` |
| `.agents/skills/<s>/SKILL.md` | `.claude/skills/<s>/SKILL.md` | `.windsurf/workflows/<s>.md` |
| `.codex/config.toml` | `.claude/settings.json` | — |

When skills are added or modified, update all three surfaces.

---

## Reference Docs

- Setup & activation: `docs/CODEX_SETUP.md`
- Migration history: `docs/CODEX_MIGRATION_MAP.md`
- Memory bank: `docs/methodology/`
- Current tasks: `tasks/active_context.md`, `tasks/tasks_plan.md`
