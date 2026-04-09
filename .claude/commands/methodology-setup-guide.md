# Claude Compatibility Notes For ProjectApp

Legacy reference only.

ProjectApp now uses a Codex-native runtime:
- `AGENTS.md`
- scoped `AGENTS.md` files
- `.agents/skills/*`
- `.codex/config.toml`

Claude compatibility remains available through:
- `CLAUDE.md`
- scoped `CLAUDE.md` files
- `.claude/skills/*`
- `.claude/commands/*`

If you change a recurring workflow, update the native Codex skill first and mirror it into `.claude/` only when Claude users still need it.

Canonical docs:
- `docs/codex-ecosystem-methodology-guide.md`
- `docs/codex-setup.md`
