### FLOW: `admin-project-state-catalog`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/projects/statuses`
- **API:** `GET|POST /api/project-states/`, `PATCH /api/project-states/<id>/`, `POST /api/project-states/<id>/retire/`, `POST /api/project-states/<id>/merge/`
- **Description:** El catálogo compartido de PA-88 se reutiliza para proyectos con el mismo componente de administración. Los siete estados semilla son visibles, incluido En evolución para un proyecto entregado que sigue operando mientras se amplía. El usuario puede descubrir otros con el uso, crearlos, renombrarlos, describirlos, recolorearlos, fusionarlos y retirarlos. La ayuda contextual combina la descripción editable con una consecuencia del sistema derivada del efecto operativo protegido que gobierna cobros y cierres.
- **Interaction matrix:**

| Interaction | Outcome | Start → end state |
|---|---|---|
| Abrir el catálogo desde Proyectos | display | Proyectos → Administrar estados → siete semillas, ayuda, usos e histórico |
| Crear, renombrar o retirar un estado libre | success | Formulario/edición → catálogo refrescado sin perder histórico |
| Retirar un estado usado | error | Confirmar retiro → explicación de proyectos activos → estado permanece |
| Guardar durante una falla del servidor | failure | Editar nombre → HTTP 5xx visible → borrador permanece para reintentar |

- **Coverage:** ✅ Las cuatro clases están cubiertas.
- **E2E Specs:** `e2e/admin/admin-project-lifecycle-states.spec.js`
