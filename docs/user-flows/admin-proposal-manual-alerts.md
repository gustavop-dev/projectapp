### FLOW: `admin-proposal-manual-alerts`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/proposals/`
- **Description:** Create, view, and dismiss manual seller alerts/reminders for proposals. Auto-alerts now include: seller_inactive (🏷️ no follow-up >3d), zombie (💀 sent >7d, no views, no activity), late_return (🔄 client returned after ≥5d gap).
- **Steps:**
  1. Admin navigates to `/panel/proposals/`.
  2. Alerts panel shows auto-alerts (not_viewed, not_responded, expiring_soon, seller_inactive, zombie, late_return) merged with manual alerts from API (`GET /api/proposals/alerts/`).
  3. Each alert type has a distinct icon (👁️‍🗨️, ⏳, 🔥, 🏷️, 💀, 🔄).
  4. Admin clicks "+ Crear recordatorio" to open the create alert form.
  5. Admin selects a proposal, alert type (reminder/followup/call/meeting/custom), date, and message.
  6. Admin submits → API call to `POST /api/proposals/alerts/create/`.
  7. New alert appears in the panel with dismiss (✕) button.
  8. Admin clicks ✕ → API call to `PATCH /api/proposals/alerts/:id/dismiss/` → alert removed from list.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-proposal-manual-alerts.spec.js`
