# Prueba skill `requirement-calculator` — Consolidado de resultados (baseline de calibración)

**Fecha:** 02/07/2026
**Sesión:** prueba de la skill con 3 reportes (2 con un requerimiento cada uno, 1 con varios requerimientos).
**Ubicación canónica:** `.claude/skills/requirement-calculator/validation/test-results.md` (+ los 3 estimates fuente en `validation/estimates/`). **Mantenimiento:** si cambian las reglas de la skill (precios, señales, flujo), actualizar esta suite en el mismo cambio — ver "Suite de validación (baseline)" en el `SKILL.md`.

## Resumen consolidado

| # | Reporte | Requerimiento | Esfuerzo | Horas | Precio (COP) | Documento en /panel/documents |
|---|---------|---------------|----------|-------|--------------|-------------------------------|
| 1 | Vástago — Conteo Diario v3 (Fase 1.5) | Épica CD-01…CD-12: conteo de validación por Grupo+Bodega | 12 filas (11 M + 1 S) — ✅ Sweet spot | 318–463 h | $6,1M–$8,8M (propuesta única) | #23 — `/panel/documents/23/edit` |
| 2 | Vástago — Inventario Detallado v3 (Fase 1.5) | Épica ID-01…ID-14: conteo mensual referencia por referencia | 14 filas (13 M + 1 S) — ✅ Sweet spot | 377–545 h | $7,2M–$10,2M (propuesta única) | #24 — `/panel/documents/24/edit` |
| 3 | Vástago — Funcionalidades adicionales v3 (Fase 1.5) | 11 requerimientos FA-* consolidados (mismo proyecto, dependencias cruzadas) | 27 filas (1 L + 21 M + 2 S + 2 XS + 1 comp.) — ⚠️ Fricción | 696–1004 h | $13,3M–$18,9M (2 fases: cimientos $4,6M–$6,2M / resto $8,7M–$12,7M) | #25 — `/panel/documents/25/edit` |

**Total Fase 1.5 completa (informativo, 3 reportes):** ~1.391–2.012 h / **$26,6M–$37,9M COP** — plan por fases con hitos de facturación; cada bloque cabe individualmente fuera de la zona killer.

> **Recalibración 02/07/2026 (definitiva ÷4):** tras revisar los resultados, el dueño ordenó dividir los rangos de precio por talla entre la tasa de cambio — primero **÷3,5** (provisional) y luego el divisor definitivo **÷4** (los valores originales eran de mercado desarrollado ≈ EE.UU.). Tarifa blended: $75.000/h → **$18.750/h**; horas, niveles y umbrales del semáforo ($12M/$20M) sin cambios. Los tres documentos fueron **reemplazados** con los precios ÷4 (los precios que aparecen arriba y abajo ya son los definitivos).

---

## Detalle por requerimiento

### Reporte 1 — Vástago Conteo Diario v3 (Fase 1.5)

- **Descripción:** reemplazo del conteo por-Ítem (que ajustaba inventario) por un Conteo Diario de validación por Grupo+Bodega: alertas Mín/Máx, traslados 5 días, PDF firmable, histórico, borrador 1 h, correo consolidado 23:00, retiro de ajustes.
- **Nivel de esfuerzo:** 12 funcionalidades (11 `M`, 1 `S`); ninguna fila XL (la épica se descompuso siguiendo el backlog CD-01…CD-12 del propio reporte).
- **Horas estimadas:** 318–463 h.
- **Rango de precio (COP, recalibrado ÷4):** $6,1M–$8,8M — ✅ Sweet spot → propuesta única; la secuencia de 3 bloques queda como orden de entrega.
- **Implicaciones técnicas:** 3 modelos nuevos (DailyCount, DailyCountLine, GroupBranchThreshold), ~7 endpoints nuevos, 2 tareas Huey, rework de la pantalla de conteo, retiro de endpoint/UI de ajustes; cobertura pytest+Jest+Playwright exigida ticket a ticket (+10–15% en todas las filas).
- **Adyacencias:** Inventario Detallado (ajustes), Facturación (prefijos FV/DV/AT reservados), recepción de traslados, reportes sobre el histórico.
- **Estrategia comercial (recalibrada):** cabe en una sola propuesta (sweet spot); orden de entrega recomendado: núcleo → seguimiento/constancia → operación/auditoría. Motores FA-EMP-01/FA-MAIL/FA-PERM excluidos (se cotizan en el reporte 3).
- **Documento generado:** #23 "Estimate: Vástago Conteo Diario Fase 1.5 — 02072026" — `/panel/documents/23/edit`.
- **Bloqueo declarado:** no cerrar precio fijo hasta aclarar §13-J (concurrencia del conteo) y §13-K (alcance de "configurable" en Mín/Máx), y confirmar contratación de FA-EMP-01/FA-MAIL.

### Reporte 2 — Vástago Inventario Detallado v3 (Fase 1.5)

- **Descripción:** módulo nuevo de conteo mensual referencia por referencia con lector de código de barras contra una "foto" del stock: prerrequisito de Conteo Diario válido, código alterno único, captura validada, autoguardado 3 min, segundo conteo solo sobre diferencias, dos tableros de estados, histórico por periodo, lock de concurrencia, vigencia 5 días, correo mensual día 29 + reporte en tiempo real.
- **Nivel de esfuerzo:** 14 funcionalidades (13 `M`, 1 `S`); sin filas XL (descompuesta según el backlog ID-01…ID-14 del reporte).
- **Horas estimadas:** 377–545 h.
- **Rango de precio (COP, recalibrado ÷4):** $7,2M–$10,2M — ✅ Sweet spot → propuesta única.
- **Implicaciones técnicas:** 3 modelos nuevos (DetailedCount, SnapshotLine, CaptureLine) + campo Period, ~12 endpoints nuevos, 2 tareas Huey (autoborrado 5 días, correo día 29), constraint único en código alterno con migración y limpieza de catálogo, lock con select_for_update, 6 pantallas/vistas nuevas.
- **Adyacencias:** ajustes desde el Inventario Detallado (fase posterior pactada), RFID (Fase III), exportar la vista Finalizado, timeout corto del lock, parametrizar los valores hoy fijos.
- **Estrategia comercial (recalibrada):** cabe en una sola propuesta (sweet spot); orden de entrega: catálogo/carga → captura/comparación → ciclo del tablero → robustez/cierre. Sugerencia: adelantar ID-11 (concurrencia) si habrá varios usuarios por sucursal desde el día uno.
- **Documento generado:** #24 "Estimate: Vástago Inventario Detallado Fase 1.5 — 02072026" — `/panel/documents/24/edit`.
- **Bloqueo declarado:** no cerrar precio fijo hasta definir §12-I (liberación del lock), confirmar FA-MAIL (reporte 3) y acordar el plan de limpieza de códigos alternos (bloqueo externo de datos del cliente).
- **Consistencia:** vs. #23 (épica hermana): +15–18% de precio, proporcional a 14 tickets y módulo 100% nuevo vs. 12 tickets adaptando pantalla existente.

### Reporte 3 (múltiples requerimientos) — Vástago Funcionalidades Adicionales v3

- **Descripción:** el resto del alcance de la Fase 1.5 — 11 requerimientos: Históricos/Logs, tipos de precio, Remisión/consignación, formatos de etiqueta, permisos en árbol, correo con marca, Datos de la Empresa + motor PDF, creación al vuelo, registro de usuarios, ajustes menores (galería/360 y bloque Facturación diferidos, sin cotizar).
- **Decisión de agrupación (la prueba clave):** la skill detectó los 11 requerimientos pero los **consolidó en un solo documento** porque pertenecen al mismo proyecto/propuesta (Fase 1.5) con dependencias cruzadas — FA-PERM/FA-MAIL/FA-EMP/FA-PRICE son cimientos del resto y de #23/#24. La regla "un documento por requerimiento **independiente**" no aplica: no son contextos sin relación entre sí.
- **Nivel de esfuerzo:** 27 funcionalidades (1 `L`, 21 `M`, 2 `S`, 2 `XS`, 1 composición); atenuadores y motores anulados/aplicados con anti-doble-cobro explícito frente a #23/#24.
- **Horas / precio (recalibrado ÷4):** 696–1004 h · $13,3M–$18,9M — ⚠️ Fricción (viable, conviene ofrecer fases).
- **Estrategia comercial (recalibrada):** 2 fases — F1 Cimientos (FA-PERM+FA-MAIL+FA-EMP+FA-PRICE, $4,6M–$6,2M, primero: #23/#24 dependen de ellos) · F2 Operación y productividad ($8,7M–$12,7M).
- **Documento generado:** #25 "Estimate: Vástago Funcionalidades Adicionales Fase 1.5 — 02072026" — `/panel/documents/25/edit`.
- **Bloqueos declarados:** medidas de las 4 dimensiones de etiqueta (bloquea F6), reunión de detalle de usuarios (bloquea cierre de F3), licenciamiento de tipografías comerciales.
- **Extra:** el documento incluye la dimensión completa de la Fase 1.5 (3 reportes: $26,6M–$37,9M recalibrado ÷4) como observación informativa, sin calcular semáforo sobre esa suma.

---

## Observaciones sobre la skill (QA)

| Aspecto | Resultado | Notas |
|---------|-----------|-------|
| Detección de requerimientos múltiples | ✅ (R1–R3) | R1/R2: un requerimiento → un documento. R3: detectó los 11 requerimientos y aplicó correctamente la regla de agrupación (consolidar por pertenecer al mismo proyecto/propuesta con dependencias cruzadas, no fragmentar en 11 docs). |
| Calidad de la estimación | ✅ (R1–R3) | Sin filas XL, señales literales citadas, atenuadores por plataforma existente, anti-doble-cobro entre los 3 documentos (motores cotizados una sola vez en #25 y "anulados" en #23/#24). Consistencia entre estimaciones verificada en cada corrida. |
| Persistencia en /panel/documents (carpeta Requirement Estimates) | ✅ (R1–R3) | Documentos #23, #24 y #25 creados por `create_estimate_document`. |
| Postfijo de fecha DDMMYYYY en el documento | ✅ (R1–R3) | `date +%d%m%Y` → 02072026 en los tres títulos. |
| Branding ProjectApp | ⏳ | Markdown puro con callouts; verificar render/PDF en el panel. |
| Retroalimentación del catálogo (pending-signals) | ✅ (R1, R2) | 3 señales por analogía registradas y promovidas al catálogo por orden del dueño (texto sugerido `M`, retiro controlado `S`, lock exclusivo `M`). R3 no generó señales nuevas (todas las filas citaron señal literal o celda espejo). |
| Condiciones de bloqueo declaradas | ✅ (R1–R3) | Cada documento cierra con su callout IMPORTANT (concurrencia/Mín-Máx en #23; lock/FA-MAIL/códigos alternos en #24; medidas de etiqueta/reunión usuarios/tipografías en #25). |
| Convención de IVA: `sin IVA` → `más IVA` (directriz del dueño) | ✅ (24072026) | `market-pricing.md` (premisa base + supuestos declarados) y `SKILL.md` (plantilla del documento + regla estricta) ahora fijan que el valor cotizado **no incluye IVA** y se presenta con la marca `+ IVA` (IVA vigente 19%), nunca con IVA incluido. **Cambio de presentación, no de cálculo:** no altera horas, niveles, señales, modificadores ni precios — el baseline (#23/#24/#25) conserva sus números y no se recalcula; su redacción histórica "sin IVA" se deja intacta como registro de la corrida del 02072026. |
| Recalibración de precios ÷4 (feedback del dueño; ÷3,5 fue provisional) | ✅ (02072026) | `market-pricing.md` → v1.3: tarifa $75.000/h → $18.750/h, tabla de tallas ÷4; umbrales del semáforo intactos ($12M/$20M, disposición de pago absoluta). Documentos #23–#25 reemplazados dos veces (÷3,5 y luego ÷4 definitivo); horas y clasificación sin cambios. Semáforos finales: #23 ✅, #24 ✅, #25 ⚠️ Fricción. |
