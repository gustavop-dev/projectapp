# PR #400 — corrección del gate de cobertura backend

## Diagnóstico

En el commit `9b0a7f35`, los 18.044 tests de CI pasaban. El único check fallido,
`backend-coverage-merge`, rechazaba una cobertura combinada de líneas y ramas
de **92,147707 %**, inferior al mínimo de **92,5 %**.

Evidencia: [ejecución del gate](https://github.com/gustavop-dev/projectapp/actions/runs/35816049806/job/107133400189),
artefacto `coverage-backend` de esa ejecución.

## Corrección

Se añaden **86 casos** sobre contratos de manifest, archivos ZIP, sintaxis,
versiones pendientes/expiradas, requisitos de imágenes, selección y publicación,
permisos de recursos, firmas de preview, capturas, clics y manifest PWA.
Las aserciones comprueban errores concretos, bytes servidos y estado persistido.

No se modifican código de producción, umbral, exclusiones ni configuración de CI.
El control de calidad estricto de los seis archivos nuevos obtiene **100/100**,
sin errores, advertencias ni sugerencias.

## Verificación local

- **86/86 casos nuevos aprobados**, en lotes de hasta 20.
- **38/38 casos existentes de Linktree aprobados**, incluidos seis con Chromium real.
- No se ejecutó la suite completa. Se utilizó `projectapp.settings_test`, SQLite y
  almacenamiento temporal. `--nomigrations` se usó en los lotes que comprueban
  comportamiento de modelos/endpoints, sin probar migraciones.
- Antes de la última regresión visual, la unión de la evidencia local y el
  artefacto original añadía 292 líneas/ramas previamente no cubiertas: una
  estimación combinada de **92,668104 %**. Es una proyección; el veredicto global
  definitivo corresponde al CI del nuevo commit.
- El primer intento de Chromium falló por bibliotecas locales ausentes. La
  repetición usó bibliotecas ya existentes mediante `LD_LIBRARY_PATH` y pasó;
  no se cambiaron las pruebas ni los paquetes del sistema para resolverlo.

Comandos de verificación, desde `backend/` del worktree
`/home/dev_env/webapps/.wt/projectapp_staging/pr400-linktree-coverage`:

```bash
COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/services/test_linktree_template_manifest.py -q --cov-append --cov-report= --tb=short
COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/services/test_linktree_template_archive.py -q --cov-append --cov-report= --tb=short
COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/services/test_linktree_template_syntax.py -q --cov-append --cov-report= --tb=short
COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/views/test_linktree_template_resources.py -q --cov-append --cov-report= --tb=short
COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/services/test_linktree_template_lifecycle.py -q --nomigrations --cov-append --cov-report= --tb=short
COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/views/test_linktree_template_publication.py -q --nomigrations --cov-append --cov-report= --tb=short
COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/services/test_linktree_template_package.py -q --cov-append --cov-report= --tb=short
COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/views/test_linktree_template_views.py -q --nomigrations --cov-append --cov-report= --tb=short
COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/services/test_linktree_template_browser.py content/tests/services/test_linktree_template_service.py -q --nomigrations --cov-append --cov-report= --tb=short
LD_LIBRARY_PATH=/home/dev_env/.cache/playwright-noble-libs/root/usr/lib/x86_64-linux-gnu COVERAGE_FILE=/tmp/pr400-local.coverage ../.venv/bin/pytest content/tests/services/test_linktree_template_browser.py -q --cov-append --cov-report= --tb=short
```

El penúltimo comando aprobó el caso de servicio y detectó las bibliotecas faltantes
en los seis casos de Chromium; el último verificó esos seis casos correctamente.

Control de calidad, desde la raíz del worktree:

```bash
python3 scripts/test_quality_gate.py --repo-root . --suite backend --semantic-rules strict --junk-severity=error --include-file backend/content/tests/services/test_linktree_template_archive.py --include-file backend/content/tests/services/test_linktree_template_manifest.py --include-file backend/content/tests/services/test_linktree_template_syntax.py --include-file backend/content/tests/services/test_linktree_template_lifecycle.py --include-file backend/content/tests/views/test_linktree_template_resources.py --include-file backend/content/tests/views/test_linktree_template_publication.py --report-path /tmp/pr400-quality-final.json
```
