# Contable — comparación campos del formulario vs filtros disponibles

**Fecha:** 2026-08-17
**Motivo:** punto 10 del requerimiento de filtros del Bolsillo. El criterio de
*insumo* dice que **todo campo que el formulario pide al crear o editar debería
poder usarse como filtro después**. Este documento aplica ese criterio a los 12
tabs del módulo contable para dimensionar el backlog, en vez de decidir tab por
tab qué merece filtro.

**Regla aplicada:** los campos estructurados (selects, segmentados, fechas,
montos, booleanos) reciben control propio en el panel; los de **texto libre**
se consideran cubiertos si están en los `searchFields` del buscador debounced.
Un campo de texto libre que no está ni en el buscador cuenta como brecha.

---

## Resumen: tamaño de la brecha por tab

| Tab | Campos del form | Controles de filtro | Brecha | Panel compartido | Pestañas guardadas | Conteos |
|---|---|---|---|---|---|---|
| Extractos | 8 + 8 (dos forms) | 2 (año, tarjeta) | **16** | ✗ bespoke | ✗ | ✗ |
| Cuentas de cobro | 18 | 5 + búsqueda | **14** | ✓ | ✓ (3 builtin, 0 sembradas) | ✗ |
| Ingresos | 15 | 10 + búsqueda | 6 | ✓ | ✓ (5 builtin + 5 sembradas) | ✗ |
| Hostings | 15 | 6 + búsqueda | 6 | ✓ | ✓ (2 builtin + 4 sembradas) | ✗ |
| Recurrentes | 13 | 7 + búsqueda | 4 | ✓ | ✓ (5 sembradas) | ✗ |
| Gastos | 9 | 6 + búsqueda | 3 | ✓ | ✓ (5 sembradas) | ✗ |
| **Bolsillo** | 6 | 5 + búsqueda | **0** ✅ | ✓ | ✓ (6 sembradas) | **✓** |
| Ads | 5 | 4, **sin búsqueda** | 1 | ✓ | ✓ (3 sembradas) | ✗ |
| Tarjetas | 4 | 3 + búsqueda | 1 | ✓ | ✓ (0 sembradas) | ✗ |
| Historial | 0 (read-only) | 8-10 + búsqueda | 0 | ✓ | ✓ ×2 vistas | ✓ |
| Resumen | n/a (dashboard) | 1 (año) | n/a | ✗ | ✗ | ✗ |
| Configuración | n/a (config) | 0 | n/a | ✗ | administra el manager | ✗ |

Bolsillo queda en 0 con la entrega de este requerimiento; era 2 antes.

**Nota sobre el orden de prioridad:** el tamaño de la brecha no es la
prioridad. Extractos y Cuentas de cobro encabezan por número, pero el criterio
que importa es *cuántas veces se hace la consulta que hoy no se puede hacer*.
En Cuentas de cobro `due_date` es el caso claro: no hay filtro de vencimiento y
la única forma de llegar es la pestaña builtin "Vencidas".

---

## Detalle por tab

La lista de tabs sale de `frontend/components/accounting/AccountingSubnav.vue:28-41`.
El filtrado es **client-side** en todos los tabs salvo Historial; los "query
params" que se nombran son los del `EXPORT_MAPPING` de cada página, que es lo
que viaja al servidor para el export.

### 1. Resumen — `pages/panel/accounting/index.vue`
Dashboard, sin lista que filtrar. Único control: selector de año
(`index.vue:12-18`). El atajo "Nuevo ingreso" abre `IncomeFormModal`. No aplica.

### 2. Bolsillo — `pages/panel/accounting/pocket.vue` ✅
**Form** (`components/accounting/PocketMovementFormModal.vue:106-172`): Concepto\*,
Fecha\*, Dirección\*, Contabilidad/"Atribuir a"\*, Valor\*, Notas.
**Filtros**: Fecha (daterange), Tipo (segmented), Valor (range), **Atribuir a**
(multi), **Vínculo** (segmented), búsqueda sobre `concept` + `notes`.
**Brecha: 0.** No existe categoría ni método de pago en este formulario — sólo
en Gastos y Recurrentes respectivamente.

### 3. Ingresos — `pages/panel/accounting/incomes.vue`
**Form** (`IncomeFormModal.vue:432-624`, 15 campos): Concepto\*, Cliente,
Proyecto, Origen\*, Tipo\*, Mes/Fecha\*, Inicio y Fin del período\*, Periodicidad\*,
Contabilidad, Destino, Valor\*, split Gustavo, split Carlos, Notas.
**Filtros**: Mes, Total, Tipo, Cobro, Avisos, Socio, Contabilidad, Cliente,
Proyecto, Origen + búsqueda.
**Brecha (6):** `destination`, `period_start`, `period_end`, `period_cadence`,
`gustavo_amount`, `carlos_amount`.

### 4. Gastos — `pages/panel/accounting/expenses.vue`
**Form** (`ExpenseFormModal.vue:103-192`): Concepto\*, Fecha/Mes\*, Categoría,
Contabilidad, Total\*, split Gustavo, split Carlos, "Registrar egreso en
bolsillo", Notas.
**Filtros**: Mes, Total, Categoría, Contabilidad, Naturaleza, Tipo de deducción
+ búsqueda.
**Brecha (3):** `gustavo_amount`, `carlos_amount`, `register_in_pocket` — es
decir, *"salió del bolsillo o no"* no se puede consultar, siendo la bisagra con
el tab de Bolsillo.

### 5. Hostings — `pages/panel/accounting/hostings.vue`
**Form** (`HostingFormModal.vue:186-350`, 15 campos).
**Filtros**: Cliente, Proyecto, Modalidad, Valor/mes, Vencimiento, Estado +
búsqueda.
**Brecha (6):** `client_email`, `client_contact_name`, `client_identification`,
`benefit`, `valid_from`, `payment_per_cycle`.

### 6. Cuentas de cobro — `pages/panel/accounting/collections.vue`
**Form** (`CollectionAccountFormModal.vue:808-1193`, 18 campos incluyendo el
bloque de datos del cliente del documento).
**Filtros**: Cliente, Proyecto, Emisión, Total + Estado (segmented **fuera** del
panel, `collections.vue:76-81`) + búsqueda.
**Brecha (14):** `income` (el ingreso vinculado), `billing_description`,
`period_start`, `period_end`, `city`, `term`, `payment_term_days`,
**`due_date`**, y los cinco `customer.*` (email, tipo y número de
identificación, contacto, dirección), más `notes`.
Sin `EXPORT_MAPPING` en esta página.

### 7. Recurrentes — `pages/panel/accounting/recurring.vue`
**Form** (`RecurringPaymentFormModal.vue:136-244`, 13 campos).
**Filtros**: Categoría, Frecuencia, Método de pago, Moneda, Tipo, Precio,
Estado + búsqueda.
**Brecha (4):** `cop_equivalent`, `custom_months`, `cycle_anchor_date`,
`billing_day` — no hay forma de preguntar *"qué se cobra este mes"*.

### 8. Ads — `pages/panel/accounting/ads.vue`
**Form** (`AdSpendFormModal.vue:64-106`): Fecha\*, Plataforma, Tarjeta origen,
Valor\*, Notas.
**Filtros**: Fecha, Tarjeta, Plataforma, Valor. **Sin caja de búsqueda.**
**Brecha (1):** `notes`, y sin buscador no hay dónde alojarlo.

### 9. Tarjetas — `pages/panel/accounting/cards.vue`
**Form** (`CardSnapshotFormModal.vue:104-157`): Tarjeta\*, Fecha\*, Disponible\*,
Notas. El catálogo de tarjetas vive en Configuración
(`AccountingCardCatalog.vue:138-165`).
**Filtros**: Fecha, Deuda (sobre el derivado `debt_amount`), Tarjeta + búsqueda.
**Brecha (1):** `available_amount` — se captura el disponible y sólo se puede
filtrar por la deuda derivada.

### 10. Extractos — `pages/panel/accounting/statements.vue`
**Forms**: cabecera (`StatementHeaderFormModal.vue:63-117`, 8 campos) +
transacción (inline, `statements.vue:122-175`, 8 campos).
**Filtros**: año y tarjeta. **Panel bespoke**: no usa `AccountingFilterPanel`.
**Brecha (16):** todos. No hay búsqueda, ni filtro por monto, fecha, comercio o
categoría sobre las transacciones.

### 11. Historial — `pages/panel/accounting/history.vue`
Read-only, sin formulario. **Brecha 0** y es el único tab con filtros en la URL
(`syncFiltersToUrl: true`) y con conteos por pestaña.

### 12. Configuración — `pages/panel/accounting/settings.vue`
Página de configuración; hospeda el manager de pestañas guardadas
(`settings.vue:252-259`, lista de vistas en `:454-463`).

---

## Hallazgos transversales (backlog, no se tocan en esta entrega)

1. **Tarjetas y Cuentas de cobro tienen pestañas propias pero no figuran en el
   manager de Configuración** (`settings.vue:454-463`) y no tienen filas
   sembradas. Su botón "Restablecer" es inalcanzable: el usuario puede crear
   pestañas y no tiene forma de volver al estado de fábrica. Es un defecto, no
   una brecha de filtro.
2. **Ads declara `search: 'q'` en su `EXPORT_MAPPING`** pero la página no
   renderiza caja de búsqueda: el parámetro existe para el export y no para la
   vista.
3. **Extractos quedó fuera del sistema compartido**: panel propio, sin
   `useAccountingFilters`, sin pestañas. Es el tab que más costaría alinear y el
   único donde la brecha es estructural y no incremental.
4. **Los conteos entre paréntesis** están cableados sólo en Historial (server-side)
   y ahora en Bolsillo (client-side, sin endpoint nuevo: el dataset completo ya
   está en el store). Los demás tabs pasan `counts` vacío y el badge no
   renderiza. El patrón de Bolsillo (`countTabs` en `useAccountingFilters`) es
   reutilizable tal cual en los otros seis tabs con pestañas.
5. **`notes` no es filtro dedicado en ningún tab.** Está en `searchFields` de
   ingresos, gastos, hostings, recurrentes, tarjetas y —desde esta entrega—
   bolsillo. Sigue **fuera** en ads (que no tiene buscador).
6. **Sólo Historial persiste los filtros en la URL.** Los demás restauran estado
   desde el id de la pestaña, así que un recorte armado a mano no se puede
   compartir por link.

## Orden sugerido si se sigue

1. **Cuentas de cobro** — `due_date` primero (la consulta que se repite), luego
   el bloque `customer.*`. Además hay que meterla al manager de Configuración.
2. **Tarjetas** — `available_amount` + entrada en el manager. Barato.
3. **Conteos en los seis tabs restantes** — reutilizar `countTabs`; es el mismo
   cambio seis veces.
4. **Gastos** — `register_in_pocket`, que cierra el circuito con Bolsillo.
5. **Recurrentes** — `billing_day` / `cycle_anchor_date` como "qué se cobra este mes".
6. **Ads** — sumar buscador (y con eso `notes` queda cubierto).
7. **Extractos** — el más grande; evaluar si se migra al panel compartido antes
   de sumarle filtros uno por uno.
