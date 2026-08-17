### FLOW: `admin-accounting-export`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel/accounting/*` (list views) and `/panel/accounting` (workbook)
- **Description:** Data export: every list view has an "Exportar" dropdown (CSV / Excel .xlsx) calling `GET /api/accounting/export/?section=&file_format=` with the active filters mapped to the server query params (`buildExportParams`), and the dashboard's "Exportar Excel" button downloads the full workbook (Resumen sheet + one sheet per section) from `GET /api/accounting/export/workbook/?year=`. Spanish headers, numeric money cells, filenames stamped with the Bogotá date.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-accounting-export.spec.js`
