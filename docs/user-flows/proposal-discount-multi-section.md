### FLOW: `proposal-discount-multi-section`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** When a proposal has an active discount, the discount badge is consistently visible across three sections: Investment (banner with % OFF), Calculator modal (footer badge), and ProposalClosing (special price badge). This ensures the client is always aware of the time-limited offer.
- **Steps:**
  1. Client opens a proposal with `discount_percent > 0`.
  2. Investment section shows a discount banner with percentage and days remaining.
  3. Calculator modal shows a discount badge in the footer.
  4. Closing section shows a "Precio especial" badge above the accept button.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-discount-multi-section.spec.js`
