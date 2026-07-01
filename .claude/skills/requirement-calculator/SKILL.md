---
name: requirement-calculator
description: "Calculadora de requerimientos: recibe la descripción en lenguaje natural de un requerimiento y devuelve nivel de esfuerzo (XS–XL), horas, rango de precio COP, implicaciones técnicas, adyacencias y estrategia comercial. Persiste el resultado como documento en /panel/documents (carpeta Requirement Estimates) con postfijo de fecha DDMMYYYY."
argument-hint: "[descripción del requerimiento en lenguaje natural]"
allowed-tools: Bash, Read, Write, AskUserQuestion
---

# Calculadora de Requerimientos

Actúa como la calculadora de requerimientos de una casa de software para el mercado **colombiano**. El insumo es la descripción de un requerimiento en lenguaje natural; el resultado es una estimación accionable (esfuerzo, horas, rango de precio COP, implicaciones técnicas, adyacencias y estrategia comercial) que además queda guardada como documento en el panel.

Sigue las fases en orden. No inventes reglas: todas viven en los archivos de referencia.

---

## 1. Cargar las reglas de juego

Lee **ambos** archivos de referencia de este skill antes de clasificar nada:

- `references/effort-indicators.md` — catálogo de señales XS–XL, modificadores, señales espejo y notas de clasificación. **Es el corazón del proceso.**
- `references/market-pricing.md` — niveles → horas → precio, orden de cálculo, zonas killer, estrategias comerciales, adyacencias y supuestos.

## 2. Gate de ambigüedad (una sola ronda)

Antes de calcular, detecta ambigüedades que **cambian el nivel**:

- ¿La base ya existe o se construye desde cero? (es LA pregunta que separa `M` de `L`)
- ¿Aplica también a la PWA contratada?
- ¿Hay reglas de negocio sin definir que impidan cerrar precio fijo?
- ¿Depende de credenciales/datos de un tercero (bloqueo externo)?

Si alguna aplica, haz **una** ronda de preguntas con AskUserQuestion (máximo 4 preguntas, las que más muevan el precio). Con las respuestas, continúa. Si algo queda ambiguo después de esa ronda: asume el caso más común, **declara el supuesto** en el documento y marca la condición de bloqueo ("no cerrar precio fijo hasta aclarar X").

## 3. Descomponer y clasificar

1. **Descompón** la descripción en funcionalidades individuales (el proyecto es la suma; nunca estimes el bloque entero de un golpe).
2. Por cada funcionalidad:
   - El **indicador más alto** que la describe fija el nivel base (XS/S/M/L/XL). Usa las **señales espejo** cuando la misma palabra pueda caer en varios niveles.
   - Aplica el **atenuador "extiende algo existente"** si la base ya existe (baja de `L` a `M` o menos).
   - Aplica los **modificadores** estructurales y de costo/riesgo activos.
3. Si una funcionalidad da `XL`: **no se cotiza como un ítem** — pártela en 2+ features (`S`/`M`/`L`) y clasifica cada uno.

## 4. Precio y reglas de mercado

1. Traduce cada nivel a **horas y rango COP** con la tabla de `market-pricing.md`. El precio siempre es **rango (piso–techo)**, nunca un punto.
2. **Suma** la propuesta y aplica el semáforo: ✅ < $12M · ⚠️ $12–20M · ⛔ > $20M (killer → fragmentar obligatorio).
3. Si el total ≥ $12M: propone **Estrategia A (fases)** o **B (V1/V2/V3)** con alcance y precio de cada parte.
4. Recorre el **mapa de adyacencias** y anticipa qué funcionalidades se abrirán después (candidatas naturales a V2/V3).
5. Identifica qué conviene **separar** (motores reutilizables, piezas transversales, features empaquetados, V2 evidentes).

## 5. Generar el documento markdown

Obtén la fecha real del sistema (nunca la asumas):

```bash
date +%d%m%Y
```

Escribe el resultado en un archivo temporal del scratchpad de la sesión, con **exactamente esta estructura y orden**:

```markdown
# Estimate: <nombre corto del requerimiento> — <DDMMYYYY>

## 1. Resumen
<1–2 líneas reinterpretando el requerimiento en lenguaje de negocio.>

## 2. Descomposición por funcionalidad
| Funcionalidad | Nivel | Indicadores | Modificadores | Horas | Precio COP |
|---|---|---|---|---|---|
<una fila por funcionalidad>

<Debajo de la tabla: implicaciones técnicas por funcionalidad (bullets cortos).>

## 3. Totales
- **Horas:** <rango total>
- **Precio total:** <rango COP>
- **Semáforo:** ✅ <$12M / ⚠️ $12–20M / ⛔ >$20M

## 4. Observaciones
<Qué separar y por qué · qué es transversal · qué adyacencias se abren.>

## 5. Estrategia comercial
<Solo si total ≥ $12M o killer: fases o V1/V2/V3 con alcance y precio. Si no aplica: "Cabe en una sola propuesta (sweet spot).">

## 6. Supuestos y exclusiones
<Los supuestos declarados en market-pricing.md, ajustados al caso, + los supuestos asumidos en el gate de ambigüedad.>
```

**Requerimiento original:** incluye al final del documento la descripción original recibida, citada textualmente, para trazabilidad.

## 6. Crear el documento en el panel

Persiste el markdown como documento real en `/panel/documents` (carpeta **Requirement Estimates**, creada una sola vez por el command):

```bash
cd backend && source venv/bin/activate && python manage.py create_estimate_document \
  --title "Estimate: <nombre corto> — <DDMMYYYY>" \
  --file "<ruta del .md temporal>"
```

El command acepta opcionalmente `--folder`, `--status` (default `published`) y `--language` (default `es`).

## 7. Reporte al usuario

Cierra el turno con:

1. **Resumen ejecutivo** en el chat: total de horas, rango de precio, semáforo, qué conviene separar y las 2–3 observaciones más importantes.
2. **Confirmación del documento**: título creado, carpeta "Requirement Estimates", visible en `/panel/documents`.
3. Si aplicó condición de bloqueo: recuérdala explícitamente ("no cerrar precio fijo hasta aclarar X").

---

## Reglas estrictas

- Todo requerimiento se procesa contra los archivos de referencia — no clasificar de memoria.
- Una funcionalidad `XL` **siempre** se parte antes de cotizar.
- El precio **siempre** es rango, en COP sin IVA.
- La fecha del título viene de `date +%d%m%Y`, jamás asumida.
- El documento se crea **siempre** (aunque haya condición de bloqueo, el análisis queda guardado con sus supuestos).
- Máximo una ronda de preguntas; después, supuestos declarados.
