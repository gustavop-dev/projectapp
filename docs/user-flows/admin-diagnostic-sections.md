### FLOW: `admin-diagnostic-sections`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/diagnostics/:id/edit` (Secciones tab)
- **Description:** Admin edits each of the 8 JSON sections through typed form components. Each section has its own form (paragraphs, severity scale, 14-category findings/recommendations, radiography table, timeline day distribution, cost payment description, etc.). Edits are debounced 600 ms and PATCHed to `/sections/:id/update/`. A per-section "Restaurar contenido por defecto" action reloads from the seed. The tab header shows a **completeness indicator** (progress bar + percentage) that counts how many enabled sections have non-empty `content_json`. Raw-JSON export/import is a separate flow (`admin-diagnostic-json-export` / `admin-diagnostic-json-import`).
- **Steps:**
  1. Admin opens the Secciones tab — the completeness bar renders at the top and the 8 seeded section cards render (collapsed).
  2. Expands a section, edits its typed form (e.g., appends a finding in the Categorías section).
  3. After 600 ms of inactivity the change PATCHes; saving indicator flips to "Guardado HH:MM".
  4. Completeness percentage and color band (≥80 emerald / ≥50 amber / otherwise red) update as enabled sections gain content.
  5. A `section_updated` entry appears in the Actividad timeline.
- **Branches:**
  - [Visibility toggle] Changing `visibility` between `initial` / `final` / `both` changes what the public page shows per phase.
  - [Disable] Unchecking "Activa en la vista pública" hides the section without deleting it and removes it from the completeness denominator.
  - [Reset] "Restaurar contenido por defecto" restores the section from `content.seeds.diagnostic_template.default_sections()` via POST `/sections/:id/reset/`.
  - [Completeness indicator] Progress bar reflects `sectionsWithContent / enabledSectionsCount`; empty content + disabled sections both drop the ratio.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-sections.spec.js`
