/**
 * Servicio para manejar el cacheo de recursos estáticos
 */
export default class CacheService {
  /**
   * Constructor del servicio de caché
   * @param {String} cacheName - Nombre de la caché
   * @param {Number} expirationTime - Tiempo de expiración en milisegundos (por defecto 7 días)
   */
  constructor(cacheName = 'static-resources', expirationTime = 7 * 24 * 60 * 60 * 1000) {
    this.cacheName = cacheName;
    this.expirationTime = expirationTime;
    this.isSupported = typeof caches !== 'undefined';
  }

  /**
   * Verifica si el caché está disponible en el navegador
   * @returns {Boolean} - True si el caché está disponible
   */
  isCacheAvailable() {
    return this.isSupported;
  }

  /**
   * Guarda un recurso en caché
   * @param {String} url - URL del recurso a cachear
   * @param {Response} response - Respuesta del recurso
   * @returns {Promise<void>}
   */
  async cacheResource(url, response) {
    if (!this.isSupported) return null;

    try {
      const cache = await caches.open(this.cacheName);
      const clonedResponse = response.clone();
      
      // Añade timestamp de expiración en los metadatos
      const metadata = {
        url,
        timestamp: Date.now(),
        expiration: Date.now() + this.expirationTime
      };
      
      // Guardar metadata en localStorage para gestionar expiración
      localStorage.setItem(`cache-metadata-${url}`, JSON.stringify(metadata));
      
      // Guardar el recurso en caché
      await cache.put(url, clonedResponse);
      
      return true;
    } catch (error) {
      console.error('Error caching resource:', error);
      return false;
    }
  }

  /**
   * Obtiene un recurso de caché
   * @param {String} url - URL del recurso
   * @returns {Promise<Response|null>} - Respuesta del recurso o null si no existe
   */
  async getResource(url) {
    if (!this.isSupported) return null;

    try {
      // Verificar si el recurso está expirado
      const metadataJson = localStorage.getItem(`cache-metadata-${url}`);
      if (metadataJson) {
        const metadata = JSON.parse(metadataJson);
        if (metadata.expiration < Date.now()) {
          // Si está expirado, eliminar del caché
          await this.deleteResource(url);
          return null;
        }
      }

      const cache = await caches.open(this.cacheName);
      const cachedResponse = await cache.match(url);
      
      return cachedResponse || null;
    } catch (error) {
      console.error('Error getting cached resource:', error);
      return null;
    }
  }

  /**
   * Elimina un recurso de caché
   * @param {String} url - URL del recurso a eliminar
   * @returns {Promise<Boolean>} - True si se eliminó correctamente
   */
  async deleteResource(url) {
    if (!this.isSupported) return false;

    try {
      const cache = await caches.open(this.cacheName);
      const result = await cache.delete(url);
      localStorage.removeItem(`cache-metadata-${url}`);
      return result;
    } catch (error) {
      console.error('Error deleting cached resource:', error);
      return false;
    }
  }

  /**
   * Limpia todos los recursos expirados
   * @returns {Promise<void>}
   */
  async cleanExpiredResources() {
    if (!this.isSupported) return;

    try {
      // Obtener todas las claves de metadatos
      const keys = Object.keys(localStorage).filter(key => key.startsWith('cache-metadata-'));
      const now = Date.now();
      const cache = await caches.open(this.cacheName);

      for (const key of keys) {
        const metadataJson = localStorage.getItem(key);
        if (metadataJson) {
          const metadata = JSON.parse(metadataJson);
          
          if (metadata.expiration < now) {
            // Eliminar recursos expirados
            await cache.delete(metadata.url);
            localStorage.removeItem(key);
          }
        }
      }
    } catch (error) {
      console.error('Error cleaning expired resources:', error);
    }
  }

  /**
   * Función para precargar una lista de recursos
   * @param {Array<String>} urls - Array de URLs a precargar
   * @returns {Promise<void>}
   */
  async preloadResources(urls) {
    if (!this.isSupported || !urls || !urls.length) return;

    try {
      const cache = await caches.open(this.cacheName);
      
      const fetchPromises = urls.map(async (url) => {
        // Verificar si ya existe en caché y no está expirado
        const metadata = localStorage.getItem(`cache-metadata-${url}`);
        if (metadata) {
          const parsedMetadata = JSON.parse(metadata);
          if (parsedMetadata.expiration > Date.now()) {
            // Si ya existe y no está expirado, no hace falta precargar
            return;
          }
        }
        
        try {
          const response = await fetch(url, { cache: 'reload' });
          if (response.ok) {
            const metadata = {
              url,
              timestamp: Date.now(),
              expiration: Date.now() + this.expirationTime
            };
            
            localStorage.setItem(`cache-metadata-${url}`, JSON.stringify(metadata));
            await cache.put(url, response.clone());
          }
        } catch (err) {
          console.warn(`Failed to preload resource: ${url}`, err);
        }
      });
      
      await Promise.allSettled(fetchPromises);
    } catch (error) {
      console.error('Error preloading resources:', error);
    }
  }
} 