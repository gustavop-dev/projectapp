### FLOW: `proposal-summary-kpis`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The Proposal Summary section displays personalized KPI cards at the top, sourced from `content_json.kpis`. Each KPI shows a value, label, and source citation. KPIs are editable in the admin SectionEditor and included in the JSON template.
- **Steps:**
  1. Client navigates to the Proposal Summary section.
  2. KPI cards render from `content.kpis` array with value, label, and source.
  3. Below KPIs, standard summary cards (investment, timeline, etc.) render.
  4. Admin can add/edit/remove KPIs in the SectionEditor for proposal_summary.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-summary-kpis.spec.js`
