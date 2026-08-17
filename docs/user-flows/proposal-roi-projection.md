### FLOW: `proposal-roi-projection`

- **Module:** proposal
- **Role:** guest (via shared UUID link); admin (edits via SectionEditor)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** ROI Projection / Business Outcomes section. Renders configurable KPI cards (visualizations/day, ad reach, MRR, payback, year-1 revenue) and per-scenario blocks (Conservative / Realistic / Optimistic) with metric rows and an emphasis flag for totals; closes with an optional CTA note. The section sits at `order=4`, between `conversion_strategy` and `investment`, so the sponsor sees quantified business outcomes BEFORE the price ask. The section is **web-only** — it has no PDF renderer (sections without a renderer are silently skipped). Migration 0118 backfilled an empty disabled row in every existing proposal so admins can enable + populate per-proposal without breaking legacy flows.
- **Steps:**
  1. Client opens `/proposal/:uuid` and selects "Propuesta Completa" in the gateway.
  2. Client navigates past `greeting`, `executive_summary`, `context_diagnostic`, `conversion_strategy` panels.
  3. ROI Projection panel renders if the section's `is_enabled=true`.
  4. KPI cards display value, label, optional sublabel, and source citation.
  5. Scenarios block lists each scenario with metric rows; metrics with `emphasis=true` get bolded total styling.
  6. CTA note (if any) renders inside a primary-tinted banner closing the section.
- **Branches:**
  - [Branch A — Disabled section] When `is_enabled=false`, the panel is filtered out of `displayPanels` (regression-tested for the 31 legacy proposals that received the row via migration 0118).
  - [Branch B — Empty arrays] When `kpis` and `scenarios` are empty, only header/subtitle/CTA render without breaking the layout.
  - [Branch C — Admin edit] Admin form in `SectionEditor.vue` lets admins drag-reorder KPIs and scenarios; round-trip JSON persistence is validated by `test/components/admin-sectionEditorUtils-roi.test.js`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-roi-projection.spec.js`
- **Unit Tests:** `test/components/admin-sectionEditorUtils-roi.test.js`, `test/composables/useLinkify-html-escape.test.js`
- **Backend Tests:** `content/tests/test_roi_projection.py`
