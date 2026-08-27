# Barrido de cuadros nativos en `/panel`

Fecha: 2026-08-26

Alcance: rutas bajo `frontend/pages/panel/` y componentes alcanzables bajo
`frontend/components/panel/`. El inventario se levantó antes de reemplazar los
diálogos.

## Hallazgos alcanzables

| Superficie | Diálogo nativo | Uso | Reemplazo definido |
| --- | --- | --- | --- |
| `DocumentClientNoteModal.vue` | 3 `prompt`, 2 `confirm` | Editar, resolver o descartar una observación y decidir transiciones de estado | Subvistas del modal existente con campos, contexto y acciones explícitas |
| `DocumentStateSelector.vue` | 1 `prompt`, 2 `confirm` | Cerrar/quitar un estado y confirmar un estado similar | Paneles propios dentro del selector para motivo y confirmación |
| `DocumentStateHistoryModal.vue` | 1 `prompt` | Corregir fecha real de apertura | Formulario dentro del modal de historial |
| `SendDocumentEmailModal.vue` | 1 `confirm` | Ofrecer marcar adjuntos como Enviado tras mandar el correo | Paso posterior dentro del mismo modal |
| `pages/panel/documents/statuses.vue` | 3 `confirm` | Crear parecido, retirar y fusionar estados | `ConfirmModal` compartido con contexto |
| `pages/panel/communications/index.vue` | 1 `confirm` | Eliminar un borrador | `ConfirmModal` compartido con detalle del borrador |

Total alcanzable: 14 llamadas nativas en 6 superficies.

## Hallazgo no alcanzable

`TagManagerModal.vue` contenía un `confirm`, pero no tenía referencias desde
ninguna ruta o componente de ejecución. Se clasifica como código huérfano y se
retira junto con su prueba aislada; la gestión de etiquetas vigente vive en las
superficies actuales del módulo de documentos.

## Errores

No se encontraron `window.alert` alcanzables. Los errores de las superficies
revisadas ya usan avisos del panel o mensajes inline; los nuevos formularios
mantienen el modal abierto y permiten reintentar.

## Regla preventiva

El CI incorpora un barrido estático de las páginas y componentes de `/panel`.
Falla ante llamadas a `window.alert`, `window.confirm`, `window.prompt` o sus
equivalentes globales, sin confundir funciones locales con esos nombres.
