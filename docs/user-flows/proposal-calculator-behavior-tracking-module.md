### FLOW: `proposal-calculator-behavior-tracking-module`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The investment calculator exposes `behavior_tracking_module` as a priced add-on (30% of the base investment, `default_selected: False`): first-party user behavior tracking installed in the client's own product — session/open registry, views opened + time per view (up to 15 tracked views), interest map, journey funnel with drop-off (1 main funnel), built-in behavior panel (up to 8 KPIs / 4 charts), device breakdown, and 12-month data retention with explicit exclusions (no screen recording, click heatmaps or cross-site tracking). It is the same capability the platform uses in its own proposal analytics tab, productized for clients.
- **Steps:**
  1. Client opens the calculator modal on a proposal that includes `behavior_tracking_module`.
  2. Module row renders under the bilingual label "👣 Rastreo de Comportamiento" with `+30%` pricing over the base total (e.g. base $4.000.000 COP → +$1.200.000).
  3. Client expands the module → 7 scope-closed items are listed.
  4. Selecting the module raises the effective total by base×30% and rescales payment options.
  5. In technical mode, an epic with `linked_module_ids: ["module-behavior_tracking_module"]` is hidden while the module is deselected and shown once selected (same gating as other additional modules).
- **Coverage:** ⚠️ Pending (registered, E2E spec not yet implemented; catalog data verified by `backend/content/tests/services/test_proposal_service.py` and migration tests, calculator mechanics structurally covered by `proposal-calculator-modules` / `proposal-investment-calculator`)
- **E2E Spec:** _suggested:_ `e2e/proposal/proposal-calculator-behavior-tracking-module.spec.js`
