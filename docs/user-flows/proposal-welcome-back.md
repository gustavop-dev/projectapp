### FLOW: `proposal-welcome-back`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Returning client sees a welcome-back overlay with their name and last visited section. Progress is persisted in localStorage per proposal UUID.
- **Steps:**
  1. Client opens a proposal they've previously visited.
  2. On animation complete, the system checks `localStorage` for saved progress (`proposal-{uuid}-progress`).
  3. If progress exists (sectionIndex > 0), welcome-back overlay appears: "Bienvenido de nuevo, [name]. La última vez llegaste hasta [section]."
  4. Client clicks "Continuar donde lo dejé" → navigates to saved section.
  5. Client clicks "Empezar desde el inicio" → dismisses overlay.
  6. Onboarding tutorial is skipped for returning visitors.
- **Branches:**
  - [Branch A — First visit] No saved progress → normal onboarding flow.
  - [Branch B — Preview mode] Welcome-back is skipped in preview mode.
- **Coverage:** ✅ Covered — `frontend/e2e/proposal/proposal-welcome-back.spec.js`
