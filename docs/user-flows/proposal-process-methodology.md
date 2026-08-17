### FLOW: `proposal-process-methodology`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** New "Proceso y Metodología" section with a 5-step visual pipeline (Discovery → Diseño → Desarrollo → QA → Lanzamiento). Horizontal on desktop, vertical timeline on mobile. Each step shows icon, title, description, and optional "Tu aporte" client action tag.
- **Steps:**
  1. Client navigates to the Process & Methodology section.
  2. Section renders with intro text and 5-step pipeline.
  3. Active steps are highlighted with green styling.
  4. Client action tags indicate what input the client provides at each stage.
- **Coverage:** ✅ Covered — `frontend/e2e/proposal/proposal-process-methodology.spec.js`
