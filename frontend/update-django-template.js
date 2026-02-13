import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const sourceDir = path.resolve(__dirname, '.output/public');
const targetDir = path.resolve(__dirname, '../backend/static/frontend');

// 1. Run nuxt generate with cdnURL set for Django static serving
console.log('Running nuxt generate...');
execSync('NUXT_APP_CDN_URL=/static/frontend/ npx nuxi generate', {
  cwd: __dirname,
  stdio: 'inherit',
});

// 2. Verify output exists
if (!fs.existsSync(sourceDir)) {
  console.error(`Nuxt generate output not found at: ${sourceDir}`);
  process.exit(1);
}

// 3. Clean target directory
if (fs.existsSync(targetDir)) {
  console.log(`Cleaning ${targetDir}...`);
  fs.rmSync(targetDir, { recursive: true, force: true });
}

// 4. Copy entire output to backend/static/frontend/
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

console.log(`Copying ${sourceDir} → ${targetDir}...`);
copyDirSync(sourceDir, targetDir);

console.log('Build complete! Files copied to backend/static/frontend/');
