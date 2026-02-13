import { ref, onMounted, onUnmounted } from 'vue';

/**
 * Composable para implementar lazy loading usando Intersection Observer API
 * @param {Object} options - Opciones del Intersection Observer
 * @param {Number} options.threshold - Umbral de visibilidad (0-1)
 * @param {String} options.rootMargin - Margen desde el viewport (ej: '0px 0px 100px 0px')
 * @returns {Object} - Métodos y propiedades para implementar lazy loading
 */
export function useIntersectionObserver(options = {}) {
  const elements = ref(new Map()); // Mapa para almacenar elementos y sus estados
  let observer = null;

  // Opciones por defecto para el Intersection Observer
  const defaultOptions = {
    threshold: 0.1, // 10% de visibilidad como valor predeterminado
    rootMargin: '0px 0px 200px 0px', // Precarga elementos cuando están a 200px de ser visibles
  };

  // Combina opciones por defecto con opciones proporcionadas
  const observerOptions = { ...defaultOptions, ...options };

  // Callback para cuando un elemento es observado
  const handleIntersect = (entries, observer) => {
    entries.forEach(entry => {
      // Obtiene el elemento y su función de callback del mapa
      const element = elements.value.get(entry.target);
      
      if (element && !element.loaded) {
        if (entry.isIntersecting) {
          // Si el elemento es visible, ejecuta la función de callback
          element.callback();
          element.loaded = true;
          
          // Si stopObserving es true, deja de observar el elemento
          if (element.stopObserving) {
            observer.unobserve(entry.target);
            elements.value.delete(entry.target);
          }
        }
      }
    });
  };

  // Método para observar un nuevo elemento
  const observe = (el, callback, stopObserving = true) => {
    if (!el) return;
    
    // Configura el elemento en el mapa
    elements.value.set(el, {
      loaded: false,
      callback,
      stopObserving,
    });
    
    // Comienza a observar el elemento
    if (observer) {
      observer.observe(el);
    }
  };

  // Método para dejar de observar un elemento
  const unobserve = (el) => {
    if (!el || !observer) return;
    
    observer.unobserve(el);
    elements.value.delete(el);
  };

  // Inicializa el Intersection Observer cuando el componente se monta
  onMounted(() => {
    observer = new IntersectionObserver(handleIntersect, observerOptions);
    
    // Observa todos los elementos que se añadieron antes de montar el componente
    elements.value.forEach((value, key) => {
      observer.observe(key);
    });
  });

  // Limpia el Intersection Observer cuando el componente se desmonta
  onUnmounted(() => {
    if (observer) {
      elements.value.forEach((value, key) => {
        observer.unobserve(key);
      });
      observer.disconnect();
      elements.value.clear();
    }
  });

  return {
    observe,
    unobserve,
    elements,
  };
} 