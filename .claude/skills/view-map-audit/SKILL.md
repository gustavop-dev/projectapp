---
name: view-map-audit
description: "Auditoría del Mapa de vistas (`/panel/views`) — verifica que `frontend/config/viewCatalog.js` esté completo y actualizado contra las páginas reales bajo `frontend/pages/`, reportando páginas huérfanas, entradas obsoletas, metadata inválida y duplicados con prioridad."
argument-hint: "[optional: section id como public-site, panel, platform, o all]"
---

# View Map Audit — Catálogo de vistas

## Goal
Verificar que el Mapa de vistas (`/panel/views`, `frontend/pages/panel/views.vue`) refleje la realidad del proyecto. La fuente de datos es `frontend/config/viewCatalog.js` (mantenido a mano) y las opciones de filtro viven en `frontend/constants/viewMapFilterOptions.js`. El skill produce un reporte priorizado de inconsistencias entre catálogo y código real, sin modificar archivos.

## Source of truth
- Catálogo: `frontend/config/viewCatalog.js` (`viewCatalogSections[]` con `views[]`).
- Sets de filtros válidos: `frontend/constants/viewMapFilterOptions.js`.
  - `audience` ∈ `{public, admin, client}`.
  - `viewType` ∈ `{list, detail, create, edit, readonly, dashboard, config, auth}`.
- Vista consumidora: `frontend/pages/panel/views.vue`.
- Composable de filtros: `frontend/composables/useViewMapFilters.js`.
- Tests focalizados:
  - `frontend/test/composables/useViewMapFilters.test.js`
  - `frontend/test/components/ViewMapFilterPanel.test.js`

## Constraints
- **Read-only.** No editar `viewCatalog.js`, `viewMapFilterOptions.js` ni ningún otro archivo durante la auditoría — solo reportar.
- Solo evidencia del repo: `frontend/pages/**/*.vue`, `viewCatalog.js`, `viewMapFilterOptions.js`. No inventar páginas ni metadata.
- Respetar reglas de testing del repo: nunca correr la suite completa, máximo 3 comandos de test por ciclo, y solo los dos tests focalizados de arriba.
- No tocar migraciones, archivos backend, ni archivos fuera del Mapa de vistas.
- Si el usuario pasa un argumento (ej. `panel`), restringir el reporte a esa sección y a las páginas bajo el prefijo equivalente.

## Workflow

### Phase 0 — Scope
1. Confirmar las rutas fuente de verdad listadas arriba. Si alguna no existe (renombrada/movida), detenerse y avisar.
2. Definir las exclusiones por defecto al enumerar páginas reales:
   - `frontend/pages/error.vue` (página de error de Nuxt).
   - Cualquier archivo cuyo nombre comience con `_` o esté bajo una carpeta `components/`.
   - Subdirectorios `pages/__tests__/` si existieran.
3. Si el usuario pasó un argumento de sección, filtrar el inventario en consecuencia.

### Phase 1 — Inventario
4. Listar todas las páginas reales:
   ```bash
   find frontend/pages -name '*.vue' -not -name '_*' | sort
   ```
5. Cargar `viewCatalogSections` desde `frontend/config/viewCatalog.js` y aplanar a una lista de entradas con su `section.id`.
6. Cargar `viewAudienceOptions` y `viewTypeOptions` desde `frontend/constants/viewMapFilterOptions.js`.

### Phase 2 — Cross-checks (8 invariantes)

| # | Invariante | Severidad |
|---|---|---|
| 1 | Toda página real tiene entrada en el catálogo (`file` coincide). | HIGH |
| 2 | Toda entrada del catálogo apunta a un `file` que existe en disco. | HIGH |
| 3 | La `url` de cada entrada concuerda con la ruta Nuxt derivada del `file` (con `[param]` → `:param`). | MEDIUM |
| 4 | `audience` está en el set válido. `viewType` está en el set válido. | MEDIUM |
| 5 | La sección asignada concuerda con el prefijo de ruta (`panel/*` ⇒ sección admin, `platform/*` ⇒ sección client, etc.). Heurística. | LOW |
| 6 | Cada entrada tiene `label`, `url`, `file`, `reference`, `audience`, `viewType` no vacíos. | MEDIUM |
| 7 | Ninguna `url` ni `file` aparece duplicada entre entradas. | HIGH |
| 8 | Las opciones de `viewMapFilterOptions.js` cubren exactamente los valores reales del catálogo (sin huérfanos en ninguna dirección). | MEDIUM |

Sugerencias de comandos:
```bash
# Listar todas las URLs/files que aparecen en el catálogo
grep -E "^\s+(url|file):\s+'" frontend/config/viewCatalog.js | sort | uniq -c | sort -rn

# Verificar existencia de cada `file` referenciado
grep -oE "file:\s*'[^']+'" frontend/config/viewCatalog.js | sed "s/file: '//;s/'//" | while read f; do
  test -f "$f" || echo "MISSING: $f"
done
```

### Phase 3 — Tests focalizados
7. Correr **solo** estos dos comandos (máx. 2 ⇒ dentro del límite del repo):
   ```bash
   npm --prefix frontend test -- test/composables/useViewMapFilters.test.js
   npm --prefix frontend test -- test/components/ViewMapFilterPanel.test.js
   ```
8. Reportar verde/rojo. Si hay fallos, incluir nombre de test y archivo, sin intentar arreglar nada (esto es una auditoría).

## Rules
- No proponer renombres masivos de archivos del proyecto: el catálogo se ajusta al código, no al revés.
- No marcar como huérfana una página que claramente es un layout o un fragmento (regla de exclusión Phase 0).
- Para el invariante #5 (asignación de sección), tratar siempre como **sugerencia humana**, no como error duro.
- Si una `url` usa `:param` y el `file` usa `[param]`, eso es **correcto** (Nuxt vs convención del catálogo). Solo reportar si el nombre del parámetro difiere.
- Considerar páginas dinámicas anidadas (`[uuid]/index.vue` ⇒ `/.../:uuid`) y rutas catch-all (`[...slug].vue`).

## Output Contract
Reporte en este orden:

1. **Resumen**
   - Páginas reales encontradas: N.
   - Entradas en catálogo: M.
   - Hallazgos por severidad: HIGH / MEDIUM / LOW.

2. **HIGH**
   - Páginas huérfanas (existen en disco, no en catálogo) — una línea por archivo, con sección sugerida.
   - Entradas obsoletas (`file` no existe) — una línea por entrada con sección y label.
   - Duplicados (`url` o `file` repetido) — agrupados.

3. **MEDIUM**
   - URL ↔ archivo desalineados.
   - `audience` o `viewType` fuera de set.
   - Campos faltantes/vacíos.
   - Filtros desalineados (opciones huérfanas o valores sin opción).

4. **LOW**
   - Secciones probablemente mal asignadas (heurístico).

5. **Estado de tests**
   - `useViewMapFilters.test.js`: ✅ / ❌ (con nombre de test si falla).
   - `ViewMapFilterPanel.test.js`: ✅ / ❌.

6. **Punch list**
   - Bullets accionables, cada uno indicando exactamente qué línea de `viewCatalog.js` o `viewMapFilterOptions.js` debe agregarse, eliminarse o corregirse. No aplicar cambios — solo enumerar.
