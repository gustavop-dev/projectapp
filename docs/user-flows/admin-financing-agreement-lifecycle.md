### FLOW: `admin-financing-agreement-lifecycle`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/financing/:id`
- **Interaction:** Gestionar el otrosí y su documento firmado a través de estados auditables.

| Outcome | Inicio → acción → resultado observable |
|---|---|
| `display` | Abrir un otrosí → ver estado, ciclo, revisión de política congelada, resumen, calendario, acciones permitidas e historial de responsables. |
| `success` | En un borrador anterior, confirmar la adopción de la política vigente → validar valores y reemplazar plantilla/calendario; marcar listo → congelar número/texto; descargar borrador marcado **BORRADOR · SIN FIRMA**; registrar PDF firmado → activar; certificar pago o cancelar con nota; archivar/restaurar sólo estados terminales. |
| `error` | Omitir PDF o nota obligatoria, subir un archivo inválido o intentar una transición no permitida → conservar el estado y mostrar validación. |
| `failure` | Fallar la carga o una mutación → mostrar el problema sin simular que el estado cambió. |

- **Privacidad:** el PDF firmado no tiene URL pública; sólo se descarga desde un endpoint autenticado y no se publica bajo `/media/`.
- **Cobranza:** la cláusula de mora queda documentada y auditable, pero este flujo no modifica automáticamente Hosting ni contabilidad.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-financing-agreements.spec.js`
- **Backend Tests:** `content/tests/views/test_financing_agreements.py`
