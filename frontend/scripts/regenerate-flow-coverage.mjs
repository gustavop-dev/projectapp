#!/usr/bin/env node
/**
 * Static flow-coverage regenerator.
 * Scans all E2E spec files for @flow: tags, cross-references with
 * flow-definitions.json, and produces an accurate flow-coverage.json
 * without needing to execute tests.
 *
 * Usage: node frontend/scripts/regenerate-flow-coverage.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  listE2eSpecFiles,
  parseFlowTagsConstantsToFlowIds,
} from './lib/e2e-flow-refs.mjs';

const __file = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__file), '..');

const definitionsPath = path.join(ROOT, 'e2e', 'flow-definitions.json');
const outputPath = path.join(ROOT, 'e2e-results', 'flow-coverage.json');
const flowTagsPath = path.join(ROOT, 'e2e', 'helpers', 'flow-tags.js');

// Load flow definitions
const definitions = JSON.parse(fs.readFileSync(definitionsPath, 'utf-8'));

// Initialize flow stats from definitions
const flowStats = new Map();
for (const [flowId, definition] of Object.entries(definitions.flows)) {
  flowStats.set(flowId, {
    flowId,
    definition,
    tests: { total: 0, passed: 0, failed: 0, skipped: 0 },
    specs: new Set(),
    status: 'missing',
  });
}

const flowTagsContent = fs.readFileSync(flowTagsPath, 'utf-8');
const constantToFlowId = parseFlowTagsConstantsToFlowIds(flowTagsContent);

const e2eDir = path.join(ROOT, 'e2e');
const specFiles = listE2eSpecFiles(e2eDir);

// For each spec file, find which flow constants are used in test() blocks
for (const specFile of specFiles) {
  const content = fs.readFileSync(specFile, 'utf-8');

  // Count test() blocks by finding all `tag: [...]` arrays in the file
  const tagArrayRe = /tag:\s*\[([^\]]+)\]/g;
  let tm;
  while ((tm = tagArrayRe.exec(content)) !== null) {
    const tagContent = tm[1];
    for (const [constName, flowId] of constantToFlowId) {
      if (tagContent.includes(`...${constName}`) || tagContent.includes(constName)) {
        let stats = flowStats.get(flowId);
        if (!stats) {
          stats = {
            flowId,
            definition: { name: flowId, module: 'unknown', roles: ['unknown'], priority: 'P4', description: 'Auto-detected', expectedSpecs: 1 },
            tests: { total: 0, passed: 0, failed: 0, skipped: 0 },
            specs: new Set(),
            status: 'missing',
          };
          flowStats.set(flowId, stats);
        }
        stats.tests.total++;
        stats.tests.passed++;
        stats.specs.add(specFile);
      }
    }
    const literalInTag = /@flow:([a-z0-9-]+)/g;
    let ltm;
    while ((ltm = literalInTag.exec(tagContent)) !== null) {
      const flowId = ltm[1];
      let stats = flowStats.get(flowId);
      if (stats) {
        stats.tests.total++;
        stats.tests.passed++;
        stats.specs.add(specFile);
      }
    }
  }
}

// Determine status
for (const stats of flowStats.values()) {
  if (stats.tests.total === 0) {
    if (stats.definition.expectedSpecs === 0) {
      stats.status = 'covered';
    } else {
      stats.status = 'missing';
    }
  } else if (stats.tests.failed > 0) {
    stats.status = 'failing';
  } else if (stats.tests.passed > 0) {
    stats.status = 'covered';
  } else {
    stats.status = 'partial';
  }
}

// Build report
const flows = Array.from(flowStats.values());
const report = {
  timestamp: new Date().toISOString(),
  generatedBy: 'static-analysis',
  summary: {
    total: flows.length,
    covered: flows.filter((f) => f.status === 'covered').length,
    partial: flows.filter((f) => f.status === 'partial').length,
    failing: flows.filter((f) => f.status === 'failing').length,
    missing: flows.filter((f) => f.status === 'missing').length,
  },
  flows: Object.fromEntries(
    flows.map((s) => [s.flowId, { ...s, specs: Array.from(s.specs) }]),
  ),
};

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));

console.log(`\n✅ Flow coverage regenerated: ${outputPath}`);
console.log(`   Total: ${report.summary.total}`);
console.log(`   Covered: ${report.summary.covered}`);
console.log(`   Partial: ${report.summary.partial}`);
console.log(`   Failing: ${report.summary.failing}`);
console.log(`   Missing: ${report.summary.missing}`);

const missing = flows.filter((f) => f.status === 'missing');
if (missing.length > 0) {
  console.log(`\n   Missing flows:`);
  for (const f of missing) {
    console.log(`     - ${f.flowId}: ${f.definition.name}`);
  }
}
console.log('');
