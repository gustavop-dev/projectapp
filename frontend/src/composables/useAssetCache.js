import { ref, onMounted } from 'vue';
import CacheService from '@/service/CacheService';

/**
 * Composable para utilizar el servicio de caché de recursos estáticos
 * 
 * @param {Object} options - Opciones de configuración
 * @param {String} options.cacheName - Nombre de la caché (por defecto: 'static-resources')
 * @param {Number} options.expirationTime - Tiempo de expiración en milisegundos
 * @param {Array<String>} options.preloadAssets - Lista de recursos a precargar
 * @returns {Object} - Métodos y propiedades del servicio de caché
 */
export function useAssetCache(options = {}) {
  const cacheService = ref(null);
  const preloadStatus = ref('idle');
  const preloadProgress = ref(0);
  const preloadedAssets = ref([]);
  const failedAssets = ref([]);
  
  // Inicializar el servicio de caché
  onMounted(() => {
    const { cacheName, expirationTime } = options;
    cacheService.value = new CacheService(cacheName, expirationTime);
    
    // Limpiar recursos expirados al montar el componente
    cleanExpiredResources();
    
    // Precargar recursos si se especifican
    if (options.preloadAssets && options.preloadAssets.length > 0) {
      preloadAssets(options.preloadAssets);
    }
  });
  
  /**
   * Precarga una lista de recursos
   * @param {Array<String>} assets - Lista de URLs de recursos a precargar
   * @returns {Promise<void>}
   */
  const preloadAssets = async (assets) => {
    if (!cacheService.value || !assets || assets.length === 0) return;
    
    preloadStatus.value = 'loading';
    preloadProgress.value = 0;
    preloadedAssets.value = [];
    failedAssets.value = [];
    
    const total = assets.length;
    let completed = 0;
    
    try {
      const preloadPromises = assets.map(async (url) => {
        try {
          const response = await fetch(url, { cache: 'reload' });
          if (response.ok) {
            await cacheService.value.cacheResource(url, response);
            preloadedAssets.value.push(url);
          } else {
            failedAssets.value.push(url);
          }
        } catch (error) {
          console.error(`Error preloading asset: ${url}`, error);
          failedAssets.value.push(url);
        } finally {
          completed++;
          preloadProgress.value = Math.round((completed / total) * 100);
        }
      });
      
      await Promise.allSettled(preloadPromises);
      preloadStatus.value = 'success';
    } catch (error) {
      console.error('Error in preloadAssets:', error);
      preloadStatus.value = 'error';
    }
  };
  
  /**
   * Obtiene un recurso de la caché o lo busca en la red
   * @param {String} url - URL del recurso
   * @returns {Promise<Response>} - Respuesta del recurso
   */
  const getAsset = async (url) => {
    if (!cacheService.value) return fetch(url);
    
    try {
      // Intentar obtener de la caché
      const cachedResponse = await cacheService.value.getResource(url);
      
      if (cachedResponse) {
        return cachedResponse;
      }
      
      // Si no está en caché, obtener de la red
      const networkResponse = await fetch(url);
      
      // Guardar en caché para futuras solicitudes
      if (networkResponse.ok) {
        await cacheService.value.cacheResource(url, networkResponse.clone());
      }
      
      return networkResponse;
    } catch (error) {
      console.error(`Error getting asset: ${url}`, error);
      // Fallback a la red
      return fetch(url);
    }
  };
  
  /**
   * Limpia los recursos expirados
   */
  const cleanExpiredResources = async () => {
    if (cacheService.value) {
      await cacheService.value.cleanExpiredResources();
    }
  };
  
  return {
    preloadAssets,
    getAsset,
    cleanExpiredResources,
    preloadStatus,
    preloadProgress,
    preloadedAssets,
    failedAssets,
    cacheService
  };
} 