### FLOW: `proposal-payment-plan-closing`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** El cliente revisa cerca de las acciones de cierre los hitos del plan de pagos y el total de la propuesta, con moneda e IVA visibles.
- **Outcomes:**
  - `display` — el panel final muestra las cuotas configuradas y conserva el sufijo fiscal del total.
- **Steps:**
  1. El cliente recorre la propuesta hasta el panel de cierre.
  2. El panel presenta el plan de pagos configurado junto a las acciones de respuesta.
  3. El total mantiene la moneda y el texto `+ IVA` sin duplicarlos.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-payment-plan-closing.spec.js`
