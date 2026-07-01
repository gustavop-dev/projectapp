# Esfuerzo, Precio y Reglas de Mercado — Calculadora de Requerimientos (v1.1)

> Complemento de `effort-indicators.md`. Traduce el nivel de esfuerzo a horas y precio COP, y define las reglas comerciales del mercado colombiano.

## Premisas base

- **Desarrollo desde cero (greenfield)** salvo que la descripción declare que se extiende algo existente.
- **Cliente PYME colombiano.** Precios en **COP, sin IVA**.
- **Tarifa de venta blended de referencia: ≈ $75.000 COP/hora** (extremo competitivo del mercado local, ≈ US$22 a TRM ≈ $3.443/USD).
- **Killer: $20.000.000 COP** — una propuesta (la **suma** de los requerimientos, no un ítem suelto) por encima de ese techo tiende a ser rechazada. Obligatorio fragmentar.
- **Granularidad:** se estima funcionalidad por funcionalidad; el proyecto es la suma.

### Qué incluye y qué no (por defecto)

- **Incluye:** análisis, desarrollo, pruebas básicas, despliegue inicial y garantía corta de estabilización.
- **No incluye:** infraestructura/hosting recurrente, licencias de terceros, soporte continuo, capacitación extensa ni migración de datos legados — salvo mención explícita en el alcance.

## Niveles: esfuerzo → horas → precio

| Nivel | Pts | Perfil típico | Horas | Precio COP | ≈ USD |
|---|---|---|---|---|---|
| **XS** | 1 | Cambio de configuración, un campo, validación básica, enlace simple. | 2–7 | $150K – $500K | $45–145 |
| **S** | 2 | Ajuste de UI/plantilla, modal, correo básico, monitoreo simple. | 7–20 | $500K – $1,5M | $145–435 |
| **M** | 3 | CRUD estándar con extras, generación de archivos, permisos, lógica condicional. A menudo se apoya en algo existente. | 20–50 | $1,5M – $3,5M | $435–1.000 |
| **L** | 5 | **Un feature completo desde cero**: backend + frontend robustos (a veces + una integración, que lo lleva al techo del rango). | 55–90 | $4M – $7M | $1.160–2.030 |
| **XL** | 8 | **No es un ítem:** la descripción trae **2+ features** mezclados. Se separa y se cotiza cada feature aparte (cada uno suele ser un L). | 90–200 | $7M – $15M | $2.030–4.350 |

## Orden de cálculo

1. **Nivel base por funcionalidad** — el indicador de esfuerzo más alto que la describe fija XS/S/M/L/XL.
2. **Modificadores estructurales y de costo/riesgo** — se suman los porcentajes/horas activos. "Motor nuevo" agrega 30–80% (o +1 nivel si es pesado). "Transversal" multiplica.
3. **Rango, no punto** — el precio siempre se expresa como rango (piso–techo). El piso usa el extremo bajo de horas; el techo, el alto.
4. **Suma y chequeo de killer** — se suman las funcionalidades. Si el techo total supera $20M, se activan las reglas de mercado (fases o versiones).

## Zonas de precio (sobre la SUMA de la propuesta)

| Zona | Rango total | Acción |
|---|---|---|
| ✅ **SWEET SPOT** | < $12M | Propuesta única, sin fricción. |
| ⚠️ **FRICCIÓN** | $12M – $20M | Viable, pero conviene ofrecer fases o versionado para bajar el ticket inicial. |
| ⛔ **KILLER** | > $20M | Rechazo probable. Obligatorio fragmentar antes de presentar. |

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

## Cuándo decir "sepáralo y constrúyelo aparte"

- **Mezcla un motor reutilizable** (PDF, correo, etiquetas) con una funcionalidad puntual → separar el motor: se cobra una vez y habilita todo lo que venga después.
- **Mezcla una pieza transversal** (notificaciones, auditoría, permisos, búsqueda global) → construirla una sola vez como feature/servicio reutilizable, no repetida pantalla por pantalla.
- **Empaqueta 2+ funcionalidades grandes** (M/L/XL) → separar para poder fasear y mantenerse bajo el techo killer.
- **Es claramente un V2** — mejora la operación pero no bloquea el arranque → marcarla como candidata a versión posterior.

> **Transversalidad y costo:** cuando algo es transversal, su costo no es fijo — escala con el número de puntos donde se integra. Advertirlo en el output: «construir una vez, reutilizar N veces», no estimarlo como una pantalla aislada.

## Supuestos que siempre se declaran

Precios en COP sin IVA · desarrollo desde cero · tarifa blended ≈ $75K/h · no incluye infraestructura recurrente, licencias de terceros ni migración de datos legados salvo mención explícita · estimación sujeta a refinamiento tras análisis detallado.
