### FLOW: `public-financing-load`

- **Module:** public
- **Role:** guest
- **Priority:** P1
- **Route:** `/:locale/financing`
- **Interaction:** See an explicit unavailable state after the live request fails, then retry and recover the program content.
- **Outcomes:** `failure`, `success`
- **Evidence:** public financing page live-load and retry states.
