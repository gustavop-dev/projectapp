<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="video-modal-overlay fixed inset-0 z-[100] flex items-center justify-center bg-black/90 p-4"
        @click.self="closeModal"
      >
        <div class="video-modal-container relative w-full max-w-5xl">
          <!-- Close button -->
          <button
            @click="closeModal"
            class="absolute -top-12 right-0 text-white hover:text-lemon transition-colors z-10"
            aria-label="Close video"
          >
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <!-- Video player -->
          <div class="video-wrapper bg-black rounded-lg overflow-hidden">
            <video
              ref="videoPlayer"
              class="plyr-video w-full"
              playsinline
              controls
            >
              <source :src="videoSrc" type="video/mp4" />
            </video>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import Plyr from 'plyr'
import 'plyr/dist/plyr.css'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  videoSrc: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

const videoPlayer = ref(null)
let player = null

const closeModal = () => {
  if (player) {
    player.pause()
  }
  emit('close')
}

// Handle ESC key
const handleEscape = (e) => {
  if (e.key === 'Escape' && props.isOpen) {
    closeModal()
  }
}

// Initialize Plyr when modal opens
watch(() => props.isOpen, (newVal) => {
  if (newVal && videoPlayer.value && !player) {
    player = new Plyr(videoPlayer.value, {
      controls: [
        'play-large',
        'play',
        'progress',
        'current-time',
        'mute',
        'volume',
        'settings',
        'pip',
        'fullscreen'
      ],
      settings: ['quality', 'speed'],
      quality: {
        default: 1080,
        options: [1080, 720, 480]
      },
      speed: {
        selected: 1,
        options: [0.5, 0.75, 1, 1.25, 1.5, 2]
      }
    })
    
    // Auto play when modal opens
    player.play()
  } else if (!newVal && player) {
    player.pause()
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleEscape)
  if (player) {
    player.destroy()
  }
})
</script>

<style scoped>
/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

/* Plyr custom colors */
:deep(.plyr) {
  --plyr-color-main: #F0FF3D;
}

:deep(.plyr--video) {
  border-radius: 0.5rem;
}

:deep(.plyr__control--overlaid) {
  background: rgba(240, 255, 61, 0.9);
}

:deep(.plyr__control--overlaid:hover) {
  background: #F0FF3D;
}

:deep(.plyr__control:hover) {
  background: rgba(240, 255, 61, 0.1);
}

/* Prevent body scroll when modal is open */
.video-modal-overlay {
  overflow-y: auto;
}
</style>
