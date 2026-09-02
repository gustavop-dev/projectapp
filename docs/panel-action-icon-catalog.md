# Catálogo de iconos de acción del panel

Este documento registra el vocabulario visual de las acciones ejecutables de
`/panel/**`. La fuente de verdad que renderiza la interfaz es
`frontend/config/panelActions.js`; esta página explica su alcance, las
decisiones tomadas y el inventario funcional.

## Inventario por pantalla y módulo

| Superficie | Acciones encontradas y normalizadas |
| --- | --- |
| Shell del panel, navegación y dashboard | abrir/contraer/expandir navegación, cambiar tema, abrir plataforma, ver, actualizar, filtrar, abrir calendario |
| Documentos, carpetas y notas | crear, buscar, limpiar, ver, editar, renombrar, copiar, duplicar, mover, enviar, descargar, adjuntar, gestionar etiquetas/carpetas, archivar, restaurar, eliminar, cerrar, ordenar, expandir/contraer |
| Proyectos, clientes, comunicaciones y administradores | crear, editar, eliminar, agregar usuario, ingresar como usuario, abrir en otra pestaña, ver, ver comunicaciones, copiar, volver, filtrar |
| Propuestas, defaults y entregables | crear, editar, copiar, duplicar, ver, abrir en otra pestaña, enviar, reenviar, enviar mensaje/oferta, registrar actividad, ver correos, activar/desactivar, aprobar/rechazar, negociar, cambiar estado, generar/regenerar, publicar/retirar, descargar, eliminar |
| Diagnósticos web | crear, editar, copiar, duplicar, ver, enviar, reenviar, ver correos, generar/regenerar, analizar, activar/desactivar, archivar, eliminar, expandir/contraer |
| Contabilidad | crear, editar, eliminar, anular, liquidar, exportar, descargar, enviar, reenviar, silenciar/reactivar, completar, marcar como perdido, ciclos de pago, estadísticas, calcular, ver listado, filtrar, actualizar, cerrar |
| Blog, portafolio, LinkedIn, Linktrees y tarjetas QR | crear, editar, copiar, duplicar, ver, publicar/retirar, abrir en otra pestaña, descargar, eliminar, abrir calendario, volver/continuar |
| Tareas, paquetes de horas, vistas y MCPs | crear, editar, completar, eliminar, actualizar, filtrar, configuración, abrir en otra pestaña, volver/continuar |
| Componentes base y styleguide | acciones de tabla y dropdown, anterior/siguiente, ordenar, mover arriba/abajo, pantalla completa, cerrar, reintentar y catálogo visual completo |

### Inventario verificable por pantalla

La tabla siguiente registra las claves canónicas renderizadas directamente por
cada archivo de página. Las acciones encapsuladas por tablas, modales, filtros,
drawers y demás componentes compartidos figuran en el inventario de módulo de
arriba y quedan cubiertas por el mismo guard. Las rutas marcadas como
redirección no renderizan controles propios.

| Ruta | Claves de acción declaradas en la página |
| --- | --- |
| `/panel` | create |
| `/panel/accounting` | create, export, forward |
| `/panel/accounting/ads` | create |
| `/panel/accounting/cards` | create |
| `/panel/accounting/collections` | complete, delete, download, email-history, more, notes, resend, view, void |
| `/panel/accounting/expenses` | create |
| `/panel/accounting/history` | Acciones servidas por componentes compartidos de historial, filtros, exportación y paginación |
| `/panel/accounting/hostings` | billing-cycles, create, email-history, more, send |
| `/panel/accounting/incomes` | create |
| `/panel/accounting/pocket` | create |
| `/panel/accounting/recurring` | create, stats, tags |
| `/panel/accounting/settings` | Acciones servidas por componentes compartidos de configuración y catálogos |
| `/panel/accounting/statements` | collapse, expand |
| `/panel/admins` | create |
| `/panel/blog` | calendar, create, delete, duplicate, edit |
| `/panel/blog/calendar` | create, list, next, previous |
| `/panel/blog/create` | back, create, download, remove, upload |
| `/panel/blog/:id/edit` | back, close, create, link, open-external, publish, remove, upload, view |
| `/panel/clients` | activate, collapse, create, deactivate, delete, edit, expand |
| `/panel/communications` | back, copy, create, view |
| `/panel/defaults` | back |
| `/panel/diagnostics` | close, copy, create, delete, edit, more, open-external, settings |
| `/panel/diagnostics/create` | back |
| `/panel/diagnostics/:id/edit` | back, copy, download, more, refresh, upload |
| `/panel/diagnostics/defaults` | Redirección a `/panel/defaults` |
| `/panel/documents` | create, folders |
| `/panel/documents/create` | back, hide, notes, paste, upload, view |
| `/panel/documents/:id/edit` | back, copy, download, enter-fullscreen, hide, notes, paste, view |
| `/panel/emails` | collapse, create, delete, expand, send |
| `/panel/hour-packages` | create, delete, edit |
| `/panel/hour-packages/create` | back |
| `/panel/hour-packages/:id/edit` | back |
| `/panel/linkedin` | delete, edit, open-external, publish |
| `/panel/linktrees` | copy, delete, edit |
| `/panel/linktrees/:id/edit` | delete, move-down, move-up |
| `/panel/login` | open-external |
| `/panel/mcps` | collapse, copy, expand, generate, regenerate |
| `/panel/portfolio` | create, delete, duplicate, edit |
| `/panel/portfolio/create` | back, download, upload |
| `/panel/portfolio/:id/edit` | back, open-external, upload |
| `/panel/projects` | archive, communications, create, edit, restore, sort-ascending, sort-descending |
| `/panel/proposals` | change-status, close, collapse, copy, create, delete, duplicate, edit, expand, log-activity, message, more, open-external, resend, send, settings, view |
| `/panel/proposals/create` | back, copy, create, download, upload, view |
| `/panel/proposals/:id/edit` | back, refresh |
| `/panel/proposals/defaults` | Redirección a `/panel/defaults` |
| `/panel/proposals/email-deliverability` | back |
| `/panel/proposals/email-templates` | Redirección a `/panel/defaults` |
| `/panel/qr-cards` | copy, delete, download, edit |
| `/panel/styleguide` | archive, close, collapse, delete, duplicate, edit, enable-dark-theme, enable-light-theme, expand, export, more; además muestra las 84 claves |
| `/panel/tasks` | collapse, create, expand |
| `/panel/views` | clear, copy, expand |

Los iconos decorativos, indicadores de estado y emojis que constituyen datos
editables no son acciones. Pueden conservarse, pero el guard exige documentar
la excepción cuando estén dentro de una fila seleccionable.

## Conflictos corregidos

### Una acción representada por símbolos distintos

- **Copiar** aparecía como hojas superpuestas, clipboard o vínculo. En reposo y
  ante fallo conserva `DocumentDuplicateIcon`; sólo un éxito real y temporal lo
  sustituye por el check canónico mientras el texto accesible dice “Copiado”.
- **Cerrar** mezclaba `XMarkIcon`, SVG propios y caracteres `✕`/`×`. Ahora usa
  `XMarkIcon`.
- **Eliminar** mezclaba papelera, `X` y signos menos. Ahora eliminar usa
  `TrashIcon`; quitar una relación o elemento usa `MinusCircleIcon`.
- **Añadir, reenviar, descargar, expandir y previsualizar** mezclaban emojis,
  SVG locales y varios Heroicons. Cada acción quedó ligada a su clave canónica.

### Un símbolo usado por acciones distintas

- La **X** ya no significa indistintamente cerrar, quitar y eliminar.
- Las **hojas/clipboard** ya no alternan entre copiar, duplicar y registrar
  actividad.
- El globo doble queda reservado a **negociar**; abrir el registro de
  **comunicaciones** usa `InboxStackIcon`, así que ambas acciones no comparten
  una señal ambigua.
- La **flecha hacia abajo** distingue descargar (`ArrowDownTrayIcon`), expandir
  (`ChevronDownIcon`) y mover abajo (`ArrowDownIcon`).
- El **check** representa completar, selección o la confirmación temporal de una
  copia verificada; nunca aparece sólo por registrar el clic.

El catálogo verifica además que ningún `iconName` canónico se asigne a dos
acciones diferentes.

## Familia, tamaño y accesibilidad

- Familia única: `@heroicons/vue/24/outline`.
- Tamaño visual de acción: `16 × 16 px`, provisto por `BaseActionIcon`.
- Área táctil: mínimo `44 × 44 px` en dispositivos de puntero grueso, provisto
  por `BaseButton`.
- Un control que contiene solamente un icono usa `BaseActionButton`: recibe
  un solo tooltip en hover/foco y nombre accesible (`aria-label`), sin duplicar
  la ayuda con un `title` nativo.
- El feedback transitorio se expresa con `statusLabel`, `statusTone` y una
  región viva. El mismo tooltip queda visible durante el estado; copiar cambia
  temporalmente a `complete` sólo después de un éxito real y conserva `copy`
  ante fallo para que la acción siga siendo reconocible y reintentable.
- La activación inmediata pertenece a `BaseButton`: presión, salto y aterrizaje
  reiniciables de 420 ms sobre el contenido, sin animar el borde. Reduced motion
  usa un cambio estático de contraste. El objetivo táctil sigue siendo 44 px y
  un estado async conserva su `loading` independiente.

## Catálogo canónico

Todos los iconos de esta tabla pertenecen a Heroicons 24 Outline.

| Clave | Etiqueta por defecto | Icono |
| --- | --- | --- |
| create | Crear | PlusIcon |
| copy | Copiar | DocumentDuplicateIcon |
| duplicate | Duplicar | Square2StackIcon |
| edit | Editar | PencilSquareIcon |
| rename | Renombrar | PencilIcon |
| delete | Eliminar | TrashIcon |
| remove | Quitar | MinusCircleIcon |
| close | Cerrar | XMarkIcon |
| clear | Limpiar | BackspaceIcon |
| more | Acciones | EllipsisVerticalIcon |
| download | Descargar | ArrowDownTrayIcon |
| export | Exportar | DocumentArrowDownIcon |
| upload | Subir | ArrowUpTrayIcon |
| import | Importar | DocumentArrowUpIcon |
| paste | Pegar | ClipboardDocumentIcon |
| attach | Adjuntar | PaperClipIcon |
| move | Mover | FolderArrowDownIcon |
| send | Enviar | PaperAirplaneIcon |
| resend | Reenviar | ArrowPathRoundedSquareIcon |
| email-history | Ver correos | EnvelopeIcon |
| communications | Ver comunicaciones | InboxStackIcon |
| notes | Notas | ChatBubbleBottomCenterTextIcon |
| message | Enviar mensaje | ChatBubbleOvalLeftEllipsisIcon |
| log-activity | Registrar actividad | ClipboardDocumentListIcon |
| open-external | Abrir en otra pestaña | ArrowTopRightOnSquareIcon |
| link | Vincular | LinkIcon |
| unlink | Desvincular | LinkSlashIcon |
| archive | Archivar | ArchiveBoxArrowDownIcon |
| restore | Restaurar | ArrowUturnLeftIcon |
| activate | Activar | PlayCircleIcon |
| deactivate | Desactivar | PauseCircleIcon |
| mute | Silenciar | BellSlashIcon |
| unmute | Reactivar | BellAlertIcon |
| complete | Completar | CheckCircleIcon |
| void | Anular | NoSymbolIcon |
| publish | Publicar | CloudArrowUpIcon |
| unpublish | Retirar publicación | CloudArrowDownIcon |
| change-status | Cambiar estado | ArrowsRightLeftIcon |
| settle | Liquidar | BanknotesIcon |
| generate | Generar documento | DocumentPlusIcon |
| regenerate | Regenerar | SparklesIcon |
| billing-cycles | Ciclos de pago | ClockIcon |
| write-off | Marcar como perdido | XCircleIcon |
| negotiate | Negociar | ChatBubbleLeftRightIcon |
| approve | Aprobar | HandThumbUpIcon |
| reject | Rechazar | HandThumbDownIcon |
| launch | Lanzar | RocketLaunchIcon |
| finish | Finalizar | FlagIcon |
| discount-offer | Enviar oferta | ReceiptPercentIcon |
| analyze | Analizar | WrenchScrewdriverIcon |
| view | Ver | EyeIcon |
| hide | Ocultar | EyeSlashIcon |
| search | Buscar | MagnifyingGlassIcon |
| filter | Filtrar | FunnelIcon |
| refresh | Actualizar | ArrowPathIcon |
| retry | Reintentar | ArrowUturnRightIcon |
| stats | Ver estadísticas | ChartBarIcon |
| calendar | Abrir calendario | CalendarDaysIcon |
| calculate | Calcular | CalculatorIcon |
| list | Ver listado | ListBulletIcon |
| settings | Configuración | Cog6ToothIcon |
| tags | Gestionar etiquetas | TagIcon |
| folders | Carpetas | FolderIcon |
| previous | Anterior | ChevronLeftIcon |
| next | Siguiente | ChevronRightIcon |
| expand | Expandir | ChevronDownIcon |
| collapse | Contraer | ChevronUpIcon |
| move-up | Mover arriba | ArrowUpIcon |
| move-down | Mover abajo | ArrowDownIcon |
| sort | Ordenar | ArrowsUpDownIcon |
| sort-ascending | Orden ascendente | BarsArrowUpIcon |
| sort-descending | Orden descendente | BarsArrowDownIcon |
| enter-fullscreen | Pantalla completa | ArrowsPointingOutIcon |
| exit-fullscreen | Salir de pantalla completa | ArrowsPointingInIcon |
| open-navigation | Abrir navegación | Bars3Icon |
| collapse-sidebar | Contraer barra lateral | ChevronDoubleLeftIcon |
| expand-sidebar | Expandir barra lateral | ChevronDoubleRightIcon |
| enable-dark-theme | Activar tema oscuro | MoonIcon |
| enable-light-theme | Activar tema claro | SunIcon |
| open-platform | Abrir plataforma | WindowIcon |
| add-user | Agregar usuario | UserPlusIcon |
| login-as | Ingresar como usuario | ArrowRightEndOnRectangleIcon |
| back | Volver | ArrowLeftIcon |
| forward | Continuar | ArrowRightIcon |

## Uso y control de regresiones

```vue
<BaseActionButton action="copy" label="Copiar enlace" @click="copyLink" />
<BaseActionIcon action="download" />
```

- `BaseActionIcon` resuelve el componente del catálogo.
- `BaseActionButton` compone icono, área de toque, tooltip y nombre accesible.
- `createPanelActionItem()` agrega acciones canónicas a menús sin permitir que
  el consumidor reemplace su icono.
- `/panel/styleguide` presenta las 84 acciones para inspección visual.
- `npm run check:panel-action-icons` falla ante SVG, emojis, Heroicons directos,
  acciones desconocidas o botones icon-only sin nombre/tooltip dentro del
  alcance del panel. El mismo guard corre en CI.
- `npm run check:icon-interaction-feedback` amplía el contrato a panel,
  plataforma y superficies públicas: rechaza controles icon-only crudos salvo
  una excepción visual justificada en el archivo. También corre en CI.

Para cambiar el símbolo de una acción se modifica una sola entrada en
`frontend/config/panelActions.js`; las pantallas consumidoras no deben importar
ni escoger el icono por su cuenta.
