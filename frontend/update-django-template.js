import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const sourceDir = path.resolve(__dirname, '.output/public');
const targetDir = path.resolve(__dirname, '../backend/static/frontend');
const stagingDir = `${targetDir}.new`;
const retiredDir = `${targetDir}.old`;

// 1. Run nuxt generate with cdnURL set for Django static serving.
// PRERENDER_BLOG=1 enables blog post prerendering (slugs fetched from the API;
// see blogPrerenderRoutes in nuxt.config.ts). PRERENDER_API_ORIGIN /
// PRERENDER_REQUIRE_BLOG are inherited from the caller's environment.
console.log('Running nuxt generate...');
execSync('NUXT_APP_CDN_URL=/static/frontend/ PRERENDER_BLOG=1 npx nuxi generate', {
  cwd: __dirname,
  stdio: 'inherit',
});

// 2. Verify output exists
if (!fs.existsSync(sourceDir)) {
  console.error(`Nuxt generate output not found at: ${sourceDir}`);
  process.exit(1);
}

// 3. Copy output to a staging dir next to the live one, then swap with two
// renames. Gunicorn serves these files straight from disk on every request,
// so the live dir must never be empty or half-written.
function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

fs.rmSync(stagingDir, { recursive: true, force: true });
fs.rmSync(retiredDir, { recursive: true, force: true });

console.log(`Copying ${sourceDir} → ${stagingDir}...`);
copyDirSync(sourceDir, stagingDir);

console.log(`Swapping ${stagingDir} → ${targetDir}...`);
if (fs.existsSync(targetDir)) {
  fs.renameSync(targetDir, retiredDir);
}
fs.renameSync(stagingDir, targetDir);
fs.rmSync(retiredDir, { recursive: true, force: true });

console.log('Build complete! Files swapped into backend/static/frontend/');
