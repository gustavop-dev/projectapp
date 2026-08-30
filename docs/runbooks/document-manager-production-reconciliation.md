# Conciliación de producción del Gestor Documental

Este procedimiento adopta las carpetas históricas como espacios de proyecto o
cliente sin borrar documentos. El despliegue de código y esquema no ejecuta la
conciliación: una persona debe generar, revisar y aprobar el manifiesto sobre la
base de producción.

## Guardas obligatorias

- Ejecutar únicamente desde el clon desplegado de producción, nunca desde un
  worktree de sesión.
- Desplegar primero la migración
  `accounts.0058_project_document_manager_enabled` y el comando actualizado.
- Crear y verificar un respaldo de la base antes de aplicar. Conservar su ruta o
  identificador para `--backup-reference`.
- No renombrar, mover, archivar ni editar carpetas o documentos entre la
  generación del plan y su aplicación. Cualquier cambio invalida la huella y
  obliga a generar otro plan.
- Guardar manifiesto, reporte, respaldo y snapshot inverso fuera de rutas
  públicas y versionadas.

## 1. Generar el plan de sólo lectura

Los identificadores siguientes corresponden al inventario verificado el
2026-08-29. Antes de usarlos, confirmar otra vez nombre, propietario, estado y
conteos en producción.

```bash
cd /home/ryzepeck/webapps/projectapp/backend
source ../.venv/bin/activate
python manage.py reconcile_project_folders \
  --plan /ruta/segura/document-manager-20260830.json \
  --exclude-project 7 \
  --enable-project 5 \
  --enable-project 8 \
  --enable-project 9 \
  --enable-project 10 \
  --enable-project 11 \
  --enable-project 12 \
  --enable-project 13 \
  --assign-client-root 2:58 \
  --assign-client-root 3:36 \
  --assign-client-root 61:36
```

El comando escribe el JSON y un reporte Markdown contiguo, imprime su SHA-256 y
confirma que no modificó la base.

## 2. Revisar todas las decisiones

Validar esta referencia contra el JSON recién generado; los conteos son una
línea base, no autorización automática:

| Destino | Proyecto/carpeta | Acción esperada | Línea base |
|---|---|---|---|
| Proyecto 8 | G&M / raíz 5 | Convertir | 4 carpetas, 13 documentos |
| Proyecto 10 | Vástago / raíz 7 | Convertir | 9 carpetas, 53 documentos |
| Proyecto 11 | Xpandia / raíz 55 | Convertir | 4 carpetas, 6 documentos |
| Proyecto 9 | Kore / raíz 65 | Convertir | 1 carpeta, 2 documentos |
| Proyecto 12 | Tenndalux / raíz 78 | Convertir | 2 carpetas, 2 documentos |
| Proyecto 5 | Mimittos | Crear raíz y revisar documento 120 | Documento sin carpeta |
| Proyecto 13 | Candle | Crear/adoptar raíz; catálogo archivado | Estado no activo |
| Proyecto 7 | PRUEBA | Excluir | No mover ni borrar contenido |
| Cliente 58 | Carlos / raíz 2 | Asignar al cliente | Conservar raíz superior |
| Cliente 36 | Gustavo / raíces 3 y 61 | Asignar ambas al cliente | No anidar ni fusionar |

Para cada acción con `decision: "pending"`:

- usar `approve` sólo si el identificador, propietario, impacto y destino son
  correctos;
- usar `skip` para toda acción informativa, ambigua o no aprobada;
- no aprobar tipos `conflict`, `client_conflict` ni `document_conflict`;
- confirmar que Candle tenga un estado cuyo efecto operativo no sea
  `development` ni `operating`; así aparece bajo **Proyectos archivados** sin
  archivar sus documentos;
- confirmar que PRUEBA produzca `configure_project` con
  `document_manager_enabled: false`;
- dejar Familia, Temporal y cualquier otra raíz sin relación inequívoca como
  carpeta sin asignar.

La aplicación rechaza un manifiesto con decisiones pendientes o con tipos no
aplicables aprobados.

## 3. Confirmar el artefacto y aplicar

Calcular el hash después de terminar la revisión:

```bash
sha256sum /ruta/segura/document-manager-20260830.json
```

Aplicar una sola vez, proporcionando el hash literal y la referencia del
respaldo ya verificado:

```bash
python manage.py reconcile_project_folders \
  --apply-reviewed /ruta/segura/document-manager-20260830.json \
  --confirm SHA256_REVISADO \
  --backup-reference RESPALDO_VERIFICADO \
  --inverse-out /ruta/segura/document-manager-20260830.inverse.json
```

Antes de la transacción, el comando escribe atómicamente un snapshot inverso
con estado `prepared`. Después del éxito lo completa con estado `applied`, la
huella posterior y cada cambio realizado. Si la huella de producción difiere
del plan, la aplicación se cancela sin conciliar datos.

## 4. Verificación posterior

- Vástago conserva exactamente sus 9 carpetas y 53 documentos y su raíz queda
  ligada al proyecto 10.
- G&M, Xpandia, Kore y Tenndalux conservan sus conteos de línea base y tienen una
  sola raíz gestionada cada uno.
- Mimittos tiene una raíz y el documento 120 queda en su ruta automática sólo
  si esa acción fue aprobada.
- PRUEBA no aparece en el catálogo del Gestor Documental.
- Candle aparece bajo **Proyectos archivados**; sus documentos permanecen
  activos salvo que ya estuvieran archivados por una operación independiente.
- Carlos y Gustavo aparecen bajo Clientes; sus raíces permanecen superiores y
  no se duplican como carpetas sin asignar.
- Familia, Temporal y las demás raíces realmente huérfanas siguen visibles sólo
  en **Carpetas sin asignar**.
- Cambiar entre proyecto, cliente y carpeta manual limpia los otros dos filtros
  y nunca produce una intersección residual vacía.

## 5. Incidente o reversión

Detener cualquier operación adicional y conservar el manifiesto, el snapshot
inverso y los logs. El comando no ofrece rollback automático: restaurar mediante
el respaldo verificado y usar el bloque `before`/`changes` del snapshot inverso
para auditar qué debía volver a su valor anterior. No improvisar movimientos ni
borrados manuales sobre la base afectada.
