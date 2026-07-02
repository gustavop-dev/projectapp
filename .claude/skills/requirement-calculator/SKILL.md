---
name: requirement-calculator
description: "Calculadora de requerimientos: recibe la descripción en lenguaje natural de un requerimiento (implementación web por defecto) y devuelve nivel de esfuerzo (XS–XL), horas, rango de precio COP, implicaciones técnicas, adyacencias y estrategia comercial. Persiste el resultado como documento con branding ProjectApp en /panel/documents (carpeta Requirement Estimates) con postfijo de fecha DDMMYYYY."
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
- `references/market-pricing.md` — niveles → horas → precio, fórmula y orden de cálculo, zonas killer, estrategias comerciales, adyacencias y supuestos.

## 2. Gate de ambigüedad (una sola ronda)

Antes de calcular, detecta ambigüedades que **cambian el nivel o el precio**:

- ¿El mensaje trae **un requerimiento o varios independientes** (contextos, clientes o módulos sin relación entre sí)? Si son independientes, confirma en la misma ronda cómo agruparlos.
- ¿La base ya existe o se construye desde cero? (es LA pregunta que separa `M` de `L`)
  - Si es para una **plataforma existente**, incluye en la misma ronda el checklist de **motores típicos ya construidos**: correo/plantillas · generación de PDF · notificaciones · tareas programadas (cron) · auth/roles · carga de archivos · i18n. Cada motor que ya exista: (1) anula el modificador *Motor nuevo* para las funcionalidades que lo usen y (2) activa el atenuador *extiende algo existente*. Registra los motores confirmados en la sección Supuestos del documento.
- **Plataforma**: ¿web (default, sin recargo), aplica también a la PWA (+30%) o es app móvil nativa (+60%)? Solo preguntar si la descripción lo insinúa.
- Si menciona "factura": ¿cuenta de cobro / PDF simple (`M`) o facturación electrónica DIAN (`XL` regulatorio)?
- ¿Hay reglas de negocio sin definir que impidan cerrar precio fijo?
- ¿Depende de credenciales/datos de un tercero (bloqueo externo)?

Si alguna aplica, haz **una** ronda de preguntas con AskUserQuestion (máximo 4 preguntas, las que más muevan el precio). Con las respuestas, continúa. Si algo queda ambiguo después de esa ronda: asume el caso más común, **declara el supuesto** (con su impacto en % o nivel si la realidad fuera otra) y marca la condición de bloqueo ("no cerrar precio fijo hasta aclarar X").

## 3. Descomponer y clasificar (orden estricto)

1. **Descompón** la descripción en funcionalidades individuales (el proyecto es la suma; nunca estimes el bloque entero de un golpe).
2. Por cada funcionalidad, en este orden:
   - **(a) ¿La base existe?** Si sí, aplica el atenuador "extiende algo existente" (baja de `L` a `M` o menos).
   - **(b) Nivel base con cita literal**: recorre los niveles de arriba hacia abajo (XL → XS); el primer indicador que la describe fija el nivel. En la tabla del documento **cita el texto literal de la señal** (o de la celda de la familia espejo). Si ninguna señal aplica: clasifica por analogía, márcalo como *"sin señal — por analogía"* y propone la señal faltante al final (retroalimenta el catálogo).
   - **(c) Checklist de modificadores completo**: recorre la tabla entera de modificadores marcando aplica / no aplica (es donde se olvidan cron, PWA, diseño no entregado). Anti-doble-conteo: *Pantalla nueva* y *Modelo de datos* **nunca** sobre un `L`.
   - **(d) Familia espejo**: si la palabra clave es ambigua (búsqueda, firma, factura, chat, tiempo real…), verifica la celda correcta en la tabla de señales espejo antes de fijar el nivel.
3. Si una funcionalidad da `XL`: **prohibido dejarla como fila** — pártela en 2+ funcionalidades `S`/`M`/`L` y clasifica cada una. La tabla final del documento **no puede contener filas XL**.
4. **Anti-doble-cobro**: verifica que dos filas no coticen la misma pieza (mismo modelo de datos, misma pantalla) y que los transversales (auditoría, permisos, notificaciones, motores) aparezcan **una sola vez** como fila propia — nunca repetidos pantalla por pantalla.

## 4. Precio y validación aritmética

1. Traduce cada nivel a horas y rango COP con la tabla de `market-pricing.md` y aplica la fórmula:

   `horas = base × (1 + Σ% aditivos) × factor transversal + horas fijas (cron)` — y si es app nativa, `× 1,6` **al final**.

2. El precio siempre es **rango (piso–techo)**, nunca un punto. La columna de precio de la tabla de niveles manda; las horas son indicativas.
3. **Valida la aritmética antes de escribir el documento**: piso ≤ techo en cada fila · total = suma de las filas · el semáforo corresponde al techo del total.
4. Semáforo sobre la **suma**: ✅ Sweet spot < $12M · ⚠️ Fricción $12–20M · ⛔ Killer > $20M (fragmentar obligatorio).
5. Si el total ≥ $12M: propone **Estrategia A (fases)** o **B (V1/V2/V3)** con alcance y precio de cada parte.
6. Recorre el **mapa de adyacencias** y anticipa qué se abrirá después (candidatas a V2/V3); identifica qué conviene **separar** (motores, transversales, features empaquetados).
7. **Formato de moneda (obligatorio):** COP en millones con sufijo `M`, coma decimal y **máximo un decimal**, redondeando cada extremo al múltiplo de $0,1M más cercano (`$1,8M`, no `$1,83M` ni `$1.830.000`). Montos < $1M en miles: `$850K`. Rangos con guion sin espacios: `$1,8M–$2,4M`. El total se redondea **después** de sumar los extremos sin redondear. Un solo formato en todo el documento.

## 4-bis. Consistencia con estimaciones previas (barato, condicional)

Lista los títulos existentes de la carpeta:

```bash
cd /home/ryzepeck/webapps/projectapp/backend && source venv/bin/activate && python manage.py shell -c "from content.models import Document; [print(d.pk, '|', d.title) for d in Document.objects.filter(folder__name='Requirement Estimates').order_by('-created_at')[:20]]"
```

Si **ningún** título es temáticamente similar, sigue de largo (no leas nada). Si 1–2 lo son, lee solo sus totales (`print(d.content_markdown)` del pk elegido). Si para alcance equivalente el precio nuevo difiere más de ±30%, no lo "corrijas" en silencio: decláralo en Observaciones (*"La estimación #N de <fecha> cotizó algo equivalente en $X; la diferencia se debe a <motivo>"*).

## 5. Generar el documento markdown (branding ProjectApp)

Obtén la fecha real del sistema (nunca la asumas):

```bash
date +%d%m%Y
```

Escribe el resultado en un archivo temporal del scratchpad. **Markdown puro** — sin HTML embebido ni colores inline: el render del panel y el PDF ya aplican la identidad ProjectApp (títulos esmeralda, tipografía Ubuntu, portadas). Usa los callouts GitHub que el panel soporta (`[!TIP]`, `[!WARNING]`, `[!CAUTION]`, `[!IMPORTANT]`, `[!NOTE]`). El semáforo lleva **emoji + etiqueta de texto** (los emojis se strippean en el PDF). Estructura exacta:

```markdown
# Estimate: <nombre corto del requerimiento> — <DDMMYYYY>

> **ProjectApp · Calculadora de Requerimientos** — estimación por funcionalidad para implementación web, precios en COP sin IVA.

## 1. Resumen
<1–2 líneas reinterpretando el requerimiento en lenguaje de negocio.>

## 2. Descomposición por funcionalidad
| Funcionalidad | Nivel | Señal aplicada (cita literal) | Modificadores | Horas | Precio COP |
|---|---|---|---|---|---|
<una fila por funcionalidad — nunca una fila XL>

<Debajo de la tabla: implicaciones técnicas por funcionalidad (bullets cortos).>

## 3. Totales
- **Horas:** <rango total>
- **Precio total:** <rango COP>
- **Semáforo:** <emoji + etiqueta, p. ej. "✅ Sweet spot (menos de $12M)">

> [!TIP] / [!WARNING] / [!CAUTION]
> <Una línea con la lectura comercial del semáforo: TIP si sweet spot, WARNING si fricción, CAUTION si killer.>

## 4. Observaciones
<Qué separar y por qué · qué es transversal · qué adyacencias se abren.>

## 5. Estrategia comercial
<Solo si total ≥ $12M o killer: fases o V1/V2/V3 con alcance y precio. Si no aplica: "Cabe en una sola propuesta (sweet spot).">

## 6. Supuestos y exclusiones
<Supuestos de market-pricing.md ajustados al caso + los asumidos en el gate, cada uno con su impacto si cambiara.>

> [!IMPORTANT]
> <Solo si hubo condición de bloqueo: "No cerrar precio fijo hasta aclarar X." Si no la hubo, omitir este callout.>

---

**Requerimiento original:** «<descripción recibida, textual>»

— *ProjectApp · Calculadora de Requerimientos*
```

## 6. Crear el documento en el panel

Persiste el markdown como documento real en `/panel/documents` (carpeta **Requirement Estimates**, creada una sola vez por el command; el PDF con portadas ProjectApp sale automático con los defaults del modelo):

```bash
cd /home/ryzepeck/webapps/projectapp/backend && source venv/bin/activate && python manage.py create_estimate_document \
  --title 'Estimate: <nombre corto> — <DDMMYYYY>' \
  --file '<ruta absoluta del .md temporal>'
```

**Saneo del título:** el nombre corto usa solo letras (con tildes/ñ), números, espacios y guiones — nunca comillas (`"` `'`), `$`, backticks ni saltos de línea. El guion largo `—` del separador de fecha sí es válido. Pasa `--title` y `--file` entre comillas simples y con rutas absolutas.

El command acepta opcionalmente `--folder`, `--status` (default `published`), `--language` (default `es`) y `--on-conflict` (default `version`). Si ya existe un documento con el mismo título (re-estimación del mismo día), el command agrega automáticamente ` — v2`. Si el usuario pidió explícitamente **corregir** la estimación anterior, usa `--on-conflict replace`. En re-estimaciones, agrega en "Supuestos y exclusiones" una línea: *"Reemplaza/versiona la estimación #<id anterior>; cambio respecto a la versión previa: <qué se aclaró>."*

## 7. Reporte al usuario

Cierra el turno con:

1. **Resumen ejecutivo** en el chat: total de horas, rango de precio, semáforo, qué conviene separar y las 2–3 observaciones más importantes.
2. **Confirmación del documento**: título creado, carpeta "Requirement Estimates" y el **enlace directo** que imprime el command (`/panel/documents/<id>/edit`) — inclúyelo siempre en el reporte final.
3. Si aplicó condición de bloqueo: recuérdala explícitamente ("no cerrar precio fijo hasta aclarar X").
4. Si alguna funcionalidad se clasificó *"sin señal — por analogía"*: propone la señal nueva en el chat **y además** añádela (append, nunca sobrescribir) a `references/pending-signals.md` con el formato `- <DDMMYYYY> · nivel sugerido: <X> · señal propuesta: "<texto>" · origen: "<funcionalidad del requerimiento>"`. Ese archivo es la bandeja de candidatas para la próxima versión del catálogo; el catálogo mismo no se toca desde el skill.

---

## Reglas estrictas

- Todo requerimiento se procesa contra los archivos de referencia — no clasificar de memoria.
- **Un documento por requerimiento independiente.** Si el input trae N requerimientos sin relación entre sí, produce N documentos, cada uno con su propia tabla, total y semáforo — el semáforo y la estrategia comercial **nunca** se calculan sobre la suma de requerimientos independientes. Solo consolida cuando las piezas pertenecen al mismo proyecto/propuesta.
- **Formato de moneda único** en todo el documento (millones con 1 decimal máx., redondeo a $0,1M, rangos `$1,8M–$2,4M`).
- **Web por defecto**; PWA `+30%` y app nativa `+60%` solo si el requerimiento lo declara (excluyentes entre sí).
- La tabla final **nunca** contiene filas `XL`: siempre se muestran descompuestas.
- Cada fila **cita la señal literal** del catálogo que fijó su nivel.
- El precio **siempre** es rango, en COP sin IVA; la aritmética se valida antes de escribir el documento.
- La fecha del título viene de `date +%d%m%Y`, jamás asumida.
- El documento se crea **siempre** (aunque haya condición de bloqueo, el análisis queda guardado con sus supuestos).
- Máximo una ronda de preguntas; después, supuestos declarados con su impacto.
- Markdown puro con callouts — sin HTML ni colores inline: el branding lo aplican el panel y el PDF.

---

## Suite de validación (baseline)

En `validation/` vive el **baseline de calibración** de la skill, producido en la prueba con los tres reportes de Vástago (02072026, calibración ÷4 definitiva):

- `validation/test-results.md` — artefacto de consolidación: tabla resumen de las 3 estimaciones (#23 $6,1M–$8,8M ✅ · #24 $7,2M–$10,2M ✅ · #25 $13,3M–$18,9M ⚠️), detalle por requerimiento y QA de la skill (detección de múltiples, anti-doble-cobro, persistencia, señales promovidas, recalibraciones).
- `validation/estimates/*.md` — los 3 markdown fuente de esas estimaciones (documentos #23, #24 y #25 de `/panel/documents`), con filas, señales citadas, modificadores, horas y precios.

**Regla de mantenimiento:** si cambian las reglas de la skill —tabla de precios/tarifa en `market-pricing.md`, señales o modificadores en `effort-indicators.md`, o el flujo de este SKILL.md— y el cambio **altera los números o la clasificación** del baseline, hay que **actualizar la suite en el mismo cambio**: recalcular las columnas afectadas de los 3 estimates (manteniendo horas/clasificación salvo que el cambio sea de catálogo), refrescar los totales y semáforos de `test-results.md`, y agregar allí una fila de QA que registre el cambio y su fecha. Si el cambio no altera números ni clasificación (p. ej. una señal nueva que el baseline no usa), basta la fila de QA. El baseline es la referencia para detectar regresiones de calibración: mismo input → mismos niveles y precios.
