#!/usr/bin/env node
/**
 * Fails if the flow registry and @flow: usage in E2E specs diverge:
 * - Every referenced @flow:id must exist in the registry
 * - Every flow with expectedSpecs > 0 must be referenced in at least one spec
 *
 * Registry layout: sharded (e2e/flows/*.json, F46) with monolith fallback —
 * see lib/flow-registry.mjs.
 *
 * Usage: node frontend/scripts/check-flow-definitions-sync.mjs
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { collectAllReferencedFlowIds } from './lib/e2e-flow-refs.mjs';
import { loadFlowRegistry } from './lib/flow-registry.mjs';

const __file = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__file), '..');
const e2eDir = path.join(ROOT, 'e2e');
const flowTagsPath = path.join(ROOT, 'e2e', 'helpers', 'flow-tags.js');

const definitions = loadFlowRegistry(e2eDir);
const definedIds = new Set(Object.keys(definitions.flows || {}));
const { referencedIds } = collectAllReferencedFlowIds(e2eDir, flowTagsPath);

const unknownInSpecs = [...referencedIds].filter((id) => !definedIds.has(id)).sort();

const requiredIds = Object.entries(definitions.flows || {})
  .filter(([, def]) => (def?.expectedSpecs ?? 1) > 0)
  .map(([id]) => id);
const missingRequired = requiredIds.filter((id) => !referencedIds.has(id)).sort();

let failed = false;

if (unknownInSpecs.length > 0) {
  failed = true;
  console.error('\n❌ @flow: IDs used in E2E specs but missing from flow-definitions.json:\n');
  for (const id of unknownInSpecs) {
    console.error(`   - ${id}`);
  }
  console.error('');
}

if (missingRequired.length > 0) {
  failed = true;
  console.error('\n❌ flow-definitions.json entries with expectedSpecs > 0 never referenced in any spec tag:\n');
  for (const id of missingRequired) {
    const name = definitions.flows[id]?.name || id;
    console.error(`   - ${id} (${name})`);
  }
  console.error('');
}

if (failed) {
  console.error('Fix: add missing definitions / tags, or set expectedSpecs to 0 for documented-only flows.\n');
  process.exit(1);
}

console.log(
  `✅ flow-definitions.json ↔ E2E @flow: tags in sync (${referencedIds.size} referenced, ${definedIds.size} defined).\n`,
);
process.exit(0);
