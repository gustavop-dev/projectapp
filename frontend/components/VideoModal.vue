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

          <!-- Native HTML5 Video player -->
          <div class="video-wrapper bg-black rounded-lg overflow-hidden">
            <video
              ref="videoPlayer"
              :src="videoSrc"
              class="w-full rounded-lg"
              playsinline
              controls
              preload="auto"
            ></video>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'

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

const closeModal = () => {
  if (videoPlayer.value) {
    videoPlayer.value.pause()
    videoPlayer.value.currentTime = 0
  }
  emit('close')
}

// Handle ESC key
const handleEscape = (e) => {
  if (e.key === 'Escape' && props.isOpen) {
    closeModal()
  }
}

// When modal opens, ensure video is ready to play with audio
watch(() => props.isOpen, async (newVal) => {
  if (newVal) {
    await nextTick()
    if (!videoPlayer.value) return
    videoPlayer.value.volume = 1
    videoPlayer.value.muted = false
  } else if (videoPlayer.value) {
    videoPlayer.value.pause()
    videoPlayer.value.currentTime = 0
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleEscape)
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

/* Custom video player styling */
video::-webkit-media-controls-panel {
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
}

/* Prevent body scroll when modal is open */
.video-modal-overlay {
  overflow-y: auto;
}
</style>
