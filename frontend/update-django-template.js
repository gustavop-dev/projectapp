import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Determinar rutas absolutas basadas en la ubicación de este script (frontend/)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const staticDir = path.resolve(__dirname, '../backend/static/frontend');
const djangoTemplatesDir = path.resolve(__dirname, '../backend/content/templates');
const sourceIndexPath = path.join(staticDir, 'index.html');
const targetIndexPath = path.join(djangoTemplatesDir, 'index.html');

if (!fs.existsSync(sourceIndexPath)) {
  console.error(`No se encontró el archivo generado: ${sourceIndexPath}.`);
  console.error('Asegúrate de ejecutar "vite build" antes de correr este script.');
  process.exit(1);
}

// Crear el directorio de templates de Django si no existe
if (!fs.existsSync(djangoTemplatesDir)) {
  fs.mkdirSync(djangoTemplatesDir, { recursive: true });
}

// Leer el index.html generado por Vite
const html = fs.readFileSync(sourceIndexPath, 'utf-8');

// Copiarlo tal cual a la carpeta de templates de Django.
// Las referencias a assets ya apuntan a /static/frontend/... gracias a base en vite.config.
fs.writeFileSync(targetIndexPath, html, 'utf-8');

console.log(`index.html copiado desde ${sourceIndexPath} a ${targetIndexPath}`);
