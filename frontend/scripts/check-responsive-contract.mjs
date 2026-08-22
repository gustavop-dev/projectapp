import { readdir, readFile } from 'node:fs/promises';
import { join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  RESPONSIVE_MODULES,
  RESPONSIVE_MODULE_NAMES,
  RESPONSIVE_VIEWPORT_NAMES,
  responsiveOwnerForView,
} from '../config/responsiveAcceptance.js';
import { PANEL_VIEWPORTS } from '../config/responsive.js';
import { viewCatalogSections } from '../config/viewCatalog.js';

const frontendRoot = resolve(fileURLToPath(new URL('..', import.meta.url)));
const repoRoot = resolve(frontendRoot, '..');

async function walkVueFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = await Promise.all(entries.map(async (entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return walkVueFiles(path);
    return entry.isFile() && entry.name.endsWith('.vue') ? [path] : [];
  }));
  return files.flat();
}

function reportDifference(label, values) {
  if (!values.length) return;
  throw new Error(`${label}:\n- ${values.join('\n- ')}`);
}

const pages = (await walkVueFiles(join(frontendRoot, 'pages')))
  .map((path) => relative(repoRoot, path).replaceAll('\\', '/'))
  .sort();
const catalogEntries = viewCatalogSections.flatMap((section) => (
  section.views.map((view) => ({ sectionId: section.id, ...view }))
));
const catalogFiles = catalogEntries.map((view) => view.file).sort();

reportDifference('Páginas ausentes del catálogo', pages.filter((file) => !catalogFiles.includes(file)));
reportDifference('Entradas obsoletas del catálogo', catalogFiles.filter((file) => !pages.includes(file)));

const duplicates = [...new Set(catalogFiles.filter((file, index) => catalogFiles.indexOf(file) !== index))];
reportDifference('Páginas duplicadas en el catálogo', duplicates);

const viewportWidths = RESPONSIVE_VIEWPORT_NAMES.map((name) => PANEL_VIEWPORTS[name].width);
const expectedWidths = [412, 835, 1195, 1440, 2560];
if (JSON.stringify(viewportWidths) !== JSON.stringify(expectedWidths)) {
  throw new Error(`Los viewports canónicos deben ser ${expectedWidths.join(', ')}; recibidos: ${viewportWidths.join(', ')}`);
}

const withoutOwner = catalogEntries
  .filter((view) => !responsiveOwnerForView(view.sectionId, view))
  .map((view) => `${view.url} (${view.file})`);
reportDifference('Vistas sin dueño responsivo', withoutOwner);

for (const name of RESPONSIVE_MODULE_NAMES) {
  const entry = RESPONSIVE_MODULES[name];
  if (!entry.tag.startsWith('@responsive:') || entry.checklist.length < 3 || entry.paths.length === 0) {
    throw new Error(`Contrato incompleto para el módulo ${name}`);
  }
}

const specFiles = [];
async function walkSpecs(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map(async (entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return walkSpecs(path);
    return entry.isFile() && entry.name.endsWith('.spec.js') ? [path] : [];
  }));
  return nested.flat();
}

specFiles.push(...await walkSpecs(join(frontendRoot, 'e2e')));
const specSource = (await Promise.all(specFiles.map((path) => readFile(path, 'utf8')))).join('\n');
const tagsWithoutTest = RESPONSIVE_MODULE_NAMES
  .filter((name) => !specSource.includes(RESPONSIVE_MODULES[name].tag))
  .map((name) => RESPONSIVE_MODULES[name].tag);
reportDifference('Módulos sin E2E responsivo', tagsWithoutTest);

console.log(`Contrato responsivo OK: ${pages.length} vistas, ${RESPONSIVE_MODULE_NAMES.length} módulos, ${RESPONSIVE_VIEWPORT_NAMES.length} viewports.`);
