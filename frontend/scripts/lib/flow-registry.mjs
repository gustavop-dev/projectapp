/**
 * Dual-layout flow registry loader (F46, 2026-08-17).
 *
 * Sharded layout (this repo, declared in .testquality.yml as
 * `flow_definitions_dir: flows`): one JSON per flow under e2e/flows/
 * ({ id, ...definition }); `_meta.json` carries registry-level fields
 * (version, lastUpdated). Falls back to the classic e2e/flow-definitions.json
 * monolith, so the loader keeps working on branches not yet migrated.
 *
 * Returns the monolith SHAPE either way: { version, lastUpdated, flows: {...} }
 * — existing consumers stay untouched beyond the import.
 */
import fs from 'node:fs';
import path from 'node:path';

export function loadFlowRegistry(e2eRoot) {
  const flowsDir = path.join(e2eRoot, 'flows');
  if (fs.existsSync(flowsDir) && fs.statSync(flowsDir).isDirectory()) {
    const flows = {};
    let meta = {};
    for (const f of fs.readdirSync(flowsDir).sort()) {
      if (!f.endsWith('.json')) continue;
      const data = JSON.parse(fs.readFileSync(path.join(flowsDir, f), 'utf-8'));
      if (f === '_meta.json') {
        meta = data;
        continue;
      }
      const { id, ...def } = data;
      flows[id ?? f.replace(/\.json$/, '')] = def;
    }
    return { ...meta, flows };
  }
  const mono = path.join(e2eRoot, 'flow-definitions.json');
  if (fs.existsSync(mono)) {
    return JSON.parse(fs.readFileSync(mono, 'utf-8'));
  }
  return { version: '0.0.0', lastUpdated: '', flows: {} };
}
