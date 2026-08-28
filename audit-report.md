# Auditoría de vulnerabilidades y dependencias

**Fecha:** 2026-08-26

**Rama:** `chore/26082026-vuln-audit`

**Base:** `origin/main` @ `eef79c57`

**Alcance:** actualizaciones directas patch/minor de Python y npm; majors y cambios incompatibles quedan fuera.

**Cierre operativo:** 2026-08-27. El virtualenv productivo recibió los 13
updates patch/minor/transitivos que aún aparecían desactualizados; no se cambió
el manifiesto de la aplicación.

## Resultado ejecutivo

| Control | Estado inicial | Estado candidato |
|---|---:|---:|
| `npm audit` | 0 vulnerabilidades | **0 vulnerabilidades** |
| `pip-audit` | 1 vulnerabilidad en `pip 26.1.2` | **0 en el virtualenv candidato con `pip 26.2.1`** |
| `npm outdated` | 26 entradas directas | 17, todas diferidas por major, frontera breaking o anomalía de dist-tag |
| `pip list --outdated` | 28 paquetes | 5, todos upgrades mayores deliberadamente diferidos |

El grafo candidato queda limpio. La remediación de `pip` y el refresh operativo
del virtualenv productivo quedaron aplicados y verificados el 2026-08-27.

## Cierre operativo del virtualenv productivo — 2026-08-27

Los 18 paquetes que aún reportaba `pip list --outdated` se resolvieron en dos
grupos. Se promovieron exactamente estos 13 updates compatibles, primero en un
virtualenv candidato y después en producción:

| Paquete | Antes | Después |
|---|---:|---:|
| certifi | 2026.5.20 | 2026.7.22 |
| cffi | 2.0.0 | 2.1.1 |
| charset-normalizer | 3.4.7 | 3.5.1 |
| click | 8.4.2 | 8.5.0 |
| filelock | 3.32.3 | 3.32.4 |
| idna | 3.18 | 3.19 |
| linkify-it-py | 2.1.0 | 2.1.1 |
| msgpack | 1.2.1 | 1.2.2 |
| packaging | 26.2 | 26.3 |
| platformdirs | 4.11.2 | 4.11.4 |
| Pygments | 2.20.0 | 2.21.0 |
| pypdfium2 | 5.12.1 | 5.13.0 |
| wheel | 0.47.0 | 0.48.0 |

Los cinco restantes son los majors ya diferidos: Django, Faker, gunicorn,
pytest-cov y ReportLab. El resultado productivo final es `pip check` limpio,
`pip-audit` sin vulnerabilidades y sólo esos cinco registros en
`pip list --outdated`. Gunicorn y Huey reiniciaron correctamente y el sitio
continuó saludable. El freeze previo quedó respaldado temporalmente en
`/tmp/projectapp-venv-freeze-before-20260827.txt` para rollback inmediato.

## Hallazgo de seguridad inicial

| Paquete | Versión | Aviso | Versión corregida | Exposición |
|---|---:|---|---:|---|
| `pip` | 26.1.2 | `PYSEC-2026-3721` / `CVE-2026-13346` | 26.2 | Un índice malicioso podía abusar URLs de paquetes doblemente codificadas para escribir archivos fuera de la ubicación esperada; el impacto material se concentra en `pip download --only-binary`. |

`pip` es tooling del entorno y no una dependencia importada por ProjectApp. Por
eso no se agregó a `backend/requirements.txt`: se actualizó a 26.2.1 en el
virtualenv aislado usado para validar el candidato y se deja una acción operativa
explícita para producción.

## Actualizaciones aplicadas

### Frontend

| Paquete directo | Antes | Después |
|---|---:|---:|
| `@splinetool/runtime` | ^1.12.90 | ^1.12.98 |
| `axios` | ^1.19.0 | ^1.20.0 |
| `sweetalert2` | ^11.26.24 | ^11.26.25 |
| `swiper` | ^12.1.4 | ^12.2.0 |
| `video.js` | ^8.23.8 | ^8.24.0 |
| `@babel/preset-env` | ^7.29.2 | ^7.29.7 |
| `@playwright/test` | ^1.59.1 | ^1.62.1 |
| `@vue/test-utils` | ^2.4.10 | ^2.4.11 |
| `jest-environment-jsdom` | ^30.3.0 | ^30.4.1 |
| `vue` | ^3.5.33 | ^3.5.41 |

`@testing-library/jest-dom` conserva la versión 6.9.1, pero ahora queda fijada
exactamente (`"6.9.1"`). El lockfile fue regenerado con ese pin y mantiene Vue y
`@vue/server-renderer` alineados en 3.5.41.

### Backend

| Paquete directo | Antes | Después |
|---|---:|---:|
| `asgiref` | 3.11.1 | 3.12.1 |
| `django-silk` | >=5.0.0 | >=5.5.2 |
| `djangorestframework` | 3.17.1 | 3.18.0 |
| `huey` | >=2.5.0 | >=3.3.4 |
| `redis` | >=4.0.0 | >=8.1.0 |
| `requests` | 2.33.1 | 2.34.2 |
| `cryptography` | >=50.0,<51.0 | >=50.0.1,<51.0 |
| `tzdata` | 2026.2 | 2026.3 |
| `pytest-django` | 4.12.0 | 4.14.0 |
| `coverage` | 7.13.5 | 7.15.4 |
| `pypdf` | >=6.15,<7.0 | >=6.16.2,<7.0 |

## Rollback y excepciones

- `@testing-library/jest-dom 6.10.0` se instaló durante el bump automático, pero
  npm emitió una advertencia explícita de publicación incompatible: esa versión
  introdujo requisitos/cambios no apropiados para la línea 6.x y recomienda usar
  6.9.1 o migrar a 7. Se revirtió a 6.9.1 y se fijó sin `^` para impedir que el
  resolver vuelva a seleccionar 6.10.0.
- `@pinia/nuxt` permanece en ^0.9.0. Un salto entre minor de una dependencia 0.x
  se trata como potencialmente breaking y requiere una migración dedicada.
- `vuedraggable` permanece en 4.1.0: el dist-tag `latest` de npm apunta a 2.24.3;
  no se hace un downgrade automático.

## Actualizaciones mayores diferidas

### Frontend

Quedan fuera de este cambio: Babel 8, `@nuxtjs/i18n` 10, `@pinia/nuxt` 1,
`@splinetool/runtime` 2, `@testing-library/jest-dom` 7, `@vueuse/core` 14,
ApexCharts 7, Jest/Babel-Jest 30, jsdom 30, marked 18, Nuxt 4, Pinia 4,
Swiper 14 y Vue Router 5. Cada una necesita pruebas y revisión de migración
propias.

### Backend

| Paquete | Actual | Último | Decisión |
|---|---:|---:|---|
| Django | 5.2.17 | 6.1 | Mantener la línea LTS 5.2; migración separada. |
| Faker | 28.4.1 | 40.37.0 | Major de tooling de datos; revisar seeds aparte. |
| gunicorn | 23.0.0 | 26.2.0 | Major de runtime; requiere prueba de despliegue/systemd. |
| pytest-cov | 5.0.0 | 7.1.0 | Major de tooling; coordinar con la configuración de coverage. |
| ReportLab | 4.5.1 | 5.0.1 | Major del motor PDF; requiere regresión visual dedicada. |

## Verificaciones ejecutadas

| Verificación | Resultado |
|---|---|
| `npm audit` antes y después | 0 vulnerabilidades en ambos puntos. |
| `npm run build` | Aprobado; cliente y servidor compilan y Nuxt prerenderiza 36 rutas. Persiste el warning no bloqueante ya conocido de `lottie-web` por uso de `eval`. |
| `pip-audit` sobre el virtualenv candidato | 0 vulnerabilidades conocidas. |
| `python -m pip --version` | 26.2.1 en el virtualenv aislado del worktree. |
| `python -m pip check` | Sin dependencias rotas. |
| `python manage.py check` | 0 issues. |
| `pytest --collect-only -q` | Colección completa aprobada con exit code 0. |
| `pytest accounts/tests/test_client_first_login_notification.py -v --no-cov` | 2/2 aprobadas en 31.07 s. |

Pytest reporta cuatro `RemovedInDjango60Warning` preexistentes sobre el futuro
cambio de esquema asumido por `URLField`; no afectan Django 5.2 ni bloquean esta
actualización. No se ejecutaron migraciones ni se alteraron datos productivos.

## Evidencia temporal de la ejecución

- Inicial: `/tmp/projectapp-npm-audit.json`,
  `/tmp/projectapp-npm-outdated.json`, `/tmp/projectapp-pip-audit.json` y
  `/tmp/projectapp-pip-outdated.json`.
- Final: `/tmp/projectapp-npm-audit-final.json`,
  `/tmp/projectapp-npm-outdated-final.json`,
  `/tmp/projectapp-pip-audit-final.json` y
  `/tmp/projectapp-pip-outdated-final.json`.

Estos JSON son artefactos locales efímeros; las conclusiones y versiones
relevantes quedan conservadas en este reporte.

## Acción operativa posterior al merge — completada

`pip 26.2.1` y los 13 updates compatibles están activos en el virtualenv
productivo. No queda una acción patch/minor pendiente; los cinco majors requieren
migraciones dedicadas y permanecen fuera de este refresh.
