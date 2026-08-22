import { appendFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  RESPONSIVE_MODULES,
  RESPONSIVE_MODULE_NAMES,
  modulesForChangedFiles,
} from '../config/responsiveAcceptance.js';

const frontendRoot = resolve(fileURLToPath(new URL('..', import.meta.url)));
const repoRoot = resolve(frontendRoot, '..');
const args = new Set(process.argv.slice(2));

function git(...command) {
  const result = spawnSync('git', command, { cwd: repoRoot, encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr.trim() || `git ${command.join(' ')} falló`);
  return result.stdout.trim();
}

function resolveChangedFiles() {
  if (process.env.RESPONSIVE_ALL === '1' || args.has('--all')) return null;
  const base = process.env.RESPONSIVE_BASE_SHA
    || git('merge-base', 'HEAD', process.env.RESPONSIVE_BASE_REF || 'origin/main');
  const diffArgs = ['diff', '--name-only', '--diff-filter=ACMR', base];
  if (process.env.RESPONSIVE_HEAD_SHA) diffArgs.push(process.env.RESPONSIVE_HEAD_SHA);
  const output = git(...diffArgs);
  return output ? output.split('\n') : [];
}

const changedFiles = resolveChangedFiles();
const modules = changedFiles === null
  ? [...RESPONSIVE_MODULE_NAMES]
  : modulesForChangedFiles(changedFiles);

if (args.has('--github-output')) {
  if (!process.env.GITHUB_OUTPUT) throw new Error('GITHUB_OUTPUT no está definido');
  await appendFile(process.env.GITHUB_OUTPUT, `modules=${JSON.stringify(modules)}\n`);
}

console.log(`Módulos responsivos: ${modules.length ? modules.join(', ') : 'ninguno'}`);
if (args.has('--list') || args.has('--github-output') || modules.length === 0) process.exit(0);

const grep = modules.map((name) => RESPONSIVE_MODULES[name].tag).join('|');
const result = spawnSync(
  process.platform === 'win32' ? 'npx.cmd' : 'npx',
  ['playwright', 'test', '--grep', grep],
  {
    cwd: frontendRoot,
    env: { ...process.env, E2E_RESPONSIVE: '1' },
    stdio: 'inherit',
  },
);
process.exit(result.status ?? 1);
