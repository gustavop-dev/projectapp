### FLOW: `admin-financing-agreement-second-cycle`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/financing/:id`
- **Interaction:** Aprobar una segunda financiación dentro de la modalidad de cinco años.

| Outcome | Inicio → acción → resultado observable |
|---|---|
| `display` | Abrir el primer ciclo completado de cinco años → ver **Aprobar segundo ciclo**; una modalidad de tres años no ofrece la acción. |
| `success` | Confirmar la evaluación manual de riesgo → crear un único borrador de ciclo 2 → navegar a él con modalidad y vigencia original bloqueadas para edición. |
| `error` | El primer ciclo no está pagado, pertenece a tres años o ya tiene ciclo 2 → rechazar la aprobación sin crear otro registro. |
| `failure` | Fallar la operación de aprobación → permanecer en el primer ciclo y mostrar el error para reintentar con seguridad. |

- **Regla temporal:** el calendario del ciclo 2 debe terminar dentro de la vigencia original; aprobarlo no reinicia ni extiende los cinco años de exclusividad.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-financing-agreements.spec.js`
- **Backend Tests:** `content/tests/services/test_financing_agreement_service.py`, `content/tests/views/test_financing_agreements.py`
