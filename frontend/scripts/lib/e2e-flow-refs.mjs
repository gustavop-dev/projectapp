import fs from 'node:fs';
import path from 'node:path';

const SPEC_SUFFIXES = ['.spec.js', '.spec.mjs', '.spec.ts', '.spec.tsx'];
const SKIPPED_DIRS = new Set(['node_modules', 'helpers', 'reporters']);

/**
 * @param {string} flowTagsSource
 * @returns {Map<string, string>}
 */
export function parseFlowTagsConstantsToFlowIds(flowTagsSource) {
  const constantToFlowId = new Map();
  const exportRe = /export\s+const\s+(\w+)\s*=\s*\[['"]@flow:([a-z0-9-]+)['"]/g;
  let m;
  while ((m = exportRe.exec(flowTagsSource)) !== null) {
    constantToFlowId.set(m[1], m[2]);
  }
  return constantToFlowId;
}

/**
 * @param {string} e2eDir absolute path to frontend/e2e
 * @returns {string[]}
 */
export function listE2eSpecFiles(e2eDir) {
  const specFiles = [];
  function walkDir(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name.startsWith('.') || SKIPPED_DIRS.has(entry.name)) continue;
        walkDir(full);
      } else if (entry.isFile() && SPEC_SUFFIXES.some((s) => entry.name.endsWith(s))) {
        specFiles.push(full);
      }
    }
  }
  walkDir(e2eDir);
  return specFiles;
}

/**
 * Flow IDs referenced in Playwright `tag: [...]` arrays (flow-tags constants + @flow: literals).
 * Matches static analysis used by regenerate-flow-coverage.mjs.
 *
 * @param {string} content
 * @param {Map<string, string>} constantToFlowId
 * @returns {Set<string>}
 */
export function collectReferencedFlowIdsFromSpecContent(content, constantToFlowId) {
  const ids = new Set();
  const tagArrayRe = /tag:\s*\[([^\]]+)\]/g;
  let tm;
  while ((tm = tagArrayRe.exec(content)) !== null) {
    const tagContent = tm[1];
    for (const [constName, flowId] of constantToFlowId) {
      if (tagContent.includes(`...${constName}`) || tagContent.includes(constName)) {
        ids.add(flowId);
      }
    }
    const literalInTag = /@flow:([a-z0-9-]+)/g;
    let ltm;
    while ((ltm = literalInTag.exec(tagContent)) !== null) {
      ids.add(ltm[1]);
    }
  }
  return ids;
}

/**
 * @param {string} e2eDir
 * @param {string} flowTagsPath
 * @returns {{ referencedIds: Set<string>, constantToFlowId: Map<string, string> }}
 */
export function collectAllReferencedFlowIds(e2eDir, flowTagsPath) {
  const flowTagsContent = fs.readFileSync(flowTagsPath, 'utf-8');
  const constantToFlowId = parseFlowTagsConstantsToFlowIds(flowTagsContent);
  const referencedIds = new Set();
  for (const specFile of listE2eSpecFiles(e2eDir)) {
    const content = fs.readFileSync(specFile, 'utf-8');
    for (const id of collectReferencedFlowIdsFromSpecContent(content, constantToFlowId)) {
      referencedIds.add(id);
    }
  }
  return { referencedIds, constantToFlowId };
}
