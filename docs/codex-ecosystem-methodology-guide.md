# Methodology Setup and Documentation Project Guide — Codex Ecosystem

Guia para implementar el sistema de Memory Bank en Codex, manteniendo interoperabilidad con Claude Code y Windsurf cuando el repositorio lo requiera.

---

## Que es el Memory Bank en Codex

Un sistema de documentacion persistente para mantener contexto del proyecto entre sesiones y agentes, con 3 workflows base:

- **Plan** -> `$plan` (planificacion con clarificacion y validacion)
- **Implement** -> `$implement` (implementacion iterativa con analisis de dependencias y pruebas)
- **Debug** -> `$debug` (diagnostico read-only con recomendacion de fix)

---

## Superficies de ejecucion en Codex

| Capa | Superficie | Proposito |
|------|------------|-----------|
| Instrucciones always-on | `AGENTS.md` (raiz), `backend/AGENTS.md`, `frontend/AGENTS.md` | Reglas de proyecto y estandares por contexto |
| Registro de plugins | `.agents/plugins/marketplace.json` | Descubrimiento de plugin repo-local |
| Manifest del plugin | `plugins/<plugin-name>/.codex-plugin/plugin.json` | Metadatos del plugin y ruta de skills |
| Workflows invocables | `plugins/<plugin-name>/skills/<skill>/SKILL.md` | Definicion del workflow |
| Politica por skill | `plugins/<plugin-name>/skills/<skill>/agents/openai.yaml` | Control de invocacion implicita y metadatos del agente |

Para ProjectApp:

- Plugin: `projectapp-codex`
- Ruta skills: `plugins/projectapp-codex/skills/`

---

## Diferencias clave vs Windsurf y Claude

| Concepto | Windsurf | Claude Code | Codex Ecosystem |
|----------|----------|-------------|-----------------|
| Reglas always-on | `.windsurf/rules/*.md` | `CLAUDE.md` por scope | `AGENTS.md` por scope |
| Workflows invocables | `.windsurf/workflows/*.md` | `.claude/skills/*/SKILL.md` | `plugins/<plugin>/skills/*/SKILL.md` |
| Registro de extension | N/A | N/A | `.agents/plugins/marketplace.json` |
| Politica de invocacion sensible | `auto_execution_mode` (legacy) | `disable-model-invocation` | `disable-model-invocation` + `policy.allow_implicit_invocation: false` |
| Datos de metodologia | `.windsurf/rules/methodology/` | `docs/methodology/` y `tasks/` | `docs/methodology/` y `tasks/` |

---

## Skills vs comandos legacy

En un ecosistema Codex:

- **Canonico**: workflows en plugin (`plugins/.../skills/...`).
- **Compatibilidad**: se pueden conservar `.claude/` y `.windsurf/` para otros clientes.
- **Convivencia permanente**: no se elimina legacy si el equipo depende de toolchains mixtos.

En ProjectApp, `debug` es el nombre principal; `debugme` se mantiene como alias legacy.

---

## Paso 1: Crear estructura base

```bash
# Memory Bank data
mkdir -p docs/methodology
mkdir -p docs/literature
mkdir -p tasks/rfc

# Codex plugin surfaces
mkdir -p .agents/plugins
mkdir -p plugins/<plugin-name>/.codex-plugin
mkdir -p plugins/<plugin-name>/skills
```

---

## Paso 2: Definir AGENTS always-on (3 niveles)

Codex carga instrucciones por alcance. Definir:

- `AGENTS.md` (raiz)
- `backend/AGENTS.md`
- `frontend/AGENTS.md`

### Secciones minimas recomendadas para AGENTS raiz

```markdown
# <Project> — Codex AGENTS Configuration

## Project Identity
## General Rules
## Security Rules — OWASP / Secrets / Input Validation
## Memory Bank System
## Directory Structure
## Testing Rules
## Lessons Learned — <Project>
## Error Documentation — <Project>
```

`backend/AGENTS.md` y `frontend/AGENTS.md` deben contener reglas tecnicas especificas del stack y testing de cada capa.

---

## Paso 3: Registrar plugin local en Codex

Crear/actualizar `.agents/plugins/marketplace.json`:

```json
{
  "name": "local-marketplace",
  "plugins": [
    {
      "name": "<plugin-name>",
      "source": {
        "source": "local",
        "path": "./plugins/<plugin-name>"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Coding"
    }
  ]
}
```

Crear/actualizar `plugins/<plugin-name>/.codex-plugin/plugin.json`:

```json
{
  "name": "<plugin-name>",
  "version": "0.1.0",
  "skills": "./skills/"
}
```

---

## Paso 4: Crear skills en el plugin

Ruta estandar:

`plugins/<plugin-name>/skills/<nombre-skill>/SKILL.md`

### 4.1 Skills base recomendados (metodologia y calidad)

- `plan`
- `implement`
- `debug` (canonico)
- `methodology-setup`
- `test-quality-gate`
- `backend-test-coverage`
- `frontend-unit-test-coverage`
- `frontend-e2e-test-coverage`
- `e2e-user-flows-check`
- `new-feature-checklist`
- `fix-broken-tests`

### 4.2 Skills operacionales (manual-only)

- `git-commit`
- `git-sync`
- `deploy-and-check`
- Skills productivos especiales (ejemplo: `blog-ai-weekly`)

### 4.3 Skills de compatibilidad (opcional)

Solo si necesitas interoperar con nomenclaturas legacy:

- `debugme` (alias de `debug`)
- `*-goal` aliases de cobertura
- Otros aliases heredados de Windsurf/Claude

---

## Formato de SKILL.md y politicas de seguridad

### Frontmatter recomendado

```yaml
---
name: debug
description: "Debug read-only workflow for runtime errors and unexpected behavior."
argument-hint: "[error message or stack trace]"
disable-model-invocation: true
allowed-tools: Bash
---
```

`disable-model-invocation: true` es obligatorio para workflows peligrosos (deploy, git, publicaciones).

### Politica de agente por skill

Archivo: `plugins/<plugin-name>/skills/<skill>/agents/openai.yaml`

```yaml
interface:
  display_name: "Deploy and Check"
  short_description: "Help with deploy tasks"

policy:
  allow_implicit_invocation: false
```

Para skills sensibles, recomienda usar ambos controles:

- `disable-model-invocation: true` en `SKILL.md`
- `allow_implicit_invocation: false` en `agents/openai.yaml`

---

## Paso 5: Inicializar Memory Files

Invocar workflow de setup:

```text
Use $methodology-setup to initialize or refresh the memory bank files.
```

Debe crear o refrescar estos 7 archivos core:

1. `docs/methodology/product_requirement_docs.md`
2. `docs/methodology/technical.md`
3. `docs/methodology/architecture.md`
4. `tasks/tasks_plan.md`
5. `tasks/active_context.md`
6. `docs/methodology/error-documentation.md`
7. `docs/methodology/lessons-learned.md`

---

## Paso 6: Verificar y corregir

Checklist posterior al setup:

- La arquitectura descrita coincide con el codebase real.
- El stack tecnico incluye versiones relevantes.
- Los requisitos reflejan el producto actual.
- Los conteos de modelos/componentes/tests son correctos.
- `active_context.md` y `tasks_plan.md` quedaron actualizados.

---

## Estructura final recomendada

```text
tu-proyecto/
├── AGENTS.md
├── backend/AGENTS.md
├── frontend/AGENTS.md
│
├── .agents/
│   └── plugins/
│       └── marketplace.json
│
├── plugins/
│   └── <plugin-name>/
│       ├── .codex-plugin/plugin.json
│       ├── agents/openai.yaml
│       └── skills/
│           ├── plan/SKILL.md
│           ├── implement/SKILL.md
│           ├── debug/SKILL.md
│           ├── methodology-setup/SKILL.md
│           └── ...
│
├── docs/
│   ├── methodology/
│   │   ├── architecture.md
│   │   ├── technical.md
│   │   ├── product_requirement_docs.md
│   │   ├── error-documentation.md
│   │   └── lessons-learned.md
│   └── literature/
│
├── tasks/
│   ├── rfc/
│   ├── active_context.md
│   └── tasks_plan.md
│
├── .claude/      # compatibilidad opcional
└── .windsurf/    # compatibilidad opcional
```

---

## Uso diario de workflows en Codex

Planificar:

```text
Use $plan to design [feature/problem].
```

Implementar:

```text
Use $implement to build [specific change].
```

Debug read-only:

```text
Use $debug to diagnose this error: [stack trace].
```

Actualizar memoria:

```text
update memory files
```

Operaciones sensibles (manuales):

```text
Use $git-commit
Use $deploy-and-check
```

---

## Inventario ProjectApp (estado actual)

Skills canonicos de ProjectApp en `plugins/projectapp-codex/skills/`:

- Base: `plan`, `implement`, `debug`, `methodology-setup`
- Calidad/testing: `test-quality-gate`, `backend-test-coverage`, `frontend-unit-test-coverage`, `frontend-e2e-test-coverage`, `e2e-user-flows-check`, `new-feature-checklist`, `fix-broken-tests`
- Operacionales: `git-commit`, `git-sync`, `deploy-and-check`, `blog-ai-weekly`
- Adicionales: `human`
- Alias legacy: `debugme`, `backend-test-coverage-goal`, `frontend-unit-test-coverage-goal`, `frontend-e2e-test-coverage-goal`, `not-forget-fake-data-and-test`

---

## Tips importantes

1. `tasks/active_context.md` es el archivo de continuidad principal entre sesiones.
2. `docs/methodology/error-documentation.md` debe crecer con cada incidente resuelto.
3. Define un nombre canonico por workflow y mantén aliases solo por compatibilidad.
4. Para skills sensibles, aplica doble bloqueo (`disable-model-invocation` + `allow_implicit_invocation: false`).
5. Mantener `.claude/` y `.windsurf/` es valido en ecosistemas mixtos; evita duplicar la fuente de verdad operativa.

