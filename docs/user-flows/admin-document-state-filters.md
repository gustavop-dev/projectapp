### FLOW: `admin-document-state-filters`

- **Módulo:** admin
- **Rol:** admin
- **Prioridad:** P1
- **Ruta:** `/panel/documents`
- **API:** `GET /api/documents/?states=&without_states=&preset=`
- **Descripción:** El listado muestra primero el episodio del ciclo y después las señales, cada uno con su antigüedad. **Solucionar bug** usa un tratamiento visual de atención. Seleccionar varios estados dentro de la dimensión usa OR; **Sin cerrado** consulta ausencia. Los presets resuelven las búsquedas repetidas: algo por solucionar, enviados sin cerrar, cerrados y por clasificar.
- **Ramas:**
  - [Display] El usuario identifica una acción pendiente y cuánto lleva abierta sin entrar al documento.
  - [Success] Estados múltiples, ausencia y presets generan consultas consistentes y reemplazan el preset al cambiar filtros manuales.
  - [Failure] Un fallo conserva un aviso persistente con opción de reintento.
- **Cobertura:** ✅ display/success/failure.
- **E2E:** `e2e/admin/admin-document-state-workflow.spec.js`
