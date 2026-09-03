### FLOW: `admin-financing-settings`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/financing?tab=settings`
- **Interaction:** Consultar y publicar revisiones de la política comercial de financiación.

| Outcome | Inicio → acción → resultado observable |
|---|---|
| `display` | Abrir **Financiación → Configuración** → ver la revisión vigente, el rango elegible, el abono mínimo derivado, la tasa USD/COP y el historial. |
| `success` | Modificar una condición editable → pulsar **Publicar revisión** → confirmar → ver la nueva versión como vigente y conservar la anterior en el historial. |
| `error` | Ingresar un rango, porcentaje, plazo o ventana inválidos → intentar publicar → ver el error en el campo sin crear una revisión. |
| `failure` | Fallar la carga de la política → mostrar un estado de error explícito → reintentar → recuperar la configuración vigente. |

- **Reglas:** cada publicación crea una revisión inmutable; los nuevos borradores la adoptan automáticamente; los borradores anteriores sólo cambian por confirmación explícita; otrosíes listos, firmados, activos o completados nunca mutan; la tasa USD/COP se administra en Contabilidad y se congela por acuerdo.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-financing-settings.spec.js`
- **Backend Tests:** `content/tests/views/test_financing_agreements.py`, `content/tests/services/test_financing_policy_service.py`
