# Auditoría de controles deshabilitados — 2026-08-26

## Veredicto

🟢 El panel termina con **0 controles deshabilitados en silencio** dentro del
alcance auditado. Los 85 hallazgos accionables fueron remediados y el mismo
criterio quedó automatizado en CI.

## Criterio adoptado

Se mantiene la deshabilitación preventiva, con un contrato parejo:

1. Un bloqueo resoluble enumera **todas** las condiciones faltantes junto al
   control y también en hover, foco de teclado y toque mediante
   `BaseControlGate`.
2. Un límite de estado, permiso o posición explica el motivo en el propio
   control mediante `disabledReason`/`title`; la interfaz cercana ya muestra el
   estado que lo origina.
3. Un bloqueo transitorio usa `loading` y un verbo activo como *Guardando…* o
   *Enviando…*.
4. El marcador `data-disabled-explained` sólo es válido cuando una explicación
   visible adyacente ya es dueña del contrato.

No se adoptó el patrón general de botones habilitados que fallan al presionarse:
en operaciones con efectos laterales, mantener el guard evita dobles envíos y
transiciones inválidas. La explicación visible conserva la enseñanza sin abrir
esa ventana de error.

## Caso inicial: cuenta de cobro

- El selector etiqueta preventivamente **Sin correo** y aclara que habrá que
  agregarlo para enviar.
- Al elegir ese cliente, el modal avisa de inmediato y ofrece **Guardar y usar**.
- El guardado hace PATCH al perfil canónico; no se limita a cambiar el snapshot
  de la cuenta ni cierra el modal.
- Descripción, notas, ingreso, valor y demás borrador permanecen intactos.
- La previsualización enumera a la vez cliente, carga pendiente, ingreso,
  conflicto de cliente, valor, concepto, correo y fecha fija que falten.
- El correo destinatario por cuenta queda disponible como override únicamente
  después de reparar el correo canónico.

## Alcance y lista de hallazgos remediados

El inventario bruto encontró 216 usos de `disabled`; al separar controles no
interactivos, valores literales falsos y estados puramente transitorios quedaron
73 bloqueos semánticos accionables en páginas y módulos. La ampliación a las
primitivas compartidas encontró otros 12, para un total remediado de 85. Se
revisaron `pages/panel`, componentes de panel, el design system base y los
módulos compartidos alcanzables por esas páginas.

| Área | Ubicaciones remediadas |
|---|---|
| Primitivas | `BaseButton`, `BaseActionButton`, `BaseActionMenu`, `BaseSegmented`, `BaseSegmentedMulti`, normalización de opciones y nuevo `BaseControlGate` |
| Cuenta de cobro y selección de cliente | `CollectionAccountFormModal`, `ClientAutocomplete` |
| Contabilidad | `AccountingMerchantInput`, `BulkAssignModal`, `CardSnapshotFormModal`, `EmailLogTable`, `HostingActionsModal`, `IncomeBulkSettleModal`, `IncomeLiquidateModal`, `IncomeMuteModal`, `PartnerSplitInput`, `PocketMovementFormModal`, `ProjectSelect`, `RecurringCategoriesModal`, `SavedFilterTabsManager`, `RecurringChartsModal`, páginas Hosting y Configuración |
| Clientes y correos | `ClientEmailsModal`, `ClientReassignModal`, `ClientEmailCopySettings`, página Comunicaciones |
| Documentos | `AttachFromDocumentsModal`, `DocumentClientNoteModal`, `DocumentStateSelector`, `FolderSidebar`, páginas Crear, Editar y Estados |
| Proyectos | `ProjectAssignUnlinkedModal`, `ProjectChangeClientModal`, `ProjectFormModal`, listado de Proyectos |
| Propuestas | `ProjectScheduleEditor`, `ProposalDocumentsTab`, `ProposalMultiSendModal`, `TechnicalDocumentEditor`, `ValueAddedModulesForm`, `ProposalDefaultsPanel`, `DevChecklistTab`, `ProposalActivityTab`, `ProposalGeneralTab`, `ProposalHourRateTab`, páginas Crear, Editar y Listado |
| Otros módulos del panel | `LocaleSwitcher`, `DiagnosticActivityTab`, `DownloadQrModal`, edición de Blog, Diagnósticos y Linktree, y Styleguide |

No quedan ubicaciones abiertas dentro de ese alcance. El guard deliberadamente
excluye superficies públicas de Diagnósticos porque esta auditoría corresponde
al panel interno.

## Prevención

`frontend/scripts/check-disabled-controls.mjs` analiza tags completos —incluidos
atributos multilínea y comparaciones con `>`— y exige uno de estos contratos:
`disabled-reason`, `aria-describedby`, `title`, `loading` o explicación adyacente
declarada. `npm run check:disabled-controls` corre en modo estricto dentro del
job de diseño de `.github/workflows/ci.yml`.

## Evidencia

- Guard estático: **PASS — 0 silent panel controls**.
- Jest focal: **29/29** casos para gate, modal, selector y contratos base.
- Playwright: **2/2** escenarios para error completo y reparación exitosa sin
  pérdida del borrador.
- Build Nuxt cliente/SSR/Nitro: aprobado.
- Mapa de flujos: fresco.
- `admin-accounting-collection-create`: **covered** en
  `display`, `failure`, `error` y `success`; sin `junk-only`, resultados sin
  validar ni evidencia fuera de contrato.
