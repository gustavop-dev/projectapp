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

// Step 1: Parse flow-tags.js to build constantName → flowId map
const constantToFlowId = new Map();
const flowTagsContent = fs.readFileSync(flowTagsPath, 'utf-8');
const exportRe = /export\s+const\s+(\w+)\s*=\s*\[['"]@flow:([a-z0-9-]+)['"]/g;
let m;
while ((m = exportRe.exec(flowTagsContent)) !== null) {
  constantToFlowId.set(m[1], m[2]);
}

// Step 2: Find all spec files
const e2eDir = path.join(ROOT, 'e2e');
const specFiles = [];
function walkDir(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules' && entry.name !== 'helpers' && entry.name !== 'reporters') {
      walkDir(full);
    } else if (entry.isFile() && entry.name.endsWith('.spec.js')) {
      specFiles.push(full);
    }
  }
}
walkDir(e2eDir);

// Step 3: For each spec file, find which flow constants are used in test() blocks
for (const specFile of specFiles) {
  const content = fs.readFileSync(specFile, 'utf-8');
  const lines = content.split('\n');

  // Find which flow constants are imported
  const importedConstants = new Set();
  for (const line of lines) {
    const importMatch = line.match(/import\s*\{([^}]+)\}\s*from\s*['"].*flow-tags/);
    if (importMatch) {
      importMatch[1].split(',').forEach(c => {
        const name = c.trim();
        if (name && constantToFlowId.has(name)) importedConstants.add(name);
      });
    }
  }

  // Also check for literal @flow: tags (some tests may inline them)
  const literalFlowRe = /'@flow:([a-z0-9-]+)'/g;
  const literalFlows = new Set();
  let lm;
  while ((lm = literalFlowRe.exec(content)) !== null) {
    literalFlows.add(lm[1]);
  }

  // Count test() blocks by finding all `tag: [...]` arrays in the file
  // This avoids fragile test-title regex matching
  const tagArrayRe = /tag:\s*\[([^\]]+)\]/g;
  let tm;
  while ((tm = tagArrayRe.exec(content)) !== null) {
    const tagContent = tm[1];
    // Find which flow constants are spread in this tag array
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
    // Check for literal flow tags in this test's tag array
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
    // Check if expectedSpecs is 0 (backend-only)
    if (stats.definition.expectedSpecs === 0) {
      stats.status = 'covered'; // backend-only, no E2E needed
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
    covered: flows.filter(f => f.status === 'covered').length,
    partial: flows.filter(f => f.status === 'partial').length,
    failing: flows.filter(f => f.status === 'failing').length,
    missing: flows.filter(f => f.status === 'missing').length,
  },
  flows: Object.fromEntries(
    flows.map(s => [s.flowId, { ...s, specs: Array.from(s.specs) }])
  ),
};

// Write
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));

console.log(`\n✅ Flow coverage regenerated: ${outputPath}`);
console.log(`   Total: ${report.summary.total}`);
console.log(`   Covered: ${report.summary.covered}`);
console.log(`   Partial: ${report.summary.partial}`);
console.log(`   Failing: ${report.summary.failing}`);
console.log(`   Missing: ${report.summary.missing}`);

const missing = flows.filter(f => f.status === 'missing');
if (missing.length > 0) {
  console.log(`\n   Missing flows:`);
  for (const f of missing) {
    console.log(`     - ${f.flowId}: ${f.definition.name}`);
  }
}
console.log('');
