### FLOW: `public-additional-modules-catalog`

- **Module:** public
- **Role:** guest
- **Priority:** P1
- **Route:** `/:locale/additional-modules`
- **Interaction:** Follow the footer link and read active modules grouped in the live catalog order; retry a failed live request.
- **Outcomes:** `display`, `failure`
- **Evidence:** public catalog page/component and `GET /api/additional-modules/public/`.
