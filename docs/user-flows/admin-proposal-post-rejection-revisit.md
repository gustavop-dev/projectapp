### FLOW: `admin-proposal-post-rejection-revisit`

- **Module:** admin
- **Role:** system
- **Priority:** P2
- **Routes:** N/A (backend-triggered)
- **Description:** When a client revisits a proposal that was previously rejected, the system creates a `post_rejection_revisit` ProposalAlert. This signals potential reconsideration and appears in the admin alerts panel.
- **Steps:**
  1. Client opens a proposal URL where `status = 'rejected'`.
  2. Backend detects the rejected status in `retrieve_public_proposal`.
  3. A `post_rejection_revisit` ProposalAlert is created with message: "{clientName} revisitó la propuesta rechazada. Posible reconsideración."
  4. Alert appears in the admin proposals list alerts panel.
- **Coverage:** ⚠️ Backend-only
- **Backend Tests:** `content/tests/views/test_proposal_views.py`
