# Auditoría de vulnerabilidades y warnings de build

**Fecha:** 2026-08-19

**Ramas:** `fix/19082026-security-build-warnings` y hotfix `fix/19082026-nuxt-payload-generation`

**Base:** `origin/main`

**Alcance:** dependencias Python/npm, cinco constraints MySQL, imports automáticos duplicados y chunks frontend mayores de 500 KB.

## Resultado ejecutivo

| Control | Estado inicial | Estado final |
|---|---:|---:|
| `npm audit` | 24 vulnerabilidades (4 critical, 14 high, 4 moderate, 2 low) | **0** |
| `pip-audit` | 88 asociaciones paquete-aviso, 77 identificadores únicos | **0** |
| Constraints condicionales ignorados por MySQL | 5 warnings | **0** |
| Imports automáticos duplicados de Nuxt | 4 nombres ambiguos | **0** |
| Chunks JavaScript mayores de 500 KB | 2; máximo aproximado 1.18 MB | **0**; máximo 448,634 bytes |

## Dependencias corregidas

### Backend

| Paquete | Antes | Después | Motivo |
|---|---:|---:|---|
| Django | 5.2.13 | 5.2.17 | Avisos de seguridad |
| Pillow | 10.4.0 | 12.3.0 | Avisos sin corrección en la línea 10.x |
| cryptography | `>=42,<44` | `>=50,<51` | Avisos sin corrección dentro del pin anterior |
| sqlparse | 0.5.5 | 0.6.0 | Avisos de seguridad |
| pytest | 8.3.2 | 9.1.1 | Aviso sin corrección en 8.x |
| pypdf | `>=4,<5` | `>=6.15,<7` | Avisos sin corrección en 4.x |

La instalación aislada termina con `pip check` sin dependencias rotas y `pip-audit` sin hallazgos.

### Frontend

| Paquete directo | Antes | Después |
|---|---:|---:|
| axios | ^1.15.2 | ^1.19.0 |
| dompurify | ^3.4.1 | ^3.4.14 |
| @babel/core | ^7.29.0 | ^7.29.7 |
| nuxt | ^3.21.4 | ^3.21.11 |

El lockfile se regeneró y validó con npm 10.9.4, la misma generación usada por Node 22 en CI; `npm ci` y `npm audit` terminan en cero. Las versiones nuevas que permanecen en `npm outdated` o `pip list --outdated` no tienen hallazgos activos en estas auditorías; sus upgrades mayores quedan fuera de este cambio para no mezclar migraciones funcionales con el cierre de seguridad.

## Compatibilidad MySQL

Los cinco `UniqueConstraint(condition=...)` que MySQL ignoraba fueron reemplazados por índices únicos funcionales que normalizan la cadena vacía a `NULL` mediante `NullIf`:

- `Requirement(phase, source_flow_key)`
- `ProjectScopeItem(phase, source_item_id)`
- `Deliverable(project, source_epic_key)`
- `DataModelEntity(deliverable, source_entity_name)`
- `SavedFilterTab(user, view, builtin_key)`

La migración `accounts/0053_mysql_compatible_unique_constraints.py` ejecuta primero una comprobación de duplicados y aborta con un mensaje accionable si encuentra datos incompatibles. El SQL generado en MySQL crea los cinco índices con `NULLIF(campo, '')`, conservando estas reglas:

- una clave no vacía no se puede repetir dentro del mismo scope;
- la misma clave puede existir en scopes diferentes;
- múltiples cadenas vacías siguen permitidas.

La comprobación read-only sobre la base de producción encontró cero grupos duplicados en los cinco casos.

## Imports y bundles frontend

Se asignaron nombres explícitos a los helpers de estado que Nuxt autoimportaba con nombres repetidos:

- `dashboardProposalStatusLabel`
- `proposalTransitionStatusLabel`
- `documentStatusLabel`
- `documentStatusBadgeClass`
- `collectionStatusBadgeClass`

ApexCharts dejó de registrarse globalmente. `ApexChart.client.vue` carga el wrapper sólo en cliente e importa únicamente core, tipos de gráfica y features utilizadas. Los consumidores usan `LazyApexChart` y Vite divide ApexCharts y GSAP mediante `vite.$client.build.rollupOptions.output.manualChunks`. El build final no reporta imports duplicados ni chunks superiores al límite; el archivo cliente más grande mide 448,634 bytes.

## Hardening del build estático

La verificación del primer despliegue detectó que Nuxt 3.21.11 combinaba los payloads extraídos con `app.cdnURL=/static/frontend/` y generaba algunas rutas `_payload.json` como HTML. La navegación seguía funcionando, pero la consola reportaba que no podía parsear el payload. Para la topología estática de Django se fijó `experimental.payloadExtraction: false`: los datos quedan inline y el build ya no emite ni solicita `_payload.json`.

También se cambió `collectstatic` a modo `--clear` en los dos caminos productivos —`scripts/deploy.sh` y el rebuild automático del blog—. Así no sobreviven chunks con hash de builds anteriores ni pueden reaparecer colisiones archivo/directorio. El build Django real pasó de 485 rutas, que incluían payloads espurios, a 313 rutas válidas.

## Verificaciones ejecutadas

- `python manage.py check` con settings de producción: 0 issues.
- `python manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- Constraints: 15 pruebas parametrizadas, todas aprobadas.
- Regresión de Django/Pillow/cryptography/pypdf: 17 pruebas, todas aprobadas.
- Frontend unitario relacionado: 37 pruebas, todas aprobadas.
- Playwright focalizado en gráficas reales: 3 pruebas, todas aprobadas sin retries.
- `npm run build`: aprobado, sin los warnings objetivo y sin chunks mayores de 500 KB.
- `npm run build:django`: aprobado con 79 posts, cero artefactos `_payload.json` y cero chunks mayores de 500 KB.
- Navegación Playwright read-only home → portfolio: URL y API 200, sin requests ni errores de payload.
- Quality gate: backend 99/100 y frontend unitario 97/100, ambos aprobados; el test backend nuevo no introduce findings.

## Nota técnica

El preview del servidor Nitro generado localmente no inicia porque su paquete virtual de `vue` queda incompleto. No afecta la ruta productiva de ProjectApp: producción usa `npm run build:django`/`nuxi generate`, copia el resultado estático a Django y no ejecuta Nitro como servidor. Se mantiene como investigación independiente si en el futuro el proyecto adopta despliegue SSR con Nitro.

La portada pública todavía emite el warning genérico preexistente `Hydration completed but contains mismatches`; no provoca errores de página, requests fallidos ni bloquea la navegación validada. Es una investigación separada del payload y de los warnings objetivo de esta auditoría.
