### FLOW: `admin-diagnostic-analytics`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/diagnostics/:id/edit` (Analytics tab)
- **Description:** Admin reviews full analytics dashboard at parity with proposal analytics: engagement score (0–100 color-coded), 6 summary KPI cards (total views, unique sessions, first view, reading time, coverage %, last visit), global comparison (3 metrics with ↑↓ arrows), funnel with drop-off % per section, device breakdown (desktop/mobile/tablet via user-agent), suggested actions (heuristic), skipped sections warning, section interest heatmap + top-2 insights, section engagement table, activity timeline (DiagnosticChangeLog), sessions history (last 50, no Mode column), and CSV export. No view-mode comparison, no share-links table (not applicable to diagnostics).
- **Steps:**
  1. Admin navigates to the Analytics tab — GET `/analytics/` fires on mount.
  2. Engagement score card renders with color-coded level label.
  3. Summary cards show total_views, unique_sessions, first_viewed_at, etc.
  4. Funnel rows render with section names and drop-off percentages.
  5. Device breakdown card shows desktop/mobile/tablet counts.
  6. CSV export button triggers download via `window.open`.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-diagnostic-analytics.spec.js` (also smoke-tested in `e2e/admin/admin-diagnostic-sections.spec.js`)
