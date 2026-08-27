### FLOW: `admin-project-lifecycle-states`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/projects`
- **API:** `POST /api/projects/<id>/state-transitions/preview/`, `POST /api/projects/<id>/state-transitions/`, `GET /api/projects/<id>/state-history/`
- **Description:** El cambio de estado es una operación de negocio en dos pasos: primero explica el significado y calcula las consecuencias, después aplica exactamente ese impacto mediante token. En evolución distingue un producto en producción con una siguiente versión en desarrollo y conserva el efecto operativo de Activo. Suspendido detiene nueva facturación y avisos sin borrar deuda causada; Completado exige cierre limpio; Dado de baja cancela futuro y obliga a decidir conservar o castigar cada saldo causado. Una baja directa requiere nota. Un cambio financiero entre preview y confirmación invalida el token y deja el modal abierto. El histórico conserva episodios, fechas efectivas, actores y notas.
- **Interaction matrix:**

| Interaction | Outcome | Start → end state |
|---|---|---|
| Abrir histórico desde la fila | display | Proyectos → Histórico → episodios reales con fecha, actor y nota |
| Suspender después de revisar consecuencias | success | Activo → preview → confirmación → fila Suspendido y nuevo episodio |
| Registrar trabajo evolutivo sin apagar la operación | success | Activo → ayuda En evolución → preview → fila En evolución con efecto operativo |
| Intentar baja directa incompleta | error | Preview de baja → falta decisión o nota → confirmar permanece bloqueado |
| Confirmar un preview financiero obsoleto | failure | Preview → cambian cobros → HTTP 409 visible y modal conserva el contexto |

- **Coverage:** ✅ Las cuatro clases están cubiertas.
- **E2E Specs:** `e2e/admin/admin-project-lifecycle-states.spec.js`
