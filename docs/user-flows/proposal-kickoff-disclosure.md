### FLOW: `proposal-kickoff-disclosure`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** El cliente revisa la nota de compromiso y el plan de kickoff en dos columnas. La información que condiciona la activación del cronograma permanece resumida en un desplegable para no desbalancear la sección.
- **Steps:**
  1. El cliente navega a la sección de nota final.
  2. La nota, los compromisos y el plan de kickoff aparecen en columnas equilibradas.
  3. El bloque “Información necesaria para activar el cronograma” inicia cerrado.
  4. El cliente expande el bloque.
  5. Se muestran la introducción y los pasos requeridos antes de iniciar.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-kickoff-closing-content.spec.js`
