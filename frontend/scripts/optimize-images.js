import fs from 'fs/promises';
import path from 'path';
import sharp from 'sharp';

// Configuración
const config = {
  // Directorio de origen de las imágenes
  inputDir: './src/assets',
  // Extensiones de archivo a procesar
  extensions: ['.jpg', '.jpeg', '.png', '.webp', '.gif'],
  // Calidad de salida (0-100)
  quality: 80,
  // Convertir imágenes a WebP
  convertToWebp: true,
  // Ignorar carpetas
  ignoreFolders: ['node_modules', 'dist', '.git'],
};

/**
 * Función para recorrer directorios recursivamente
 * @param {string} dir - Directorio a procesar
 * @returns {Promise<string[]>} - Lista de rutas de archivos
 */
async function walkDirectory(dir) {
  const files = [];
  
  try {
    const items = await fs.readdir(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = await fs.stat(fullPath);
      
      if (stat.isDirectory()) {
        if (!config.ignoreFolders.includes(item)) {
          const subDirFiles = await walkDirectory(fullPath);
          files.push(...subDirFiles);
        }
      } else {
        const ext = path.extname(fullPath).toLowerCase();
        if (config.extensions.includes(ext)) {
          files.push(fullPath);
        }
      }
    }
  } catch (err) {
    console.error(`Error al recorrer el directorio ${dir}:`, err);
  }
  
  return files;
}

/**
 * Optimiza una imagen usando sharp
 * @param {string} filePath - Ruta del archivo a optimizar
 */
async function optimizeImage(filePath) {
  try {
    console.log(`Optimizando: ${filePath}`);
    
    // Cargar la imagen con sharp
    let processor = sharp(filePath);
    const metadata = await processor.metadata();
    
    // Optimizar según el tipo de imagen
    switch (metadata.format) {
      case 'jpeg':
      case 'jpg':
        processor = processor.jpeg({ quality: config.quality });
        break;
      case 'png':
        processor = processor.png({ compressionLevel: 9, quality: config.quality });
        break;
      case 'webp':
        processor = processor.webp({ quality: config.quality });
        break;
      case 'gif':
        // Sharp tiene soporte limitado para GIF, solo procesamos metadatos
        break;
      default:
        console.log(`Formato no soportado para optimización: ${metadata.format}`);
        return;
    }
    
    // Guardar la imagen optimizada sobrescribiendo el original
    await processor.toBuffer().then(data => fs.writeFile(filePath, data));
    
    // Si está habilitado, crear versión WebP (excepto si ya es WebP)
    if (config.convertToWebp && metadata.format !== 'webp') {
      const webpPath = filePath.replace(/\.[^.]+$/, '.webp');
      await processor.webp({ quality: config.quality }).toFile(webpPath);
      console.log(`  WebP creado: ${webpPath}`);
    }
  } catch (err) {
    console.error(`Error optimizando ${filePath}:`, err);
  }
}

/**
 * Función principal
 */
async function main() {
  console.log('Iniciando optimización de imágenes...');
  console.log(`Buscando imágenes en: ${config.inputDir}`);
  
  const startTime = Date.now();
  const imageFiles = await walkDirectory(config.inputDir);
  
  console.log(`Encontradas ${imageFiles.length} imágenes para optimizar.`);
  
  // Optimizar todas las imágenes encontradas
  for (const file of imageFiles) {
    await optimizeImage(file);
  }
  
  const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(2);
  console.log(`Optimización completa. Tiempo total: ${elapsedTime}s`);
}

// Ejecutar el script
main().catch(err => {
  console.error('Error en la optimización:', err);
  process.exit(1);
}); 