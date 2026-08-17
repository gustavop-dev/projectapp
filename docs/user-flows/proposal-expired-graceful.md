### FLOW: `proposal-expired-graceful`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P1
- **Routes:** `/proposal/:uuid`
- **Description:** When a client opens an expired proposal, the backend returns HTTP 410 Gone and creates a `post_expiration_visit` alert. The frontend renders a graceful `ProposalExpired` component with the client name, proposal title, a WhatsApp reactivation CTA, and an email contact option.
- **Steps:**
  1. Client opens a proposal URL where `expires_at` is in the past.
  2. API call to `GET /api/proposals/:uuid/` returns HTTP 410 with partial proposal data.
  3. Backend creates a `post_expiration_visit` ProposalAlert for the seller.
  4. Frontend detects 410 status and sets `loadError = 'expired'`.
  5. `ProposalExpired` component renders with personalized message: "{clientName}, esta propuesta ha expirado".
  6. WhatsApp reactivation button pre-fills a message mentioning the proposal title.
  7. Email contact button links to team email.
- **Branches:**
  - [Branch A — Post-rejection revisit] If the proposal was rejected and the client revisits, a `post_rejection_revisit` alert is also created.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-expired-graceful.spec.js` (410 fallback + 200 expired_meta banner)
- **Known gaps:** When the full proposal still renders with the persistent expired banner (`pages/proposal/[uuid]/index.vue` `isExpired`), the top-left index toggle must drop below the banner (`ProposalIndex` `bannerActive` → `top-28 sm:top-20`) so the two don't overlap. No E2E asserts this no-overlap; only a unit test (`test/components/ProposalIndex.test.js`) covers the offset class.
