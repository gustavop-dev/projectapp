### FLOW: `admin-proposal-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/`
- **Description:** View the list of all business proposals. Table includes heat score badge (1-10, color-coded), "días sin actividad" red badge for inactive proposals, WhatsApp quick-action in dropdown, and a floating metrics manual button.
- **Steps:**
  1. Admin navigates to `/panel/proposals/`.
  2. Proposals load from API (`GET /api/proposals/`) with `heat_score` per proposal.
  3. Proposal table renders with status, client, dates, 🔥 heat score column, and inactivity badges.
  4. Actions dropdown includes "Enviar por WhatsApp" with pre-filled contextual message.
  5. Floating "?" button opens the MetricsManual slide-over with searchable metric definitions.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-list.spec.js`
