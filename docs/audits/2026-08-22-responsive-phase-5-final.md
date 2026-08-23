# Auditoría responsiva final — Fase 5

**Fecha:** 2026-08-22
**Base auditada:** `main` en `996cca44`
**Alcance:** Fases 0–4 del plan PA-75 y fichas absorbidas PA-45, PA-61,
PA-66 y PA-73
**Veredicto:** **amarillo — implementación automatizada aprobada; certificación
física pendiente**

## Resumen ejecutivo

La premisa se cumplió antes de auditar: las cinco fases quedaron integradas en
`main`. La revisión encontró cuatro desviaciones puntuales y las corrigió:

1. Proyectos probaba únicamente filas de escritorio aunque en 412/835 renderiza
   tarjetas y sustituye segmentos por un selector.
2. Blog edit conservaba un breakpoint local con `window.innerWidth`.
3. La acción de completar tarjetas de Kanban dependía de `hover` y medía 24 px.
4. El avatar de Perfil era un `div` clickeable cuya affordance dependía de
   `hover`.

Después de las correcciones, el contrato cubre 101 páginas, 12 módulos y los
cinco viewports exactos; Proyectos, Kanban y Perfil pasan sus matrices 5/5. No
se emite un cierre verde total porque el requerimiento exige dispositivos
físicos y esta sesión sólo dispone de Chromium emulado. También sobrevivieron
variantes cuyo retiro requiere una migración transversal, no una corrección
puntual. Esas desviaciones quedan como fichas nuevas al final de este informe.

## Método y significado de estados

- **Cumple:** coincide con el estándar escrito y tiene evidencia ejecutable.
- **No cumple:** falta el comportamiento o la prueba exigida.
- **Cumple de forma distinta:** funciona, pero usa otra arquitectura,
  representación o evidencia diferente de la definida.

Una variante operable no se convierte en estándar por existir. Las correcciones
puntuales se aplicaron en esta fase; los rediseños quedaron en backlog.

## Premisa: fases integradas

| Fase | PR | Commit en `main` | Estado |
| --- | ---: | --- | --- |
| Fase 0 — estándar e inventario | #243 | `f77e70a4` | Cumple |
| Fase 1 — componentes base | #244 | `5686230d` | Cumple |
| Fase 2 — Contabilidad | #247 | `289a16e4` | Cumple |
| Fase 3 — Documentos, Clientes y Proyectos | #249 | `996cca44` | Cumple |
| Fase 4 — módulos restantes y aceptación | #245 | `8e64f59c` | Cumple |

La auditoría no comenzó sobre ramas sueltas. El único check rojo posterior a la
integración fue `responsive-e2e (projects)` de #249; su causa y corrección
quedan documentadas abajo.

## Resultado por criterio

| # | Criterio | Resultado | Evidencia / razón |
| ---: | --- | --- | --- |
| 1 | Ejecutar sobre las cinco fases en `main` | Cumple | Tabla de commits anterior; base `996cca44`. |
| 2 | Clasificación en tres estados | Cumple | Este informe usa Cumple / No cumple / Cumple de forma distinta. |
| 3 | Corregir hallazgos puntuales y separar rediseños | Cumple | Cuatro correcciones aplicadas; cuatro fichas nuevas para alcance no puntual. |
| 4 | Estándar, cinco anchos, máximo wide e inventario cerrado | Cumple de forma distinta | El proyecto fija 412×915, 835×1195, 1195×835, 1440×900 y 2560×1440 y tope de 1400 px. El estándar fleet del repo está adelantado al canónico del toolkit y el inventario histórico necesitaba esta conciliación. Ficha RSP-F5-02. |
| 5 | PA-45, PA-61, PA-66 y PA-73 cerradas con la solución canónica | Cumple de forma distinta | PA-61/66/73 coinciden técnicamente. PA-45 tiene adopción mayoritaria de `BaseModal`, pero sobreviven overlays locales; no hay objetos PA administrativos en el repo/GitHub para comprobar su estado de tablero. Ficha RSP-F5-03. |
| 6 | Componentes base existentes y usados | Cumple de forma distinta | Existen tabla priorizada, tabs/filtros, modal, drawer, shell, acciones, bulk bar y escala. Persisten consumidores de overlays propios. |
| 7 | Retirar implementaciones propias | No cumple | Quedan superficies `fixed inset-0` fuera de `BaseModal`/`BaseDrawer`; migrarlas todas excede una corrección puntual. Ficha RSP-F5-03. |
| 8 | Ninguna acción depende sólo de hover | Cumple | Kanban y Perfil corregidos; el gate nuevo rechaza `<button>`/`<a>` ocultos por `group-hover` sin alternativa táctil o de foco. |
| 9 | Contabilidad completa | Cumple de forma distinta | Los 12 tabs, prioridades, agrupación, saldo de Bolsillo, modales y filtros usan el contrato. El guion 12×5 existe, pero el tag automático ejecuta una muestra representativa y no sustituye la pasada física completa. Fichas RSP-F5-01/04. |
| 10 | Documentos, Clientes y Proyectos | Cumple | Drawer de carpetas, archivados, tarjetas/filtros y cambio guiado están integrados. Proyectos quedó verde 5/5 después de alinear fila/tarjeta y segmentos/select. |
| 11 | Comercial, Emails, Canvas, Dashboard, Contenido, MCP y públicas | Cumple de forma distinta | Producto y checks representativos están integrados; el guion por tag no ejecuta todavía cada punto escrito de cada checklist. Ficha RSP-F5-04. |
| 12 | Guion completo en dispositivos reales | No cumple | No hay device lab, sesión remota ni artefactos de teclado/barras de sistema disponibles. Playwright emula viewport/touch, no hardware físico. Ficha RSP-F5-01. |
| 13 | Regresión en portátil y monitor grande | Cumple de forma distinta | Las matrices 1440×900 y 2560×1440 pasan sin overflow y con tope de 1400 px; falta ratificación física del criterio 12. |
| 14 | Apoyo de QA y responsividad | Cumple de forma distinta | QA independiente aprobó el lote: unit 7/7, flujos de Perfil 2/2 y matriz Perfil/Kanban 15/15. `responsive-module` reconoce la configuración exacta, pero no puede registrar `applied` mientras el estándar fleet esté `stale`. Ficha RSP-F5-02. |
| 15 | Informe, correcciones, fichas y pendientes | Cumple | Este documento y `tasks/tasks_plan.md` son la trazabilidad versionada. |

## Estado por módulo

| Módulo de aceptación | Resultado | Evidencia principal | Residual |
| --- | --- | --- | --- |
| Fundamentos | Cumple | Config única, shell 1400 px, primitives y styleguide. | Ninguno puntual. |
| Contabilidad | Cumple de forma distinta | 12 rutas, navegación/filtros y políticas de columna; guion 12×5. | Automatización representativa y certificación física pendientes. |
| Documentos | Cumple | Carpetas en drawer compacto, nombres legibles, archivados y acciones táctiles. | Ninguno puntual. |
| Clientes y Plataforma | Cumple de forma distinta | Tarjetas/filtros de Clientes; Perfil y Kanban añadidos al tag y verdes 5/5. | Un módulo responsivo agrupa flows `admin` y `platform`, que el ledger no puede medir como una sola unidad. |
| Proyectos | Cumple | Tarjetas en 412/835, tabla desde 1195, alcance y archivados verdes 5/5. | Ninguno después de esta fase. |
| Comercial | Cumple de forma distinta | Tabla comparativa, filtros y E2E representativo. | Overlays propios en propuestas/diagnósticos heredados. |
| Emails | Cumple de forma distinta | Compositor responsivo y tag ejecutable. | El tag no recorre cada punto del guion escrito. |
| Canvas | Cumple de forma distinta | Stack/split y guard de salida bajo contrato. | El tag representa el guard, no todo el recorrido editor/preview. |
| Dashboard | Cumple de forma distinta | Dashboard y shell pasan cinco anchos. | Admins/Tareas conservan overlays o formularios locales. |
| Contenido | Cumple de forma distinta | Blog/LinkedIn/Portfolio/QR tienen checks; Blog usa ya el breakpoint compartido. | Blog edit conserva un overlay propio; el tag no recorre todas las subfamilias. |
| MCP | Cumple | Conector representativo pasa los cinco perfiles. | Certificación física transversal pendiente. |
| Públicas | Cumple | Marketing, propuesta, diagnóstico y linktree tienen checks responsivos. | Certificación física transversal pendiente. |

## Conciliación del inventario RSP-01…RSP-16

| ID | Estado final | Evidencia / residual |
| --- | --- | --- |
| RSP-01 | Cumple | Tabs densos usan selector/tira compartidos. |
| RSP-02 | Cumple | Drawer hasta 1023 y sidebar desde 1024. |
| RSP-03 | Cumple | Shell limita contenido general a 1400 px. |
| RSP-04 | Cumple | `BaseFilterTabs` y subnav contable comparten umbral 1024. |
| RSP-05 | Cumple | Tablas comparativas declaran prioridad de negocio. |
| RSP-06 | Cumple | QR y Linktrees adoptan representación exploratoria compacta. |
| RSP-07 | Cumple de forma distinta | `BaseModal` es canónico y ampliamente usado, pero sobreviven overlays locales. RSP-F5-03. |
| RSP-08 | Cumple | Primitives de formulario apilan según capacidad. |
| RSP-09 | Cumple | Barras masivas usan la primitive compartida. |
| RSP-10 | Cumple | Canvas/Documentos apilan antes de perder mínimos de panel. |
| RSP-11 | Cumple | Listas exploratorias concentran acciones en menú. |
| RSP-12 | Cumple | Clientes usa tarjetas/detalles compactos. |
| RSP-13 | Cumple | Carpetas son drawer en 412/835 y zona legible desde 1195. |
| RSP-14 | Cumple | Blog edit migró a `useIsMobile`; el gate prohíbe breakpoints JS locales en páginas del panel. |
| RSP-15 | Cumple | Headers compactos preservan título y CTA. |
| RSP-16 | Cumple | Overview contable usa el vocabulario compartido. |

## Fichas absorbidas

| Ficha | Resultado técnico | Decisión final |
| --- | --- | --- |
| PA-45 — modales y saltos | Cumple de forma distinta | Mantener absorbida, pero no declarar migración completa hasta cerrar RSP-F5-03. |
| PA-61 — panel de carpetas | Cumple | La solución es `BaseDrawer`/zona ancha del estándar, no una variante local. |
| PA-66 — tira de filtros | Cumple | `ProposalFilterTabs` conserva compatibilidad y delega en `BaseFilterTabs`. |
| PA-73 — tabs contables móviles | Cumple | Selector bajo 1024 y tira compartida desde 1024. |

## Correcciones aplicadas

| Hallazgo | Corrección | Protección contra regresión |
| --- | --- | --- |
| El E2E de Proyectos asumía tabla y segmentos en todos los anchos. | Selector de entidad fila/tarjeta y operación segmento/select según la representación real. | `@responsive:projects`: 5/5. |
| Blog edit inventaba `window.innerWidth < 1024`. | Migración a `useIsMobile()` y eliminación del listener local. | Gate estático de breakpoints JS locales. |
| Completar tarjeta de Kanban era 24×24 y sólo aparecía por hover. | `touch-reveal`, target táctil, foco visible y nombre accesible. | `@responsive:clients`: Kanban 5/5 y medición 44×44 en touch. |
| Avatar de Perfil era un `div` clickeable y sólo mostraba affordance por hover. | Botón semántico, nombre accesible, foco visible y target táctil. El selector tiene flow propio y el primer campo del formulario quedó asociado a su label. | Perfil 5/5, medición 44×44 en touch; selector y guardado 2/2. |
| El ledger infería 835×1194, breakpoints genéricos y 8 módulos. | Overrides en `.testquality.yml`; helper canónico consumido por el runner. | Test unitario fija 835×1195 y rechaza aliases desconocidos. |
| El contrato sólo fijaba anchos y presencia de tags. | Validación de alturas, breakpoints locales y controles hover-only. | `npm run check:responsive-contract`. |

## Evidencia automatizada

| Verificación | Resultado |
| --- | --- |
| Contrato estático | 101 vistas / 12 módulos / 5 viewports |
| Config responsive unit | 7/7 |
| Design tokens guard | Aprobado |
| Proyectos — alcance/archivados | 5/5 viewports |
| Plataforma — Perfil | 5/5 viewports |
| Plataforma — Kanban | 5/5 viewports |
| Plataforma — Perfil/Kanban focal | 15/15; render, foco visible y contrato táctil en cinco viewports |
| Perfil — selector y guardado | 2/2; `FileChooser` de imagen/archivo único y PATCH `first_name` con feedback |
| Flow registry | 301 referencias / 331 definiciones, sincronizado y fresco |
| Build Nuxt de producción | Aprobado |
| QA Verifier focal | **APPROVED**; unit 0 errores, E2E 0 errores, 13 advertencias baseline no bloqueantes |
| QA Auditor | **APPROVED**; todos los tests modificados `KEEP`, sin junk, duplicados ni ubicación incorrecta |
| QA global determinista | 258 covered, 39 partial, 0 junk-only, 0 unvalidated, 0 missing; amarillo por 1 gap negativo y 1473 advertencias históricas |
| CI de Fase 3 | Backend, unit, 15 shards E2E, quality gate y 11/12 módulos responsivos aprobados; el único rojo de Proyectos queda corregido en esta fase. |

Estas pruebas usan Chromium con viewport y capacidades táctiles emuladas. No son
evidencia de teclado en pantalla, barras del sistema, safe areas o particularidades
de navegador/hardware real.

## Fichas nuevas

| ID | P | Estado | Hallazgo | Criterio de cierre |
| --- | ---: | --- | --- | --- |
| RSP-F5-01 | P0 | Backlog | Falta certificación en hardware real para los cinco perfiles. | Ejecutar el guion consolidado en dispositivos físicos o device lab; adjuntar evidencia de touch, teclado, barras/safe-area, portátil y monitor wide; cero regresiones abiertas. |
| RSP-F5-02 | P1 | Backlog externo | `docs/RESPONSIVE_STANDARDS.md` del proyecto usa `/responsive-module`, pero el canónico del toolkit aún usa `/responsive-pass`; el ledger queda `standard=stale` y ausente. | Corregir el canónico en `vps-ops-toolkit`, sincronizar sin perder la versión nueva, sembrar ledger y registrar QA medido. |
| RSP-F5-03 | P1 | Backlog | Persisten overlays `fixed inset-0` propios en Panel/Plataforma/Públicas, pese a que `BaseModal`/`BaseDrawer` son canónicos. | Inventariar cada overlay como modal, drawer, workspace o excepción; migrar consumidores y documentar las excepciones legítimas; cero modal paralelo sin justificación. |
| RSP-F5-04 | P1 | Backlog | La aceptación usa cinco `projects` globales de Playwright y un tag representativo por módulo; además `clients` agrupa flows `admin`/`platform`, que el ledger no relaciona. | Adoptar matrices acotadas por spec o versionar la excepción; mapear módulos responsivos a flows; cada punto del checklist debe tener un E2E calificable y medible por QA. |

## Pendientes y condición de cierre total

El código puede integrarse porque las desviaciones puntuales están corregidas y
la regresión automatizada queda verde. El plan completo sólo podrá declararse
**verde** cuando RSP-F5-01 aporte evidencia física y RSP-F5-03/04 cierren o
versionen formalmente sus variantes. RSP-F5-02 no bloquea el producto, pero sí
el registro confiable de la skill de responsividad.
