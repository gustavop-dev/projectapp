# Claude Compatibility Notes For ProjectApp

Legacy reference only.

The canonical runtime for this repo is Codex-native:
- `AGENTS.md`
- `backend/AGENTS.md`
- `frontend/AGENTS.md`
- `.agents/skills/*`
- `.codex/config.toml`

## Claude Surfaces Kept For Compatibility
- `CLAUDE.md`
- `backend/CLAUDE.md`
- `frontend/CLAUDE.md`
- `.claude/skills/*`
- `.claude/commands/*`
- `.claude/settings*.json`

## Maintenance Rule
If a reusable workflow changes:
1. update the native Codex skill in `.agents/skills/` first
2. mirror the change into `.claude/` only if Claude users still rely on it
3. do not reintroduce plugin-first Codex docs or treat `CLAUDE.md` as the source of truth

## Naming Rule
- Codex canonical diagnosis workflow: `debug`
- Legacy alias still tolerated: `debugme`

For active Codex usage, see `docs/CODEX_METHODOLOGY_GUIDE.md`, `docs/CODEX_SETUP.md`, and `docs/CODEX_MIGRATION_MAP.md`.
