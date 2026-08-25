# Auditoría de navegación listado → detalle → listado

**Fecha:** 2026-08-25
**Alcance implementado:** Documentos
**Alcance auditado:** módulos del Panel con edición desde listados
**Veredicto:** **Documentos corregido; el patrón sigue pendiente en seis familias**

## Resumen ejecutivo

La causa de Documentos era doble: las cuatro salidas del editor apuntaban de
forma fija a la raíz y el listado sólo persistía carpeta, alcance, cliente y
proyecto. La corrección convierte la URL en la descripción completa del
listado (`folder`, `scope`, `tags`, `client`, `project`, `q`, `order`, `view`,
`page`, `focus`), lleva esa dirección al editor mediante `from` y sólo acepta
como retorno una ruta interna —con locale opcional— de `/panel/documents`.

El enlace visible, Cancelar y la salida de error comparten el mismo destino. La
etiqueta nombra búsqueda, carpeta, modo archivado o vista raíz. Al volver por el
enlace se reconstruye la página y se enfoca la fila/tarjeta; Atrás del navegador
recupera la misma URL previa y deja que el navegador conserve su posición
nativa. Una entrada directa o un `from` no confiable cae a Documentos sin
reescribir el historial.

Evidencia principal:

- Contrato URL bidireccional: `frontend/composables/useDocumentFilterQuery.js:5` y `:92`.
- Origen completo en cada enlace de edición: `frontend/pages/panel/documents/index.vue:1255`.
- Hidratación de página/foco y popstate: `frontend/pages/panel/documents/index.vue:920`.
- Destino común y contextual del editor: `frontend/pages/panel/documents/[id]/edit.vue:5` y `:593`.
- Validación anti-open-redirect: `frontend/utils/documentReturnNavigation.js:24`.

## Inventario transversal

| Prioridad | Módulo | Estado que se pierde | Evidencia del listado | Evidencia del retorno fijo | Decisión |
| --- | --- | --- | --- | --- | --- |
| P1 | Propuestas | búsqueda, filtros guardados, orden y página | `frontend/pages/panel/proposals/index.vue:585`, `:783`, `:812` | `frontend/pages/panel/proposals/[id]/edit.vue:59` | Adoptar primero el contrato compartido: es el listado más denso y frecuente. |
| P1 | Diagnósticos | búsqueda, filtros guardados, orden, selección y página | `frontend/pages/panel/diagnostics/index.vue:384`, `:458`, `:504`, `:585` | `frontend/pages/panel/diagnostics/[id]/edit.vue:103`; eliminación también fuerza raíz en `:1379` | Resolver junto con Propuestas; ambos ya comparten conceptos de filtros guardados. |
| P2 | Blog | página del listado y origen lista/calendario | `frontend/pages/panel/blog/index.vue:20`, `:78`, `:146` | `frontend/pages/panel/blog/[id]/edit.vue:6` | Distinguir `list` de `calendar`; no basta con conservar número de página. |
| P2 | Paquetes de horas | sección, nacionalidad, presentación y página | `frontend/pages/panel/hour-packages/index.vue:30`, `:38`, `:43`, `:296` | `frontend/pages/panel/hour-packages/[id]/edit.vue:4`, `:18`, `:120`, `:259` | La nacionalidad debe estar en URL antes de propagar `from`. |
| P3 | Portafolio | página del listado | `frontend/pages/panel/portfolio/index.vue:46`, `:58`, `:108` | `frontend/pages/panel/portfolio/[id]/edit.vue:4`, `:147` | Aplicación pequeña del mismo patrón con `page` + `focus`. |
| P3 | Linktrees | hoy casi no hay estado de listado | navegación fija en `frontend/pages/panel/linktrees/[id]/edit.vue:21` | mismo punto | Mantener en observación; migrar cuando el listado gane filtros/paginación. |

## Patrón recomendado para el siguiente lote

1. Cada listado es dueño de un composable que serializa sólo estado visible y
   reproducible, omitiendo defaults y usando `router.replace`.
2. Cada enlace de detalle añade `from=<fullPath del listado>` y un identificador
   de foco, sin mutar la entrada actual del historial.
3. Cada detalle valida `from` contra una allowlist de rutas internas del módulo;
   nunca usa un destino arbitrario recibido por query.
4. Todas las salidas del detalle consumen el mismo `returnTarget`; la etiqueta
   describe el destino. Una entrada directa usa la raíz del módulo.
5. La aceptación mínima por módulo cubre enlace explícito, Atrás, entrada
   directa, URL manipulada y restauración de página/foco.

## Fuera de alcance de esta corrección

No se cambiaron Propuestas, Diagnósticos, Blog, Paquetes de horas, Portafolio ni
Linktrees. Aplicar el patrón sin llevar primero el estado real de cada listado a
su URL sólo trasladaría el defecto a un `from` incompleto. Este inventario deja
el orden de implementación y la evidencia para un lote separado.
