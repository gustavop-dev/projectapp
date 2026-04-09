# Codex Setup for ProjectApp (Quickstart)

Guia completa: `docs/codex-ecosystem-methodology-guide.md`

## 1) Superficies Codex en este repo

- Instrucciones always-on:
  - `AGENTS.md`
  - `backend/AGENTS.md`
  - `frontend/AGENTS.md`
- Registro plugin local: `.agents/plugins/marketplace.json`
- Manifest plugin: `plugins/projectapp-codex/.codex-plugin/plugin.json`
- Skills: `plugins/projectapp-codex/skills/*`

## 2) Activacion rapida

1. Abre Codex en `/home/ryzepeck/webapps/projectapp`.
2. Verifica que `.agents/plugins/marketplace.json` apunte a `./plugins/projectapp-codex`.
3. Reinicia Codex para refrescar descubrimiento de plugin y skills.

## 3) Smoke test recomendado

Ejecuta prompts cortos para validar wiring:

- `Use $plan to outline a small change in this repo.`
- `Use $debug to analyze this sample error in read-only mode.`
- `Use $methodology-setup to refresh memory files.`

## 4) Politica de seguridad para skills sensibles

En ProjectApp, skills operacionales (`deploy-and-check`, `git-commit`, `git-sync`, `blog-ai-weekly`) se restringen con:

- `disable-model-invocation: true` en `SKILL.md`
- `policy.allow_implicit_invocation: false` en `agents/openai.yaml`

## 5) Compatibilidad de ecosistema

Este repo mantiene convivencia permanente con superficies legacy:

- `.claude/`
- `.windsurf/`

La fuente operativa principal para Codex permanece en `AGENTS.md` + `plugins/projectapp-codex`.
