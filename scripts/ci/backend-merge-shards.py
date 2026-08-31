#!/usr/bin/env python3
"""Combina los resultados de los shards del backend en un solo veredicto.

Corre en el job `backend-coverage-merge`, desde `backend/`. Hace dos cosas:

1. `coverage combine` sobre los data files parciales de cada shard, y regenera
   `coverage-backend.json` desde el combinado. Ese json es el que consume
   `scripts/coverage-summary-ci.cjs` para el comentario del PR.
2. Funde los N `pytest-results.xml` en uno solo con los atributos sumados.

Lo segundo no es cosmetico: `coverage-summary-ci.cjs` parsea **el primer**
`<testsuite>` con una regex. Con N junit sueltos contaria los tests de un shard
y reportaria una cuarta parte de la suite como si fuera el total.

El piso de coverage NO se evalua aca — lo aplica el step siguiente del workflow
con `coverage report --fail-under`, para que el numero salga del combinado y el
fallo se lea como lo que es.
"""
from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2] / 'backend'
ARTIFACTS = BACKEND / 'shard-artifacts'
JUNIT_OUT = BACKEND / 'pytest-results.xml'
SUMMED = ('tests', 'errors', 'failures', 'skipped')


def run(*args: str) -> None:
    """Corre `coverage` con ESTE interprete, no con el que este en el PATH.

    En el runner `pip install` deja el binario a mano, pero atarse al PATH hace
    que el job dependa de cual python quedo activo. `-m coverage` usa siempre el
    mismo entorno que ya importo estos modulos.
    """
    cmd = [sys.executable, '-m', *args]
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, cwd=BACKEND, check=True)


def collect_coverage_data() -> int:
    """Junta los `.coverage*` de cada shard en el cwd, con nombre unico.

    `coverage combine` busca en el directorio actual, y los shards traen todos
    un archivo llamado igual: se renombran por shard antes de mover.
    """
    moved = 0
    for data in sorted(ARTIFACTS.rglob('.coverage*')):
        if not data.is_file():
            continue
        shard = data.parent.name
        target = BACKEND / f'.coverage.{shard}.{moved}'
        target.write_bytes(data.read_bytes())
        moved += 1
    return moved


def merge_junit() -> int:
    """Un solo `<testsuite>` con los contadores sumados de todos los shards."""
    files = sorted(ARTIFACTS.rglob('pytest-results.xml'))
    if not files:
        return 0

    totals = dict.fromkeys(SUMMED, 0)
    time_total = 0.0
    cases: list[ET.Element] = []
    for path in files:
        # Un junit de pytest no declara entidades; si aparecen, es que el
        # artifact no es lo que decimos que es. ElementTree no resuelve
        # entidades externas pero si expande las recursivas.
        if b'<!doctype' in path.read_bytes()[:4096].lower():
            print(f'ERROR: {path} declara un DOCTYPE.', file=sys.stderr)
            raise SystemExit(2)
        for suite in ET.parse(path).iter('testsuite'):
            for key in SUMMED:
                totals[key] += int(suite.get(key) or 0)
            time_total += float(suite.get('time') or 0.0)
            cases.extend(list(suite))

    root = ET.Element('testsuites', name='pytest tests')
    suite = ET.SubElement(root, 'testsuite', name='pytest')
    for key in SUMMED:
        suite.set(key, str(totals[key]))
    suite.set('time', f'{time_total:.3f}')
    suite.extend(cases)
    ET.ElementTree(root).write(JUNIT_OUT, encoding='utf-8', xml_declaration=True)

    print(f'junit combinado: {len(files)} shards → {totals["tests"]} tests, '
          f'{totals["failures"]} failures, {totals["errors"]} errors, '
          f'{time_total / 60:.1f} min de ejecucion')
    return totals['tests']


def main() -> int:
    if not ARTIFACTS.is_dir():
        print(f'ERROR: no existe {ARTIFACTS}', file=sys.stderr)
        return 2

    moved = collect_coverage_data()
    print(f'data files de coverage recogidos: {moved}')
    if not moved:
        print('ERROR: ningun shard subio datos de coverage.', file=sys.stderr)
        return 2

    run('coverage', 'combine', '--rcfile=coverage.ini')
    run('coverage', 'json', '--rcfile=coverage.ini', '-o', 'coverage-backend.json')

    tests = merge_junit()
    if not tests:
        print('ERROR: ningun shard subio junit.', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
