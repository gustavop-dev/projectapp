# Codex Setup For ProjectApp

Full guide: `docs/CODEX_METHODOLOGY_GUIDE.md`

## Runtime Surfaces
- Always-on instructions:
  - `AGENTS.md`
  - `backend/AGENTS.md`
  - `frontend/AGENTS.md`
- Native repo skills: `.agents/skills/*`
- Project config: `.codex/config.toml`
- Deep project context: `docs/methodology/*` and `tasks/*`
- Compatibility-only surfaces: `CLAUDE.md`, `backend/CLAUDE.md`, `frontend/CLAUDE.md`, `.claude/`, `.windsurf/`

## Activation
1. Open Codex at `/home/ryzepeck/webapps/projectapp`.
2. Confirm the repo has `.agents/skills/` and `.codex/config.toml`.
3. Restart Codex if you added or renamed repo skills during this session.

## Smoke Test
- `Use $plan to outline a small change in this repo.`
- `Use $debug to diagnose this sample error in read-only mode.`
- `Use $methodology-setup to refresh the runtime docs after a structural change.`

## Manual-Only Skills
Operational workflows stay manual-only:
- `deploy-and-check`
- `git-commit`
- `git-sync`
- `blog-ai-weekly`

Their `SKILL.md` frontmatter keeps `disable-model-invocation: true`, and their `agents/openai.yaml` keeps `policy.allow_implicit_invocation: false`.

## Notes
- `debug` is the canonical diagnosis workflow.
- `debugme` remains as a legacy alias for compatibility.
- This repo no longer depends on a repo-local Codex plugin registry or plugin manifest for normal Codex use.
