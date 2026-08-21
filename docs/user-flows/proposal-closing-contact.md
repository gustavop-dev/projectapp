### FLOW: `proposal-closing-contact`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** El cliente llega al panel final “Gracias por tu tiempo” y encuentra allí el mensaje comercial, las acciones principales y los canales de contacto, separados de la nota de compromiso.
- **Steps:**
  1. El cliente recorre la propuesta hasta el panel de cierre.
  2. El panel muestra el llamado “¿Listo para comenzar?”.
  3. Se presentan las acciones comerciales configuradas.
  4. Se muestran Email, WhatsApp y Website con sus enlaces correspondientes.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-kickoff-closing-content.spec.js`
