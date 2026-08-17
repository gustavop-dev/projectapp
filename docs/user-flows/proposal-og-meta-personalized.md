### FLOW: `proposal-og-meta-personalized`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P3
- **Routes:** `/proposal/:uuid`
- **Description:** Personalized Open Graph meta tags are set dynamically so WhatsApp/social media previews show the client name and proposal title. Uses `useHead` with computed `og:title` and `og:description`.
- **Steps:**
  1. Proposal page loads and fetches proposal data.
  2. `useHead` sets `og:title` to "Propuesta para {client_name}".
  3. `og:description` includes client name and proposal title in the appropriate language.
  4. When the proposal URL is shared on WhatsApp/social media, the personalized preview is shown.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-og-meta-personalized.spec.js`
