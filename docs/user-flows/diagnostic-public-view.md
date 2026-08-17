### FLOW: `diagnostic-public-view`

- **Module:** diagnostic
- **Role:** guest (via UUID link in email)
- **Priority:** P1
- **Routes:** `/diagnostic/:uuid`
- **Description:** Client opens the public diagnostic link (no Nuxt global header — `layout: false`) and navigates the 8 JSON-driven section components (Purpose / Radiography / Categories / DeliveryStructure / ExecutiveSummary / Cost / Timeline / Scope). Navigation is via a floating sidebar index (`DiagnosticIndex.vue`) — hamburger toggle top-left, panel slides in with numbered badges and visited checkmarks. Server-side filtering returns only sections whose `visibility ∈ {phase, both}` where `phase = 'final' if final_sent_at else 'initial'`. Per-section dwell time is recorded via `DiagnosticViewEvent` + `DiagnosticSectionView`; the final row is flushed via `navigator.sendBeacon` on tab unload.
- **Steps:**
  1. Client navigates to `/diagnostic/:uuid` (no auth required).
  2. Page fetches GET `/api/diagnostics/public/:uuid/` (auto-increments `view_count`) and generates a client-side `session_id`.
  3. POST `/track/` with `session_id` creates a `DiagnosticViewEvent`.
  4. [Branch: SENT + no `final_sent_at`] — Only `initial`/`both` sections are returned by the API and appear in the sidebar index.
  5. [Branch: SENT + `final_sent_at`] — Sections with `final` visibility (e.g. `executive_summary`) also appear; footer shows accept/reject buttons.
  6. Client opens the sidebar (hamburger button) and clicks a section → sidebar closes, section changes, POST `/track-section/` fires with elapsed seconds.
  7. Client clicks "Aceptar propuesta" → POST `/api/diagnostics/public/:uuid/respond/` with `decision: 'accept'`.
  8. Status transitions to `accepted`; acceptance footer replaces the CTA.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/public/diagnostic-public-view.spec.js` + `e2e/admin/admin-diagnostic-sections.spec.js` (initial-phase visibility filter)
