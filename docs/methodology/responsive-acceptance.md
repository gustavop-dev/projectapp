# Aceptación responsiva y guion de regresión

**Estado:** obligatorio desde 2026-08-22  
**Alcance:** panel interno, plataforma autenticada y vistas públicas  
**Contrato ejecutable:** `frontend/config/responsive.js` y `frontend/config/responsiveAcceptance.js`

Este documento cierra el plan PA-75 → fase 4. Complementa el estándar de
componentes de `responsive-standard.md`: ese documento define cómo responde
cada patrón; este define cómo demostrar que una vista está terminada y cómo
evitar que una entrega posterior reconstruya el problema.

## Estado de implementación

El cierre del 2026-08-22 deja 101 páginas Nuxt asignadas sin ambigüedad a 12
módulos de aceptación. Comercial, Emails, Canvas de Documentos, Dashboard,
Contenido, MCP y Públicas completan la adopción iniciada por Fundamentos,
Contabilidad, Documentos, Clientes y Proyectos. Las listas CRUD de exploración
usan tarjetas debajo de 1000 px mediante `BaseExploratoryList`; las superficies
comparativas usan `BaseResponsiveTable` y declaran la prioridad de cada columna.

Las fichas PA-45, PA-61, PA-66, PA-69, PA-70 y PA-73 dejan de ser variantes
independientes: su criterio de cierre es este contrato y sus primitives
compartidas. La línea base quedó verificada con las matrices de los doce módulos,
build de producción, contrato 101/12/5, catálogo 101/101 y flow-map fresco sin
flows `junk-only` ni `missing`.

## Condición de aceptación

Una vista nueva o modificada **no se considera terminada** hasta cumplir todo
lo siguiente en los cinco viewports canónicos:

| Perfil | Viewport | Riesgo que valida |
| --- | ---: | --- |
| `compact` | 412 × 915 | Lectura, orden, targets táctiles y overlays |
| `portrait` | 835 × 1194 | Tableta vertical; transición entre móvil y escritorio |
| `landscape` | 1195 × 835 | Tableta horizontal y altura limitada |
| `desktop` | 1440 × 900 | Portátil de uso diario |
| `wide` | 2560 × 1440 | Relación visual y ancho útil máximo de 1440 px |

La comprobación exige:

1. contenido y acción principal visibles;
2. cero overflow horizontal del documento;
3. tablas con prioridad de negocio declarada, nunca inferida;
4. formularios en orden de lectura y overlays que caben o tienen scroll interno;
5. ninguna acción disponible únicamente por hover o drag;
6. targets táctiles de al menos 44 × 44 px cuando se declaran para aceptación;
7. contenido del panel limitado a 1440 px en `wide`;
8. un E2E de resultado real con tags `@flow:*` y `@responsive:<módulo>`.

`npm run check:responsive-contract` falla si una página Nuxt no está en el
catálogo, si una vista no tiene dueño, si cambia la matriz de equipos o si un
módulo pierde su E2E responsivo. El workflow de PR determina los módulos
afectados por los archivos modificados y corre su tag en los cinco viewports.

## Guion repetible por módulo

El detalle ejecutable vive junto al código para que CI y documentación no
mantengan listas divergentes. La matriz actual es:

| Módulo | Tag | Recorrido mínimo |
| --- | --- | --- |
| Fundamentos | `@responsive:foundation` | Navegación, tabs/filtros, tabla, modal y acciones compartidas |
| Contabilidad | `@responsive:accounting` | Doce tabs, filtros, fila representativa y modales largos |
| Documentos | `@responsive:documents` | Carpetas, activos/archivados y acciones de documento |
| Clientes | `@responsive:clients` | Estado, filtros, tarjeta/fila y reasignación |
| Proyectos | `@responsive:projects` | Búsqueda, alcance, formulario y cambio de cliente |
| Comercial | `@responsive:commercial` | Propuestas, diagnósticos, selección múltiple y paquetes |
| Emails | `@responsive:emails` | Composición, adjuntos, preview e historial |
| Canvas | `@responsive:canvas` | Metadata, editor/preview, guardado y guard de salida |
| Dashboard | `@responsive:dashboard` | Pulso, radar, cifras, estadísticas y acciones rápidas |
| Contenido | `@responsive:content` | Blog, calendario, LinkedIn, portafolio, QR y linktrees |
| MCP | `@responsive:mcp` | Conector, actividad, tools, token y activación |
| Públicas | `@responsive:public` | Marketing, blog, portafolio, linktree, propuesta y diagnóstico |

Para repetirlo localmente:

```bash
cd frontend
npm run check:responsive-contract
npm run e2e:responsive -- --grep '@responsive:commercial'
npm run e2e:responsive:changed
```

La segunda orden ejecuta un módulo en los cinco anchos. La tercera resuelve el
diff contra `origin/main`; un cambio transversal ejecuta todos los módulos.

## Cierre de fichas adelantadas

Una ficha previa de responsividad sólo se cierra cuando:

- su pantalla usa el patrón canónico o documenta por qué el caso es distinto;
- no conserva una media query, selector o modal paralelo que replique la
  primitive compartida;
- el comportamiento coincide con el resto del módulo en `compact`, `portrait`
  y `landscape`, no sólo en celular;
- su flujo representativo queda dentro del tag responsivo del módulo;
- el gate del contrato y el E2E focalizado quedan verdes.

Esto aplica expresamente a PA-45, PA-61, PA-66, PA-69, PA-70 y PA-73. Una
solución adelantada se adapta al estándar; no se convierte en una excepción
por haber llegado primero.

## Automatización y revisión periódica

`.github/workflows/responsive-acceptance.yml` aplica tres ritmos:

- **Cada PR:** valida catálogo/propiedad y ejecuta sólo módulos afectados.
- **Mensual:** ejecuta los doce guiones completos en los cinco viewports.
- **Febrero y agosto:** abre una ficha de revisión semestral del estándar.

La revisión semestral debe contrastar los equipos canónicos con analytics y
dispositivos reales, revisar errores de CI por perfil, actualizar breakpoints
sólo desde `responsive.js` y dejar cualquier cambio de patrón en el estándar,
el styleguide y sus pruebas dentro del mismo PR. Cambiar un ancho en CSS sin
actualizar esa fuente no es una revisión válida.
