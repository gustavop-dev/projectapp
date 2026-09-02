### FLOW: `proposal-engagement-tracking`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Qualified tracking of client engagement while viewing a proposal. Loading the document is read-only; after five visible seconds, `useProposalTracking` sends validated section-level time data and the backend atomically records the session, first-view alert, and delivery state.
- **Steps:**
  1. User opens a proposal page.
  2. `useProposalTracking` generates a stable session ID but does not count the document `GET` as a view.
  3. Once the proposal remains visible for five seconds, it sends the first validated heartbeat to `POST /api/proposals/:uuid/track/`.
  4. As the user navigates, 30-second heartbeats update section time; hiding or leaving the page sends a final beacon.
  5. The backend validates the complete payload and atomically creates or updates `ProposalViewEvent` and `ProposalSectionView` records without duplicating the session.
  6. The first qualified session creates a persistent panel alert and queues an email with durable retry state.
  7. [Optional] Revisit, stakeholder, expiration, rejection, and engagement-decay signals are evaluated from confirmed tracking events.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-engagement-tracking.spec.js`
