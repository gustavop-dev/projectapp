### FLOW: `public-additional-modules-catalog`

- **Module:** public
- **Role:** guest
- **Priority:** P1
- **Route:** `/:locale/additional-modules`
- **Interaction:** Follow the footer link, read active modules in Spanish or English, choose card/list/accordion presentation and retry a failed live request. The chosen presentation is remembered separately from the panel.
- **Outcomes:** `success`, `display`, `failure`
- **Evidence:** public catalog page/component and `GET /api/additional-modules/public/`.
