# Vulnerability Audit & Dependency Update Report

**Branch:** `double-check-30042026`
**Date:** 2026-04-30
**Base:** `origin/main` @ `2bdd4ff0`
**Scope:** patch + minor updates only (no major version bumps)

## Summary

| Surface  | Vulns (initial) | Outdated (initial) |
|----------|-----------------|--------------------|
| Frontend | 8 (6 moderate, 2 high) | 20 |
| Backend  | 60 across 8 packages | 18 |

---

## Frontend — `npm audit` (initial)

Source: `/tmp/projectapp-npm-audit.json`

| Package | Severity | Notes |
|---|---|---|
| `@unhead/vue` | moderate | via `unhead` |
| `@xmldom/xmldom` | high | DoS, XML injection (multiple CVEs) |
| `axios` | moderate | NO_PROXY bypass SSRF; cloud metadata exfiltration |
| `dompurify` | moderate | ADD_TAGS / FORBID_TAGS bypass; SAFE_FOR_TEMPLATES bypass; prototype pollution -> XSS |
| `follow-redirects` | moderate | leaks Custom Auth Headers on cross-domain redirects |
| `postcss` | moderate | XSS via unescaped `</style>` in CSS stringify |
| `unhead` | moderate | `hasDangerousProtocol()` bypass |
| `vite` | high | Path traversal in optimized deps `.map`; `server.fs.deny` bypass; arbitrary file read via WS |

**Totals:** 0 critical / 2 high / 6 moderate / 0 low (8 total).

## Frontend — `npm outdated` (initial)

Source: `/tmp/projectapp-npm-outdated.json`

Outdated packages (current → wanted → latest):

- @babel/preset-env: 7.29.0 → 7.29.2 → 7.29.2
- @nuxtjs/i18n: 9.5.6 → 9.5.6 → 10.3.0  *(latest is major bump — skip)*
- @pinia/nuxt: 0.5.5 → 0.5.5 → 0.11.3  *(0.x: minor only)*
- @splinetool/runtime: 1.12.54 → 1.12.90 → 1.12.90
- @vue/test-utils: 2.4.6 → 2.4.10 → 2.4.10
- @vueuse/core: 10.11.1 → 10.11.1 → 14.2.1  *(major bump — skip)*
- axios: 1.13.5 → 1.15.2 → 1.15.2
- babel-jest: 29.7.0 → 29.7.0 → 30.3.0  *(major bump — skip)*
- dompurify: 3.3.2 → 3.4.1 → 3.4.1
- gsap: 3.14.2 → 3.15.0 → 3.15.0
- jest: 29.7.0 → 29.7.0 → 30.3.0  *(major bump — skip)*
- jsdom: 28.1.0 → 28.1.0 → 29.1.1  *(major bump — skip)*
- marked: 17.0.4 → 17.0.6 → 18.0.2  *(latest is major — minor only)*
- nuxt: 3.21.1 → 3.21.4 → 4.4.4  *(latest is major — patch only within 3.x)*
- pinia: 2.3.1 → 2.3.1 → 3.0.4  *(major bump — skip)*
- sweetalert2: 11.26.18 → 11.26.24 → 11.26.24
- swiper: 12.1.2 → 12.1.4 → 12.1.4
- vue: 3.5.28 → 3.5.33 → 3.5.33
- vue-router: 4.6.4 → 4.6.4 → 5.0.6  *(major bump — skip)*
- vuedraggable: 4.1.0 → 4.1.0 → 2.24.3  *(latest tag is older, skip)*

---

## Backend — `pip-audit` (initial)

Source: `/tmp/projectapp-pip-audit.json`

Found **60 known vulnerabilities** in **8 packages**:

| Package | Current | Vulns | Min in-major fix |
|---|---|---|---|
| Django | 5.0.6 | 27 | 5.2.x available (in major 5) |
| djangorestframework | 3.15.1 | 1 (CVE-2024-21520) | 3.15.2+ |
| pillow | 10.3.0 | 2 | 10.x has no fix; fixes in 12.x (major bump — skip) |
| requests | 2.31.0 | 3 | 2.32.x / 2.33.x (in major 2) |
| sqlparse | 0.5.0 | 1 (GHSA-27jp-wm6q-gp25) | 0.5.4 |
| pytest | 8.3.2 | 1 (CVE-2025-71176) | fixed in 9.x (major bump — skip) |
| cryptography | 43.0.3 | 3 | 44.0.1+ within constraint `<44.0` blocks; relax constraint within major 4? Latest: 47.x. Will go to 43.x latest patch and update minor floor cautiously. |
| pypdf | 4.3.1 | 22 | fixes start at 6.x (major bump — skip; pinned `>=4.0,<5.0`) |

## Backend — `pip list --outdated` (initial)

Source: `/tmp/projectapp-pip-outdated.json`

- asgiref 3.8.1 → 3.11.1
- coverage 7.6.1 → 7.13.5
- cryptography 43.0.3 → 47.0.0  *(constrained to `<44.0`; major bumps skipped)*
- Django 5.0.6 → 6.0.4  *(latest is major 6 — stay within major 5)*
- django-cors-headers 4.3.1 → 4.9.0
- djangorestframework 3.15.1 → 3.17.1
- Faker 28.4.1 → 40.15.0  *(major bump — skip)*
- freezegun 1.4.0 → 1.5.5
- gunicorn 23.0.0 → 25.3.0  *(constrained `<24.0`)*
- pillow 10.3.0 → 12.2.0  *(major bump — skip; pinned 10.3.0)*
- pypdf 4.3.1 → 6.10.2  *(constrained `<5.0`)*
- pytest 8.3.2 → 9.0.3  *(major bump — skip)*
- pytest-cov 5.0.0 → 7.1.0  *(major bump — skip)*
- pytest-django 4.8.0 → 4.12.0
- requests 2.31.0 → 2.33.1
- six 1.16.0 → 1.17.0
- sqlparse 0.5.0 → 0.5.5
- tzdata 2024.1 → 2026.2

---

## Plan

### Frontend
- Run `npm audit fix` (no `--force`).
- Run `npx --yes npm-check-updates -u --target minor` and `npm install`.
- Skip all majors listed above.

### Backend
Patch+minor bumps within current majors (and respecting current pin constraints):
- Django 5.0.6 → 5.2.x (patch+minor, stays in major 5)
- djangorestframework 3.15.1 → 3.17.x
- requests 2.31.0 → 2.33.1
- sqlparse 0.5.0 → 0.5.5
- pillow stays 10.3.0 (no in-major fix; latest 10.x = 10.3.0)
- pypdf stays in `>=4.0,<5.0`; will bump to 4.3.1 latest in 4.x
- cryptography stays in `<44.0`; will bump to latest 43.x (43.0.3 currently)
- asgiref → 3.11.x, coverage → 7.13.x, django-cors-headers → 4.9.x, freezegun → 1.5.x, pytest-django → 4.12.x, six → 1.17.x, tzdata → 2026.2, gunicorn stays `<24.0` so latest 23.x.

## Updates Applied

### Frontend (commit `deps(frontend): apply patch+minor updates`)
- `npm audit fix` resolved all 8 reported vulnerabilities (2 high / 6 moderate -> 0).
- `npx npm-check-updates -u --target minor` then `npm install`.
- `package.json` bumps:
  - @babel/preset-env 7.29.0 -> 7.29.2
  - @headlessui/vue 1.7.22 -> 1.7.23
  - @heroicons/vue 2.1.3 -> 2.2.0
  - @nuxtjs/i18n 9.1.0 -> 9.5.6
  - @nuxtjs/tailwindcss 6.12.0 -> 6.14.0
  - @pinia/nuxt 0.5.5 -> 0.9.0  (rolled back from 0.11.3, see Rollbacks)
  - @splinetool/runtime 1.9.37 -> 1.12.90
  - @vue/test-utils 2.4.6 -> 2.4.10
  - @vueuse/core 10.0.0 -> 10.11.1
  - axios 1.7.2 -> 1.15.2
  - dompurify 3.3.2 -> 3.4.1
  - gsap 3.13.0 -> 3.15.0
  - lottie-web 5.12.2 -> 5.13.0
  - marked 17.0.4 -> 17.0.6
  - nuxt 3.14.0 -> 3.21.4
  - pinia 2.1.7 -> 2.3.1
  - sweetalert2 11.11.1 -> 11.26.24
  - swiper 12.0.3 -> 12.1.4
  - video.js 8.12.0 -> 8.23.8
  - vue 3.4.21 -> 3.5.33
  - vue-router 4.3.0 -> 4.6.4
  - vue3-marquee 4.2.0 -> 4.2.2
- Final `npm audit`: **0 vulnerabilities**.
- Remaining outdated (all major bumps, intentionally skipped): @nuxtjs/i18n (10.x), @pinia/nuxt (0.11.x — pulls pinia 3), @vueuse/core (14.x), babel-jest (30.x), jest (30.x), jsdom (29.x), marked (18.x), nuxt (4.x), pinia (3.x), vue-router (5.x).

### Backend (commit `deps(backend): apply patch+minor updates`)
- `requirements.txt` bumps (within current major / pin constraints):
  - asgiref 3.8.1 -> 3.11.1
  - Django 5.0.6 -> 5.2.13  (stays in major 5; resolves 27 CVEs)
  - django-cors-headers 4.3.1 -> 4.9.0
  - djangorestframework 3.15.1 -> 3.17.1  (resolves CVE-2024-21520)
  - pillow 10.3.0 -> 10.4.0  (latest in major 10; remaining CVEs only fixed in 12.x)
  - requests 2.31.0 -> 2.33.1  (resolves 3 CVEs)
  - six 1.16.0 -> 1.17.0
  - sqlparse 0.5.0 -> 0.5.5  (resolves GHSA-27jp-wm6q-gp25)
  - tzdata 2024.1 -> 2026.2
  - pytest-django 4.8.0 -> 4.12.0
  - coverage 7.6.1 -> 7.13.5
  - freezegun 1.4.0 -> 1.5.5
- `pip-audit` after updates: **28 vulnerabilities remaining in 4 packages** (down from 60 in 8). All require major bumps blocked by repo pin constraints / policy:
  - pillow 10.4.0: 2 CVEs — fixes only in 12.x.
  - pytest 8.3.2: 1 CVE — fix in 9.x (major bump skipped).
  - cryptography 43.0.3: 3 CVEs — fixes in 44.0.1+, but pin is `cryptography>=42.0,<44.0`; staying within the documented range.
  - pypdf 4.3.1: 22 CVEs — fixes in 6.x, but pin is `pypdf>=4.0,<5.0`; staying within the documented range.

## Rollbacks
- **Frontend `@pinia/nuxt`**: `npm-check-updates --target minor` proposed `^0.11.3` but that release peer-depends on `pinia@^3` (a major bump for pinia, which we're skipping). `npm install` failed with `ERESOLVE`. Rolled back to `^0.9.0`, the latest 0.x release that still supports `pinia@^2.3`. `npm install` succeeded with 0 vulnerabilities.
- No backend rollbacks; `pip install -r requirements.txt` succeeded on the first attempt.

## Verification Results

### Frontend
- `npm audit`: 0 vulnerabilities.
- `npm run build` (Nuxt build): success. Total bundle size 12.7 MB (2.77 MB gzip).
- `npm run test` / `npm run lint`: not executed (CLAUDE.md prohibits running full suites; no lint script defined in package.json; jest harness exists but blanket runs are forbidden by repo rules).

### Backend
- `python manage.py check`: `System check identified no issues (0 silenced).`
- `pytest --collect-only`: 3621 tests collected, no collection errors (Django 5.2.13 + DRF 3.17.1 imports fine).
- Targeted slices (per CLAUDE.md "never run the full backend suite"):
  - `pytest tests/test_markdown_parser.py`: 39 passed.
  - `pytest accounts/tests/test_serializers.py`: 84 passed.
- Only deprecation warning observed: `RemovedInDjango60Warning` for `forms.URLField.assume_scheme` default. Non-blocking; surfaces because Django 5.2 announces the future 6.0 default. No code changes required for this audit.

