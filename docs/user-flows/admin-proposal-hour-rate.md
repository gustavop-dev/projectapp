### FLOW: `admin-proposal-hour-rate`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit?tab=hour-rate` (Tarifa por hora tab)
- **Description:** Admin sets the hourly rate of the hour packages for one proposal. In **automático** (the default) the rate keeps syncing from the `HourPackage` catalog, so a catalog edit reaches every PDF. In **manual** the proposal carries its own base rate — and optionally a rate for an individual package — while names, hours and discounts still come from the catalog. The manual value is stored on the proposal and never touches the catalog or any other proposal.
- **Steps:**
  1. Admin opens a proposal in edit mode and selects the "Tarifa por hora" tab.
  2. The tab loads the catalog for the proposal's nationality and renders a preview of the table the PDF prints (Paquete / Horas / Dcto. / Tarifa/hora / Total).
  3. Admin switches the control to "Manual"; the rate input appears, pre-filled from the catalog.
  4. Admin types a rate; every row of the preview recalculates live (rate × (1 − discount), × hours).
  5. Optionally, admin sets a rate for a single package, which overrides the base rate for that row only.
  6. Admin clicks "Guardar" → `PATCH /api/proposals/sections/:id/update/` writes `hourPackagesMode`, `manualHourlyRate`, `manualCurrency` and `manualPackageRates` into the commercial_conditions `content_json`.
  7. The generated PDF seeds the packages from the catalog and overlays the manual rates.
- **Branches:**
  - [Branch A — Back to automatic] The manual rate is kept, not discarded; the catalog value rules while automatic is on, and re-enabling manual restores the saved rate.
  - [Branch B — No section] A proposal without the commercial_conditions section shows an empty state with a "Crear la sección" button.
  - [Branch C — Empty catalog] With no active packages for the nationality, a warning shows and the preview falls back to the snapshot stored on the proposal.
  - [Branch D — Currency changed] If the proposal's nationality changed after the manual rate was set, the tab reverts to automatic and warns, so a COP amount is never reprinted as USD.
  - [Branch E — Disabled section] If commercial_conditions is disabled, a banner warns that these packages will not reach the PDF.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-hour-rate.spec.js`
- **Unit Tests:** `test/components/SectionEditor.test.js`
- **Backend Tests:** `content/tests/views/test_section_update_views.py`
- **Known gaps:** The `commercial_conditions` and `value_added_modules` editors are not exercised by the spec; their money fields (`hourlyRate` base and per-package, `min_price_usd/cop`) now use `BaseCurrencyInput` (2026-07).
