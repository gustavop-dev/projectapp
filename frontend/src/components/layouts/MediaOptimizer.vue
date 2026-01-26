<template>
  <div style="display: none;">
    <!-- Componente invisible que optimiza la carga de medios -->
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue';

// Configuración
const config = {
  // Tiempo máximo que se mantienen los recursos en memoria antes de liberarlos
  resourceCleanupInterval: 3 * 60 * 1000, // 3 minutos
  // Lista de formatos de archivo a optimizar
  imageFormats: ['.jpg', '.jpeg', '.png', '.webp', '.gif'],
  videoFormats: ['.mp4', '.webm']
};

// Variables para mantener referencias de recursos y temporizadores
let resourceObserver = null;
let resourceCleanupTimer = null;
const loadedResources = new Map();

/**
 * Libera recursos que no se están utilizando
 */
const cleanupUnusedResources = () => {
  console.log('Limpiando recursos no utilizados...');
  
  // Solo procesar si tenemos recursos cargados
  if (loadedResources.size === 0) return;
  
  const now = Date.now();
  const deleteKeys = [];
  
  // Identificar recursos para liberar
  loadedResources.forEach((resource, key) => {
    // No liberar recursos marcados explícitamente como "no optimizar"
    if (resource.element && resource.element.getAttribute && resource.element.getAttribute('data-no-optimize') === 'true') {
      return;
    }

    // Si el recurso no ha sido accedido recientemente o ya no está visible
    if (now - resource.lastAccessed > config.resourceCleanupInterval || !resource.inViewport) {
      deleteKeys.push(key);
    }
  });
  
  // Liberar recursos
  deleteKeys.forEach(key => {
    const resource = loadedResources.get(key);
    
    // Si es un video, liberar los recursos del video
    if (resource.element && resource.element.tagName === 'VIDEO') {
      resource.element.pause();
      resource.element.src = '';
      resource.element.load();
    }
    
    // Si es un objeto URL, revocarlo
    if (resource.objectUrl) {
      URL.revokeObjectURL(resource.objectUrl);
    }
    
    console.log(`Recurso liberado: ${key}`);
    loadedResources.delete(key);
  });
};

/**
 * Detecta si un formato de archivo es una imagen
 */
const isImageFormat = (url) => {
  const lowercasedUrl = url.toLowerCase();
  return config.imageFormats.some(format => lowercasedUrl.endsWith(format));
};

/**
 * Detecta si un formato de archivo es un video
 */
const isVideoFormat = (url) => {
  const lowercasedUrl = url.toLowerCase();
  return config.videoFormats.some(format => lowercasedUrl.endsWith(format));
};

/**
 * Inicializa el observador de recursos
 */
const initResourceObserver = () => {
  // Configurar Intersection Observer para detectar elementos visibles
  resourceObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const element = entry.target;

      // Ignorar elementos marcados como no optimizables
      if (element.getAttribute && element.getAttribute('data-no-optimize') === 'true') {
        return;
      }

      const src = element.tagName === 'IMG' ? element.getAttribute('src') : 
                element.tagName === 'VIDEO' ? element.getAttribute('src') : null;
      
      if (src) {
        const resource = loadedResources.get(src);
        
        if (resource) {
          // Actualizar estado de visibilidad
          resource.inViewport = entry.isIntersecting;
          resource.lastAccessed = Date.now();
        } else if (entry.isIntersecting) {
          // Registrar nuevo recurso visible
          loadedResources.set(src, {
            element,
            inViewport: true,
            lastAccessed: Date.now(),
            objectUrl: null
          });
        }
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px 200px 0px'
  });
  
  // Observar imágenes y videos existentes
  setTimeout(() => {
    document.querySelectorAll('img, video').forEach(element => {
      resourceObserver.observe(element);
    });
    
    // Configurar un observer para nuevos elementos que se añadan al DOM
    const bodyObserver = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          // Si el nodo es un elemento DOM con imágenes o videos
          if (node.nodeType === 1) {
            // Buscar imágenes o videos dentro del nodo
            const mediaElements = node.querySelectorAll('img, video');
            mediaElements.forEach(element => {
              resourceObserver.observe(element);
            });
            
            // Comprobar si el propio nodo es una imagen o video
            if (node.tagName === 'IMG' || node.tagName === 'VIDEO') {
              resourceObserver.observe(node);
            }
          }
        });
      });
    });
    
    // Observar cambios en el cuerpo del documento
    bodyObserver.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // Guardar el observador para limpiarlo más tarde
    window.bodyObserver = bodyObserver;
  }, 1000); // Retrasar la observación para asegurar que los componentes estén cargados
};

// Inicializar cuando el componente se monte
onMounted(() => {
  console.log('Inicializando optimizador de medios...');
  
  // Iniciar el observador de recursos
  initResourceObserver();
  
  // Configurar limpieza periódica
  resourceCleanupTimer = setInterval(cleanupUnusedResources, config.resourceCleanupInterval);
  
  // Optimizar carga inicial de imágenes
  setTimeout(() => {
    document.querySelectorAll('img').forEach(img => {
      if (!img.hasAttribute('loading')) {
        img.setAttribute('loading', 'lazy');
      }
      if (!img.hasAttribute('decoding')) {
        img.setAttribute('decoding', 'async');
      }
    });
    
    // Optimizar videos
    document.querySelectorAll('video').forEach(video => {
      if (!video.hasAttribute('preload')) {
        video.setAttribute('preload', 'metadata');
      }
    });
  }, 500);
});

// Limpiar recursos cuando el componente se desmonte
onBeforeUnmount(() => {
  console.log('Limpiando optimizador de medios...');
  
  // Detener el timer de limpieza
  if (resourceCleanupTimer) {
    clearInterval(resourceCleanupTimer);
  }
  
  // Desconectar observadores
  if (resourceObserver) {
    resourceObserver.disconnect();
  }
  
  if (window.bodyObserver) {
    window.bodyObserver.disconnect();
    delete window.bodyObserver;
  }
  
  // Liberar todos los recursos
  loadedResources.forEach((resource, key) => {
    if (resource.element && resource.element.tagName === 'VIDEO') {
      resource.element.pause();
      resource.element.src = '';
      resource.element.load();
    }
    
    if (resource.objectUrl) {
      URL.revokeObjectURL(resource.objectUrl);
    }
  });
  
  loadedResources.clear();
});
</script> 