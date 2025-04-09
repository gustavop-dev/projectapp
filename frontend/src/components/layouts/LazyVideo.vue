<template>
  <div ref="videoContainer" class="lazy-video-container" :style="containerStyle">
    <!-- Placeholder mientras el video carga -->
    <div v-if="!loaded" class="placeholder" :style="containerStyle">
      <slot name="placeholder">
        <!-- Placeholder predeterminado es un fondo con efecto de pulso -->
        <div class="animate-pulse bg-gray-200 h-full w-full rounded"></div>
      </slot>
    </div>

    <!-- Video (oculto hasta que se carga) -->
    <video
      ref="video"
      :class="['lazy-video', { 'opacity-0': !loaded, 'opacity-100': loaded }]"
      :autoplay="autoplay"
      :muted="muted"
      :loop="loop"
      :controls="controls"
      :playsinline="playsinline"
      :width="width"
      :height="height"
      :poster="poster"
      :preload="preload"
      @loadeddata="onVideoLoaded"
      @error="onVideoError"
    >
      <source v-if="currentSrc" :src="currentSrc" :type="type" />
      <slot></slot>
    </video>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useIntersectionObserver } from '@/composables/useIntersectionObserver';
import { useAssetCache } from '@/composables/useAssetCache';

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'video/mp4'
  },
  autoplay: {
    type: Boolean,
    default: false
  },
  muted: {
    type: Boolean,
    default: true
  },
  loop: {
    type: Boolean,
    default: false
  },
  controls: {
    type: Boolean,
    default: false
  },
  playsinline: {
    type: Boolean,
    default: true
  },
  width: {
    type: [Number, String],
    default: '100%'
  },
  height: {
    type: [Number, String],
    default: 'auto'
  },
  objectFit: {
    type: String,
    default: 'cover'
  },
  poster: {
    type: String,
    default: ''
  },
  preload: {
    type: String,
    default: 'metadata' // 'none', 'metadata', 'auto'
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
    default: 30 * 24 * 60 * 60 * 1000 // 30 días por defecto para videos
  }
});

// Emitir eventos
const emit = defineEmits(['loaded', 'error']);

// Estado para el lazy loading
const loaded = ref(false);
const error = ref(false);
const currentSrc = ref(''); // Inicialmente vacío, para no cargar el video
const videoContainer = ref(null);
const video = ref(null);
const objectUrl = ref(null); // Para mantener referencia y liberar memoria

// Inicializar servicio de caché si está habilitado
const { getAsset } = useAssetCache({
  cacheName: 'videos-cache',
  expirationTime: props.cacheExpiration
});

// Estilos computados para el contenedor
const containerStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  width: typeof props.width === 'number' ? `${props.width}px` : props.width,
}));

// Configura el observador de intersección
const { observe, unobserve } = useIntersectionObserver({
  threshold: props.threshold,
  rootMargin: props.rootMargin
});

// Cuando el video es visible, carga el video desde caché o red
const loadVideo = async () => {
  try {
    if (props.useCache) {
      // Usar caché si está habilitado
      const response = await getAsset(props.src);
      if (response) {
        const blob = await response.blob();
        
        // Liberar URL anterior si existe
        if (objectUrl.value) {
          URL.revokeObjectURL(objectUrl.value);
        }
        
        // Crear nuevo objectURL desde el blob
        objectUrl.value = URL.createObjectURL(blob);
        currentSrc.value = objectUrl.value;
      } else {
        currentSrc.value = props.src;
      }
    } else {
      // Si no usa caché, cargar directamente
      currentSrc.value = props.src;
    }
  } catch (error) {
    console.error('Error loading video:', error);
    currentSrc.value = props.src; // Fallback
  }
};

// Evento cuando el video termina de cargar
const onVideoLoaded = () => {
  loaded.value = true;
  emit('loaded', video.value);
};

// Evento cuando hay un error al cargar el video
const onVideoError = (e) => {
  loaded.value = false;
  error.value = true;
  console.error(`Error loading video: ${props.src}`, e);
  emit('error', e);
};

// Exponer métodos del video
defineExpose({
  play: () => video.value?.play(),
  pause: () => video.value?.pause(),
  stop: () => {
    if (video.value) {
      video.value.pause();
      video.value.currentTime = 0;
    }
  },
  // Más métodos según necesites
});

// Observa cambios en la fuente del video
watch(() => props.src, (newSrc) => {
  if (newSrc && loaded.value) {
    // Si ya está cargado pero cambia la URL, vuelve a cargar
    loaded.value = false;
    error.value = false;
    loadVideo();
  }
});

// Cuando el componente se monta, configura el observador
onMounted(() => {
  if (videoContainer.value) {
    observe(videoContainer.value, loadVideo, true);
  }
});

// Liberar recursos al desmontar
onUnmounted(() => {
  if (videoContainer.value) {
    unobserve(videoContainer.value);
  }
  
  if (video.value) {
    video.value.src = '';
    video.value.load();
  }
  
  // Liberar ObjectURL si existe
  if (objectUrl.value) {
    URL.revokeObjectURL(objectUrl.value);
    objectUrl.value = null;
  }
});
</script>

<style scoped>
.lazy-video-container {
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

.lazy-video {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  object-fit: v-bind('objectFit');
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