# Esfuerzo, Precio y Reglas de Mercado — Calculadora de Requerimientos (v1.3)

> Complemento de `effort-indicators.md`. Traduce el nivel de esfuerzo a horas y precio COP, y define las reglas comerciales del mercado colombiano.

## Premisas base

- **Implementación web por defecto.** La calculadora está calibrada para web. La plataforma solo entra como modificador excluyente: web = sin recargo · PWA = `+30%` · app móvil nativa (iOS/Android + tiendas) = `+60%` (aplicado al final, `×1,6` sobre el resultado ya modificado).
- **Desarrollo desde cero (greenfield)** salvo que la descripción declare que se extiende algo existente.
- **Cliente PYME colombiano.** Precios en **COP, sin IVA**.
- **Tarifa de venta blended de referencia: ≈ $18.750 COP/hora** (≈ US$5,4 a TRM ≈ $3.443/USD). *Recalibrada el 02/07/2026:* la calibración anterior (≈ $75.000/h) producía precios justos para un mercado desarrollado (≈ EE.UU.), no para la realidad colombiana; por directriz del dueño los rangos se dividieron **÷4**.
- **Killer: $20.000.000 COP** — una propuesta (la **suma** de los requerimientos, no un ítem suelto) por encima de ese techo tiende a ser rechazada. Obligatorio fragmentar.
- **Granularidad:** se estima funcionalidad por funcionalidad; el proyecto es la suma.

### Qué incluye y qué no (por defecto)

- **Incluye:** análisis, desarrollo, pruebas básicas, despliegue inicial y garantía corta de estabilización.
- **No incluye:** infraestructura/hosting recurrente, licencias de terceros, soporte continuo, capacitación extensa ni migración de datos legados — salvo mención explícita en el alcance.

## Niveles: esfuerzo → horas → precio

| Nivel | Pts | Perfil típico | Horas | Precio COP | ≈ USD |
|---|---|---|---|---|---|
| **XS** | 1 | Cambio de configuración, un campo, validación básica, enlace simple. | 2–7 | $40K – $130K | $12–38 |
| **S** | 2 | Ajuste de UI/plantilla, modal, correo básico, contador simple. | 7–20 | $130K – $380K | $38–110 |
| **M** | 3 | CRUD estándar con extras, generación de archivos, permisos, lógica condicional. A menudo se apoya en algo existente. | 20–50 | $380K – $880K | $110–255 |
| **L** | 5 | **Un feature completo desde cero**: backend + frontend robustos (a veces + una integración, que lo lleva al techo del rango). | 55–90 | $1,0M – $1,8M | $290–510 |
| **XL** | 8 | **Referencia de magnitud, NO cotizable como ítem.** Exige descomposición obligatoria en 2+ filas `S`/`M`/`L` (cada una suele ser un L). El rango solo sirve para dimensionar la conversación. | 90–200 | $1,8M – $3,8M | $510–1.090 |

**Fuente de verdad:** la **columna de precio** manda (es la calibración comercial del dueño frente al mercado); las horas son indicativas. Los pequeños desfases entre horas × tarifa y el rango de precio, y el colchón de horas entre `M` (50) y `L` (55), son deliberados: margen pre-modificador. Los puntos (Pts) son un *shorthand* de magnitud, no entran en fórmulas.

## Orden de cálculo

1. **Nivel base por funcionalidad** — el indicador de esfuerzo más alto que la describe fija XS/S/M/L/XL, **citando la señal literal** del catálogo.
2. **Modificadores** — recorrer la tabla completa marcando cuáles aplican. Fórmula:

   `horas = base × (1 + Σ% aditivos) × factor transversal + horas fijas (cron)`

   Si aplica app móvil nativa: `× 1,6` **al final**, sobre el resultado ya modificado. Anti-doble-conteo: *Pantalla nueva* y *Modelo de datos* nunca sobre un `L`.
3. **Rango, no punto** — el precio siempre se expresa como rango (piso–techo). El piso usa el extremo bajo de horas; el techo, el alto.
4. **Suma y chequeo de killer** — se suman las funcionalidades (verificar que la suma de filas = total y que piso ≤ techo). Si el techo total supera $20M, se activan las reglas de mercado (fases o versiones).

## Zonas de precio (sobre la SUMA de la propuesta)

| Zona | Rango total | Acción |
|---|---|---|
| ✅ **SWEET SPOT** | < $12M | Propuesta única, sin fricción. |
| ⚠️ **FRICCIÓN** | $12M – $20M | Viable, pero conviene ofrecer fases o versionado para bajar el ticket inicial. |
| ⛔ **KILLER** | > $20M | Rechazo probable. Obligatorio fragmentar antes de presentar. |

> **Nota (recalibración 02/07/2026):** los umbrales del semáforo **no** se dividieron con la tarifa. Miden la **disposición de pago absoluta** del cliente colombiano por propuesta (cuánto está dispuesto a firmar), no el costo de producción — por eso permanecen en $12M/$20M aunque los precios por talla bajaran ÷4.

### Estrategia A — Fragmentación por fases

- Cada fase es **desplegable y útil sola** (nunca "medio CRUD").
- Cada fase queda idealmente en **≤ $12–15M** para mantenerse fuera de la zona killer.

### Estrategia B — Versionado (V1 + posteriores)

- **V1** = núcleo operativo que el cliente *necesita* para arrancar.
- Se difiere a V2/V3 lo que *mejora* la operación pero no la bloquea: reportes, notificaciones, filtros guardados, dashboards.
- Las **adyacencias** son las candidatas naturales a versiones posteriores.

## Adyacencias — mapa "abre la puerta"

Anticiparlas siempre: no para cobrarlas de una, sino para ordenarlas en fases/versiones y no quedar cortos en el análisis.

| Disparador | Abre la puerta a |
|---|---|
| CRUD con tabla / listado | Filtros · ordenamiento · paginación · búsqueda · exportar (Excel/PDF) · acciones masivas · columnas configurables |
| Filtros | Preferencias guardadas · filtros combinados/avanzados · vistas guardadas por usuario |
| Cualquier dato listado | Reportes (PDF/Excel) · dashboards · KPIs · envío programado de reportes |
| Cambios de estado / eventos | Notificaciones in-app · correo · push · bitácora de eventos |
| Acciones de usuario | Trazabilidad / auditoría (quién, cuándo, qué) · historial de cambios |
| Formularios | Validaciones · lógica condicional · carga de archivos · autoguardado |
| Carga de archivos | Procesamiento de imágenes · almacenamiento · previsualización · antivirus |
| Multiusuario | Permisos / roles · control de concurrencia · invitaciones |
| Documentos | Motor de PDF · plantillas · numeración/secuencias · firmas |
| Tiempo / recurrencia | Tareas programadas (Huey) · recordatorios · vencimientos |
| Solicitudes / aprobaciones | Escalamiento · SLA · delegación · reportes de tiempos de respuesta |
| Documentos comerciales | Conversión entre documentos (cotización→orden→factura) · exportación contable · pagos |

## Cuándo decir "sepáralo y constrúyelo aparte"

- **Mezcla un motor reutilizable** (PDF, correo, etiquetas) con una funcionalidad puntual → separar el motor: se cobra una vez y habilita todo lo que venga después.
- **Mezcla una pieza transversal** (notificaciones, auditoría, permisos, búsqueda global) → construirla una sola vez como feature/servicio reutilizable, no repetida pantalla por pantalla.
- **Empaqueta 2+ funcionalidades grandes** (M/L/XL) → separar para poder fasear y mantenerse bajo el techo killer.
- **Es claramente un V2** — mejora la operación pero no bloquea el arranque → marcarla como candidata a versión posterior.

> **Transversalidad y costo:** cuando algo es transversal, su costo no es fijo — escala con el número de puntos donde se integra. Advertirlo en el output: «construir una vez, reutilizar N veces», no estimarlo como una pantalla aislada.

## Supuestos que siempre se declaran

Precios en COP sin IVA · implementación web (PWA/nativa solo si se declara, con su recargo) · desarrollo desde cero · tarifa blended ≈ $18.750/h (recalibración colombiana 02/07/2026) · no incluye infraestructura recurrente, licencias de terceros ni migración de datos legados salvo mención explícita · estimación sujeta a refinamiento tras análisis detallado.

---

## Qué cambió en esta versión (v1.3 — recalibración al mercado colombiano)

**Recalibración de precios (02/07/2026, directriz del dueño tras probar la calculadora con los tres reportes de Vástago):** los rangos por talla producían valores justos para un mercado desarrollado (≈ EE.UU.); se dividieron **÷4** para acercarlos a lo que el cliente colombiano efectivamente acepta. La tarifa blended pasó de ≈ $75.000/h a **≈ $18.750/h**. **Sin cambios:** horas por nivel, señales y niveles del catálogo, modificadores, y las zonas del semáforo ($12M/$20M), que miden disposición de pago absoluta y no se recalibran con la tarifa.
