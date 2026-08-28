### FLOW: `admin-outbound-email-history-attachments`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/emails?tab=history`
- **Description:** El administrador reconoce y abre la evidencia exacta que acompañó cada correo, sin regenerarla desde el documento actual.
- **Interacciones y outcomes:**
  1. **display:** navegar a Emails, abrir Historial, expandir un envío y comprobar nombre, tipo documental, formato, tamaño individual, peso total, vínculo al documento y enlaces del contenido/plantilla.
  2. **display:** abrir **Previsualizar** y ver el PDF retenido en el visor compartido.
  3. **display:** un snapshot sin archivos afirma “Este correo no llevaba adjuntos”; un registro legado revela la brecha y no ofrece descarga.
  4. **success/error/failure:** n/a; esta interacción sólo consulta evidencia. Descarga/autorización y bytes exactos se verifican en integración backend.
- **E2E Spec:** `e2e/admin/admin-client-email-copy-settings.spec.js`
