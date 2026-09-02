### FLOW: `public-financing-pdf`

- **Module:** public
- **Role:** guest
- **Priority:** P2
- **Route:** `/:locale/financing`
- **Interaction:** Download the complete localized booklet; if generation fails, remain on the page with a visible retryable error.
- **Outcomes:** `success`, `failure`
- **Evidence:** public PDF control and `GET /api/financing/public/pdf/`.
