# Barrido transversal — saltos de línea y anchos de modal — 2026-08-27

**Veredicto inicial: 🟡 el defecto es sistémico y nace en cuatro primitivas compartidas.**
El barrido se hizo antes de corregir: 61 superficies con `BaseModal`, 32 archivos con
controles segmentados, 25 con badges y 19 con filas de formulario. Los cinco casos
reportados se reproducen por la misma combinación: ancho semántico incompleto,
contenido interno quebrable y ayudas reservadas dentro de una sola columna.

## Hallazgos confirmados

| Superficie | Hallazgo | Causa compartida | Corrección transversal |
|---|---|---|---|
| Crear y editar cliente | `Código de facturación (opcional)` puede elevar sólo su columna; editar además usa el ancho legacy `md` mientras crear usa `form`. | Los dos modales no comparten contrato de ancho y la etiqueta decide la posición de su control. | Unificar ambos en `kind="form"`; etiquetas cortas atómicas y bandas compartidas de etiqueta/control/error. |
| Nueva cuenta de cobro | `Del cliente (N)` y los estados del ingreso vinculado pueden separar el conteo; el riesgo aumenta con cuatro dígitos. | `BaseSegmented` permite quiebre interno y el asistente usa un ancho de detalle, no uno propio. | Opción segmentada indivisible, grupo reordenable y `kind="wizard"`. |
| Filtros de Clientes | `Huérfanos (N)` puede dejar el conteo en una segunda línea. | Mismo `BaseSegmented`; el conteo es texto quebrable. | Corregir la primitiva y probar con `9999`. |
| Filtros de Documentos | La ayuda de Proyecto baja esa columna y deja `Sin proyecto` por debajo de su selector. | Flex con bloques de alturas independientes; el botón se alinea con todo el bloque. | `BaseFormRow` con ayuda bajo el grupo y una celda de acción alineada con el control. |
| Estados de Documentos | `⚠ Solucionar bug` se parte tanto en filtros como en filas del listado. | `BaseBadge` fuerza `flex-wrap`, `whitespace-normal` y `overflow-wrap:anywhere`. | Badge atómico por defecto en el componente compartido. |

## Hallazgos adicionales del barrido

1. `BaseModal` sólo distingue `confirm`, `form`, `detail` y `workspace`. Faltan los
   contratos para formularios de dos columnas y asistentes, por lo que los consumidores
   siguen mezclando `kind` con tamaños legacy que ya no tienen efecto.
2. `BaseFormRow` alinea etiqueta, control y una tercera banda de hint/error. La banda evita
   que la fila siguiente se tuerza, pero reserva aire vacío y deja la ayuda asociada a una
   única columna. Se encontraron ayudas dentro de filas compartidas en:
   `RecurringPaymentFormModal`, `IncomeFormModal`, `HostingFormModal`,
   `CollectionAccountFormModal`, `ProjectFormModal`, la edición de diagnósticos, la edición
   de Linktrees y el styleguide.
3. Hay rejillas manuales de formulario dentro de modal en
   `IncomeLiquidateModal`, `PocketMovementFormModal`,
   `ConfidentialityParamsModal` y `ContractParamsModal`. Son candidatas a las bandas
   compartidas; las rejillas de `CollectionAccountDetailModal`, `IncomeDetailModal` y
   `StateHistoryModal` son de lectura/detalle y no deben convertirse en campos.
4. Los 32 consumidores de controles segmentados heredan el mismo riesgo aunque hoy no
   todos tengan conteos. La corrección pertenece a `BaseSegmented` y
   `BaseSegmentedMulti`; el grupo puede repartirse o saltar por opciones, pero cada opción
   conserva una sola línea y una altura uniforme.
5. Los 25 consumidores de `BaseBadge` son estados, métricas o chips cortos. El estado de
   Documentos confirma que el default debe ser atómico; se conserva una salida explícita
   para contenido arbitrario que de verdad necesite envolver.
6. `BaseButton` ya une icono y texto en un flex, pero el texto anónimo todavía puede
   envolver. El default debe ser atómico y los CTA de frase larga deben optar
   explícitamente por texto envolvente.

## Contratos de ancho resultantes

| Tipo | Ancho máximo desde 640 px | Uso |
|---|---:|---|
| `confirm` | 28 rem | confirmación breve |
| `form` | 42 rem | formulario simple o de una columna |
| `form-wide` | 64 rem | formulario habitual de dos columnas |
| `wizard` | 80 rem | asistente de varios pasos |
| `detail` | 64 rem | consulta o detalle |
| `workspace` | `min(90vw, 100rem)` | visor o espacio de trabajo |

Por debajo de 640 px todos conservan el contrato existente de ancho disponible completo;
las filas pasan a una columna y los grupos de opciones se reorganizan entre botones.

## Excepciones verificadas

- Los títulos largos de la tabla de Documentos ya tienen detección real de recorte,
  consulta completa por cursor/toque, ancho persistido, mínimo/máximo y doble clic para
  restablecer. Se conserva esa implementación y se cubre sólo como regresión.
- Las rejillas de resúmenes, métricas, historiales y vistas previas no son formularios y no
  participan de las bandas etiqueta/control/error.
- `/panel/documents` se mantiene. El cambio a **Gestor Documental** es sólo de rótulo y
  descripción pública; identificadores, modelos, endpoints y slug MCP permanecen estables.

## Criterio de prueba

- Texto real más largo de cada consumidor confirmado.
- Conteos `9999` en Clientes y cuenta de cobro.
- Geometría de controles y acciones en 412×915, 835×1195, 1195×835 y 1440×900.
- Mismo alto para opciones hermanas y estado `Solucionar bug` en sus dos apariciones.

## Resultado de la corrección

**Veredicto final: 🟢 corregido en las primitivas compartidas y en los casos
confirmados.** Crear y editar cliente usan el mismo contrato; los filtros de
Clientes y la cuenta de cobro conservan conteos de cuatro dígitos en una línea;
la ayuda de Proyecto en Documentos queda bajo el grupo completo y su acción se
centra exactamente contra el selector; el badge `⚠ Solucionar bug` permanece
atómico en filtros y listado. Los formularios de dos columnas y asistentes
detectados en el barrido adoptaron los anchos y bandas comunes.

Validación registrada:

- pruebas Jest focalizadas de las primitivas y consumidores confirmados;
- prueba Django del conector MCP y `makemigrations --check --dry-run` sin drift;
- build de producción Nuxt completo;
- contratos de diseño, responsividad y catálogo de vistas verdes;
- Playwright local con API simulada: 2/2 casos, incluyendo `9999`, badge con
  icono y alineación campo/acción con diferencia medida de 0 px;
- QA final con gate de paridad CI en cero errores; el auditor clasificó como
  `KEEP` todas las pruebas tras reemplazar selectores posicionales y fijar
  explícitamente los conteos `9999`;
- barrido de referencias visibles y ocultas sin apariciones de los rótulos
  anteriores fuera de migraciones históricas; las skills que
  publican al MCP quedaron sincronizadas en sus superficies Codex y Claude;
- flow-map fresco, registro derivado y tags E2E sincronizados.
