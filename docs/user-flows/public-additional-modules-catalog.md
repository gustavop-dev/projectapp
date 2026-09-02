### FLOW: `public-additional-modules-catalog`

- **Module:** public
- **Role:** guest
- **Priority:** P1
- **Route:** `/:locale/additional-modules`
- **Interaction:** Follow the footer link, reach the catalog near the top without the panel/global header, read active modules in Spanish or English, choose card/list/accordion presentation, use the four catalog floating controls and retry a failed live request. The chosen presentation is remembered separately from the panel.
- **Outcomes:** `success`, `display`, `failure`
- **Evidence:** public catalog page/component and `GET /api/additional-modules/public/`.
