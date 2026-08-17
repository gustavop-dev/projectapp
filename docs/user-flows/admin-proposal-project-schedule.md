### FLOW: `admin-proposal-project-schedule`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/<id>/edit?tab=schedule`
- **Description:** Admin sets per-stage start/end dates (design, development) for an accepted proposal in the Cronograma tab, sees proportional status badges (faltan / vencida / completada), and marks stages as completed to silence deadline alerts. The daily Huey task `notify_proposal_stage_deadlines` reads these dates and emails the team a 70%-elapsed warning + every-3-day overdue reminder.
- **Steps:**
  1. Admin opens an accepted proposal via `/panel/proposals/<id>/edit`.
  2. Admin clicks the "Cronograma" tab (only visible when status is `accepted` or `finished`).
  3. Tab shows two stage cards: Diseño and Desarrollo.
  4. Admin types start_date and end_date for the Diseño stage and clicks "Guardar fechas".
  5. PUT `/api/proposals/<id>/stages/design/` succeeds; the stage card status badge updates ("Faltan X días" / "Vencida hace X días").
  6. Admin clicks "Marcar como completada" → POST `/api/proposals/<id>/stages/design/complete/` → badge becomes "🟢 Completada".
- **Branches:**
  - [Branch A — Validation] When start_date > end_date, the form shows an inline error and no request is sent.
  - [Branch B — Tab visibility] When the proposal is in `draft`/`sent`/`viewed`/`negotiating`, the Cronograma tab is hidden.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-project-schedule.spec.js`
