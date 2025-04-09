<template>
  <div ref="imageContainer" class="lazy-image-container" :style="{ height: `${height}px` }">
    <!-- Placeholder mientras la imagen carga -->
    <div v-if="!loaded" class="placeholder" :style="{ height: `${height}px` }">
      <slot name="placeholder">
        <!-- Placeholder predeterminado es un fondo con efecto de pulso -->
        <div class="animate-pulse bg-gray-200 h-full w-full rounded"></div>
      </slot>
    </div>

    <!-- Imagen real (oculta hasta que se carga) -->
    <img
      ref="image"
      :class="['lazy-image', { 'opacity-0': !loaded, 'opacity-100': loaded }]"
      :src="currentSrc"
      :alt="alt"
      :width="width"
      :height="height"
      :style="imgStyle"
      @load="onImageLoaded"
      @error="onImageError"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useIntersectionObserver } from '@/composables/useIntersectionObserver';
import { useAssetCache } from '@/composables/useAssetCache';

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  alt: {
    type: String,
    default: ''
  },
  width: {
    type: [Number, String],
    default: 'auto'
  },
  height: {
    type: [Number, String],
    default: 300 // Altura predeterminada del contenedor
  },
  objectFit: {
    type: String,
    default: 'cover'
  },
  threshold: {
    type: Number,
    default: 0.1
  },
  rootMargin: {
    type: String,
    default: '0px 0px 200px 0px'
  },
  useCache: {
    type: Boolean,
    default: true
  },
  cacheExpiration: {
    type: Number,
    default: 7 * 24 * 60 * 60 * 1000 // 7 días por defecto
  }
});

// Estado para el lazy loading
const loaded = ref(false);
const error = ref(false);
const currentSrc = ref(''); // Inicialmente vacío, para no cargar la imagen
const imageContainer = ref(null);
const image = ref(null);

// Inicializar servicio de caché si está habilitado
const { getAsset } = useAssetCache({
  cacheName: 'images-cache',
  expirationTime: props.cacheExpiration
});

// Estilos computados para la imagen
const imgStyle = computed(() => ({
  objectFit: props.objectFit,
  width: typeof props.width === 'number' ? `${props.width}px` : props.width,
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  transition: 'opacity 0.3s ease-in-out'
}));

// Configura el observador de intersección
const { observe } = useIntersectionObserver({
  threshold: props.threshold,
  rootMargin: props.rootMargin
});

// Cuando la imagen es visible, carga la imagen desde caché o red
const loadImage = async () => {
  try {
    if (props.useCache) {
      // Usar caché si está habilitado
      const response = await getAsset(props.src);
      if (response) {
        const blob = await response.blob();
        currentSrc.value = URL.createObjectURL(blob);
      } else {
        currentSrc.value = props.src;
      }
    } else {
      // Si no usa caché, cargar directamente
      currentSrc.value = props.src;
    }
  } catch (error) {
    console.error('Error loading image:', error);
    currentSrc.value = props.src; // Fallback
  }
};

// Evento cuando la imagen termina de cargar
const onImageLoaded = () => {
  loaded.value = true;
};

// Evento cuando hay un error al cargar la imagen
const onImageError = () => {
  loaded.value = true;
  error.value = true;
  console.error(`Error loading image: ${props.src}`);
};

// Observa cambios en la fuente de la imagen
watch(() => props.src, (newSrc) => {
  if (newSrc && loaded.value) {
    // Si ya está cargado pero cambia la URL, vuelve a cargar
    loaded.value = false;
    error.value = false;
    loadImage();
  }
});

// Cuando el componente se monta, configura el observador
onMounted(() => {
  if (imageContainer.value) {
    observe(imageContainer.value, loadImage, true);
  }
});
</script>

<style scoped>
.lazy-image-container {
  position: relative;
  overflow: hidden;
  width: 100%;
}

.placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1;
}

.lazy-image {
  position: relative;
  z-index: 2;
  width: 100%;
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
}

.opacity-0 {
  opacity: 0;
}

.opacity-100 {
  opacity: 1;
}
</style> 