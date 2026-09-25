# QA — copia Markdown de documentos de propuestas

Alcance: [PR #408](https://github.com/gustavop-dev/projectapp/pull/408), pestaña
Documentos de la edición de propuestas. Validación en el worktree
`proposal-document-markdown`, sin escrituras sobre bases o archivos del servicio.

| Capa | Evidencia |
|---|---|
| Backend | 29 casos nuevos aprobados en lotes focales: snapshot real de contrato por plantilla y personalizado, PDF legado, alcance formal, permisos, pertenencia, bytes de descarga, extracción y límites. SQLite y storage temporales con `projectapp.settings_test`. |
| Frontend unit | Aprobados los casos de portapapeles, errores en español, acciones según formato, descarga con nombre UTF-8 y tablas Markdown sanitizadas. Los cambios pedidos por el auditor se reejecutaron: 3 casos de formatos y 2 de representación Markdown. |
| E2E | 18 casos aprobados sin reintentos en navegador: navegación desde el panel, copia de cada documento, errores recuperables, descarga, vista previa y pantalla compacta. Verificado en el blob de Playwright del [job de CI](https://github.com/gustavop-dev/projectapp/actions/runs/36080807692/job/107902119821), sobre `eda48433`; el shard completo aprobó 162 casos. Marca de borrador retirada tras esta ejecución. |
| Quality gate | `qa-agent.sh --verify` terminó con código 0: backend 3 archivos, unit 4, E2E 1; cero errores y warnings, reglas estrictas y lint externo. El engine retiró `.qa-gate-pending`. |
| Auditoría | KEEP tras corregir nombres parametrizados, selección del mensaje del botón, semántica real de celdas y separación de pruebas móviles. Sin eliminaciones de tests. |
| Mapas | Catálogos de vistas y contrato responsivo válidos. Registro de flujos regenerado; freshness aprobado. El nuevo flujo declara success/error/failure/display y dispone de tests calificables para cada clase. |
| Regresión | Caso del PDF formal existente y contrato MCP de campos aprobados. `makemigrations --check --dry-run` no detectó cambios pendientes. Guard de diseño aprobado en los tres componentes tocados. |

Los tests usan los archivos reales de extracción y el navegador con respuestas
HTTP simuladas; no prueban OCR ni reproducen el diseño binario de Office. PDF
escaneado e imágenes requieren reconocimiento de texto; DOC/XLS requieren
conversión. No se ejecutó la suite completa localmente. El CI de la versión final
queda registrado en el PR.

La revisión global del registro detecta deuda previa fuera del cambio (un flujo
junk-only y 31 parciales); no se presenta esta entrega como una auditoría limpia
de todo el producto. La memoria QA externa del toolkit tenía cambios de otra
sesión y quedó intacta.

La migración 0255 incorpora el snapshot del contrato y se aplica en el deploy.
