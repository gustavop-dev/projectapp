### FLOW: `proposal-value-added-modules`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The "Value Added Modules" section (`section_type: value_added_modules`) renders a card grid of included-free items. Each card is resolved from the proposal's `functional_requirements` groups using `module_ids`. Cards show module title, icon, justification text, and a "Gratis" badge. An optional `footer_note` appears below the grid. Falls back to "Incluido sin costo adicional" when no `title` is set in `content_json`. Each card may carry per-module conditions (`content_json.conditions[id]`): when the proposal's effective total is below the module minimum (in the proposal currency), a "Disponible en proyectos desde $X" badge is shown ("condicionado", the module is never hidden); a duration badge ("Disponible por N meses") and a discretionary note may also appear. A "Términos y condiciones" button, placed opposite "Ver detalle", opens a per-module terms modal (`ModuleTermsModal`) without triggering the card's detail modal.
- **Steps:**
  1. Client navigates to the Value Added Modules section.
  2. Section title and intro text render.
  3. Each module card resolves its title and icon from `functional_requirements.content_json.groups`.
  4. Each card shows the justification text from `content_json.justifications`.
  5. A "Gratis" badge appears on every card.
  6. Optional `footer_note` renders at the bottom of the section.
  7. [Optional] Clicking a card opens the shared requirements modal; items with linked technical requirements show the same nested "Ver requerimientos (N)" link as `proposal-functional-requirements-modal` (pass-through covered by `test/components/ValueAddedModules.test.js`).
  8. [Optional] When a module minimum is not met, the "Disponible en proyectos desde $X" badge renders; a duration badge renders when `duration_months` is set.
  9. [Optional] Clicking "Términos y condiciones" opens the `ModuleTermsModal` with the module terms, without opening the detail modal.
- **Coverage:** ✅ Covered — `frontend/e2e/proposal/proposal-value-added-modules.spec.js` (card grid, condition badges, and terms modal)
- **Known gaps:** The terms modal now renders `**bold**` via `renderInlineBold` (2026-07) but the spec's mock terms carry no `**` markers, so bold output is unasserted. The canonical card order (admin → manual → kpi_dashboard → analytics → ai_automation, 2026-07) is not asserted either.
