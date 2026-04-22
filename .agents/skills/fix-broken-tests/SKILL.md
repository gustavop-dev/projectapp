---
name: fix-broken-tests
description: "Fix a user-provided set of broken ProjectApp tests with minimal code changes and only targeted regression runs."
---

# Fix Broken Tests Workflow

## Rules
- Run only the failing tests plus a tight regression slice in the same module.
- Never run the full suite.
- Read `docs/TESTING_QUALITY_STANDARDS.md` before modifying tests.
- Avoid production code changes unless the failing behavior proves the production code is wrong.

## Commands
- Backend: `source .venv/bin/activate && cd backend && pytest path/to/test_file.py::TestClass::test_name -v`
- Frontend unit: `npm --prefix frontend test -- path/to/file.spec.js`
- Frontend E2E: `npm --prefix frontend run e2e -- path/to/spec.js`
- If a dev server is already running for E2E: `cd frontend && E2E_REUSE_SERVER=1 npx playwright test path/to/spec.js`

## Workflow
1. Reproduce the failing test exactly.
2. Read the test and the production code it exercises.
3. Apply the smallest correct fix.
4. Re-run the failing test.
5. Run the narrowest useful regression slice in the same file or module.

## Output Contract
Report:
- original failure
- root cause
- change applied
- exact verification commands
- regression result

---

# Fix Broken Tests (Detailed Workflow)

## Goal

Recibir una lista de tests rotos, entender por qué fallan, arreglarlos y verificar que pasan — junto con una regresión mínima del módulo afectado. Nunca correr la suite completa.

## Restricciones No Negociables

1. **Solo correr los tests que el usuario indicó + regresión del módulo afectado.** Nunca la suite completa.
2. **No modificar código de producción** salvo que sea estrictamente necesario para que el test sea válido.
3. **No agregar comentarios** al código salvo que el usuario lo pida explícitamente.
4. **Respetar los estándares de calidad**: consultar `docs/TESTING_QUALITY_STANDARDS.md` antes de tocar cualquier test.

## Referencia de Estándares

Antes de modificar cualquier test, leer: `docs/TESTING_QUALITY_STANDARDS.md`

## Comandos por Tipo de Test

### Backend (pytest)
```bash
cd backend && source venv/bin/activate
pytest path/to/test_file.py::TestClass::test_name -v
```

### Frontend Unit (Jest)
```bash
cd frontend && npm test -- path/to/test_file.spec.ts
```

### Frontend E2E (Playwright)
```bash
cd frontend && npx playwright test path/to/spec.spec.ts
# Si el servidor ya está corriendo:
cd frontend && E2E_REUSE_SERVER=1 npx playwright test path/to/spec.spec.ts
```

## Flujo de Trabajo

### Paso 1 — Correr los tests rotos para capturar el error
Ejecutar cada test fallido y guardar el output completo (mensaje de error, traceback, línea exacta).

### Paso 2 — Leer y entender el test + el código que prueba
Leer el archivo del test y el código de producción relacionado. Identificar:
- Qué comportamiento se está probando
- Por qué está fallando (API cambió, mock incorrecto, estado global, selector frágil, etc.)
- Si el test en sí es correcto o si el código de producción cambió

### Paso 3 — Arreglar los tests
Aplicar la corrección mínima necesaria. Seguir los patrones de `docs/TESTING_QUALITY_STANDARDS.md`:
- Patrón AAA (Arrange → Act → Assert)
- Un comportamiento por test
- Sin condicionales en el cuerpo del test
- Mocks solo en boundaries externos
- Selectores estables (role > testId > locator)

### Paso 4 — Verificar que los tests arreglados pasan
Correr únicamente los tests que fueron modificados. Confirmar que todos pasan.

### Paso 5 — Regresión del módulo afectado
Correr el archivo de tests completo (no la suite) donde vivían los tests rotos, para verificar que el arreglo no rompió tests vecinos.

### Paso 6 — Reportar
Entregar un resumen con: qué falló, por qué, qué se cambió, y los comandos exactos ejecutados.

## Formato de Output

```
### Test: <nombre_del_test>
- Archivo: <ruta>
- Error original: <mensaje corto>
- Causa raíz: <explicación en 1-2 líneas>
- Cambio aplicado: <qué se modificó>
- Resultado: ✅ Pasa / ❌ Aún falla

### Regresión
- Archivo: <ruta del módulo>
- Comando: <comando exacto>
- Resultado: ✅ Sin regresiones / ⚠️ <detalle si hay problema>
```
