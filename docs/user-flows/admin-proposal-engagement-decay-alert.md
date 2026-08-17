### FLOW: `admin-proposal-engagement-decay-alert`

- **Module:** admin
- **Role:** system
- **Priority:** P2
- **Routes:** N/A (backend-triggered)
- **Description:** When a client views fewer sections in a session compared to their average from previous sessions (below 50% of the average), the system creates an `engagement_decay` ProposalAlert. The alert is rate-limited to one per 3 days per proposal. It appears in the alerts panel on the proposals list page.
- **Steps:**
  1. Client views a proposal and engagement data is sent via `POST /api/proposals/:uuid/track/`.
  2. Backend compares current session section count to the average of previous sessions.
  3. If current count < 50% of average, and no `engagement_decay` alert exists for the last 3 days, a new alert is created.
  4. Alert message includes section counts: "{clientName} vio {N} secciones vs promedio anterior de {avg}. Posible pérdida de interés."
  5. Alert appears in the admin proposals list alerts panel.
- **Coverage:** ⚠️ Backend-only
- **Backend Tests:** `content/tests/views/test_proposal_views.py`
