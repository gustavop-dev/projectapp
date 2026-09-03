### FLOW: `admin-financing-agreement-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/financing?tab=agreements`, `/panel/financing/new`, `/panel/financing/:id`
- **Interaction:** Crear un borrador de otrosí desde el registro administrativo.

| Outcome | Inicio → acción → resultado observable |
|---|---|
| `display` | Abrir **Financiación → Otrosíes** → ver métricas, filtros y registros vigentes o el estado vacío. |
| `success` | Pulsar **Nuevo otrosí** → seleccionar un cliente → verificar su identidad precargada → completar contrato, alcance y valores → crear → abrir el borrador con doce cuotas editables. |
| `error` | Enviar datos incompletos o inválidos → el API y el formulario señalan los campos → los datos ya escritos permanecen disponibles. |
| `failure` | Fallar la carga del registro → mostrar un estado de error explícito sin presentar una lista vacía engañosa. |

- **Reglas:** el cliente debe estar activo; propuesta y proyecto opcionales deben pertenecerle; el saldo debe ser positivo; las doce cuotas deben sumar exactamente el saldo y vencer entre los días 1 y 5.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-financing-agreements.spec.js`
- **Backend Tests:** `content/tests/views/test_financing_agreements.py`, `content/tests/services/test_financing_agreement_service.py`
