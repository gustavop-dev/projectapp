#!/usr/bin/env python3
"""Reparte los tests del backend en shards y mide el desbalance.

Read-only. Lee el `pytest-results.xml` que el CI ya sube como artifact
(`coverage-backend`) y que trae el tiempo de CADA test, agrega por archivo y por
dominio, y contrasta el reparto declarado en `backend/ci-shards.yml` contra la
duracion real.

Existe porque la cantidad de tests es un proxy enganoso: `test_fake_data_contract.py`
son 29 tests que corren tres seeders completos, y los 25 archivos de PDF generan
documentos de verdad con reportlab. Repartir por conteo pone esos dos en el mismo
shard y el balance se rompe.

Uso:
    gh run download <run-id> -n coverage-backend -D /tmp/durations
    python3 scripts/ci/backend-shard-plan.py --junit /tmp/durations/pytest-results.xml

    # ver que archivos pesan mas, para mover a mano entre dominios
    python3 scripts/ci/backend-shard-plan.py --junit <path> --top 25
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / 'backend' / 'ci-shards.yml'


def parse_manifest(path: Path):
    """Lee el manifiesto sin depender de PyYAML.

    El formato es deliberadamente plano — `shard: N` seguido de `- ruta` — para
    que el mismo archivo lo pueda leer un `grep` desde el workflow sin instalar
    nada en el runner.
    """
    shards: dict[int, list[str]] = {}
    current: int | None = None
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.split('#', 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith('shard:'):
            current = int(line.split(':', 1)[1].strip())
            shards[current] = []
        elif line.lstrip().startswith('- ') and current is not None:
            shards[current].append(line.lstrip()[2:].strip())
    return shards


def durations_by_file(junit_path: Path) -> dict[str, float]:
    """Segundos acumulados por archivo de test.

    El atributo `file` del junit de pytest ya viene relativo a `backend/`, que es
    el rootdir; se normaliza para que matchee las rutas del manifiesto.

    El junit llega por red (`gh run download`), asi que se rechaza cualquier
    declaracion de entidades antes de parsear: ElementTree no resuelve entidades
    externas, pero si es vulnerable a la expansion recursiva tipo billion-laughs,
    y un DOCTYPE no tiene nada que hacer en un reporte de pytest.
    """
    head = junit_path.read_bytes()[:4096].lower()
    if b'<!doctype' in head or b'<!entity' in head:
        raise ValueError(
            f'{junit_path}: declara entidades XML; un junit de pytest no lo hace.'
        )
    tree = ET.parse(junit_path)
    totals: dict[str, float] = defaultdict(float)
    for case in tree.iter('testcase'):
        path = file_of(case.get('classname') or '')
        if not path:
            continue
        totals[path] += float(case.get('time') or 0.0)
    return dict(totals)


def file_of(classname: str) -> str:
    """Ruta del archivo a partir del `classname` punteado del junit.

    pytest no emite el atributo `file`: manda `content.tests.views.test_x.TestY`
    (o sin la clase, para tests a nivel de modulo). El modulo es el ULTIMO
    segmento que arranca con `test_` — las clases son `Test*` con mayuscula por
    `python_classes` en pytest.ini, asi que no hay ambiguedad.
    """
    parts = classname.split('.')
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].startswith('test_'):
            return '/'.join(parts[:i + 1]) + '.py'
    return ''


def shard_of(test_file: str, shards: dict[int, list[str]], catch_all: int) -> int:
    """A que shard cae un archivo. El catch-all se queda con lo no reclamado."""
    for index, prefixes in sorted(shards.items()):
        if index == catch_all:
            continue
        for prefix in prefixes:
            if test_file == prefix or test_file.startswith(prefix.rstrip('/') + '/'):
                return index
    return catch_all


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--junit', required=True, type=Path,
                        help='pytest-results.xml del artifact coverage-backend')
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--top', type=int, default=0,
                        help='listar los N archivos mas lentos')
    parser.add_argument('--max-skew', type=float, default=30.0,
                        help='desvio maximo tolerado sobre la media, en %%')
    parser.add_argument('--emit-weights', type=Path, default=None,
                        help='escribir los pesos medidos para el repartidor')
    args = parser.parse_args()

    if not args.junit.exists():
        print(f'ERROR: no existe {args.junit}', file=sys.stderr)
        return 2

    totals = durations_by_file(args.junit)
    grand_total = sum(totals.values())
    print(f'Tests medidos:  {len(totals)} archivos')
    print(f'Tiempo total:   {grand_total / 60:.1f} min de ejecucion pura\n')

    if args.emit_weights:
        # Redondeado a centesimas: el peso solo ordena el bin-packing, y un JSON
        # con 15 decimales genera diff en cada corrida sin significar nada.
        payload = dict(sorted((k, round(v, 2)) for k, v in totals.items()))
        args.emit_weights.write_text(
            json.dumps(payload, indent=1, sort_keys=True) + '\n', encoding='utf-8',
        )
        print(f'pesos escritos: {args.emit_weights} ({len(payload)} archivos)\n')

    if args.top:
        print(f'── {args.top} archivos mas lentos ──')
        for path, secs in sorted(totals.items(), key=lambda kv: -kv[1])[:args.top]:
            print(f'  {secs / 60:6.2f} min  {path}')
        print()

    if not args.manifest.exists():
        print(f'(sin manifiesto en {args.manifest}: solo se midio)')
        return 0

    shards = parse_manifest(args.manifest)
    if not shards:
        print(f'ERROR: manifiesto vacio o ilegible: {args.manifest}', file=sys.stderr)
        return 2
    catch_all = max(shards)

    per_shard: dict[int, float] = defaultdict(float)
    files_per_shard: dict[int, int] = defaultdict(int)
    for path, secs in totals.items():
        index = shard_of(path, shards, catch_all)
        per_shard[index] += secs
        files_per_shard[index] += 1

    count = len(shards)
    mean = grand_total / count
    print(f'── reparto en {count} shards (media {mean / 60:.1f} min) ──')
    worst = 0.0
    for index in sorted(shards):
        secs = per_shard[index]
        skew = (secs - mean) / mean * 100 if mean else 0.0
        worst = max(worst, abs(skew))
        tag = ' ← catch-all' if index == catch_all else ''
        print(f'  {index}/{count}  {secs / 60:6.2f} min  '
              f'{files_per_shard[index]:3d} archivos  {skew:+6.1f}%{tag}')

    print(f'\nDesbalance maximo: {worst:.1f}% (tolerado {args.max_skew:.0f}%)')
    projected = max(per_shard.values()) / 60 if per_shard else 0.0
    print(f'Wall clock proyectado: {projected:.1f} min '
          f'(lo marca el shard mas lento, no la media)')

    if worst > args.max_skew:
        print('\nDESBALANCEADO: mover archivos entre dominios en el manifiesto.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
