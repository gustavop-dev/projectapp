<template>
  <div class="share-diagnostic">
    <button
      data-testid="share-diagnostic-btn"
      class="share-btn fixed bottom-[8.5rem] right-4 z-40 w-12 h-12 bg-white border border-esmerald/15
             rounded-full shadow-lg flex items-center justify-center
             hover:bg-esmerald/5 transition-colors group"
      :title="t.shareTitle"
      @click="showModal = true"
    >
      <svg class="w-5 h-5 text-esmerald/70 group-hover:text-esmerald transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
      </svg>
    </button>

    <teleport to="body">
      <Transition name="share-modal">
        <div
          v-if="showModal"
          class="fixed inset-0 z-[9990] flex items-end sm:items-center justify-center bg-black/40 backdrop-blur-sm"
          @click.self="closeModal"
        >
          <div class="share-modal-card bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl w-full sm:max-w-md sm:mx-4 p-6 sm:p-8">
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-esmerald/5 rounded-xl flex items-center justify-center">
                  <svg class="w-5 h-5 text-esmerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                  </svg>
                </div>
                <div>
                  <h3 class="text-lg font-bold text-esmerald">{{ t.shareTitle }}</h3>
                  <p class="text-xs text-esmerald/50">{{ t.shareSubtitle }}</p>
                </div>
              </div>
              <button
                class="w-8 h-8 rounded-full bg-esmerald/5 flex items-center justify-center text-esmerald/50 hover:text-esmerald hover:bg-esmerald/10 transition-colors"
                @click="closeModal"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div class="bg-bone/60 border border-esmerald/10 rounded-xl p-3 sm:p-4 flex items-center gap-3 mb-4">
              <div class="flex-1 min-w-0">
                <p class="text-[11px] text-esmerald/55 mb-0.5 font-medium uppercase tracking-wider">{{ t.linkLabel }}</p>
                <p class="text-sm text-esmerald/80 truncate">{{ currentUrl }}</p>
              </div>
              <button
                class="flex-shrink-0 px-4 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap"
                :class="copied
                  ? 'bg-esmerald/10 text-esmerald'
                  : 'bg-esmerald text-lemon hover:bg-esmerald-dark'"
                @click="copyLink"
              >
                <span v-if="copied" class="flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                  </svg>
                  {{ t.copied }}
                </span>
                <span v-else class="flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  {{ t.copyLink }}
                </span>
              </button>
            </div>

            <button
              v-if="canNativeShare"
              class="w-full flex items-center justify-center gap-2.5 px-4 py-3.5 bg-esmerald text-lemon rounded-xl font-medium text-sm hover:bg-esmerald-dark transition-colors shadow-sm"
              @click="nativeShare"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              {{ t.shareViaApps }}
            </button>

            <p v-else class="text-center text-xs text-esmerald/50 mt-2">
              {{ t.copyHint }}
            </p>
          </div>
        </div>
      </Transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const props = defineProps({
  diagnosticUuid: { type: String, required: true },
  language: { type: String, default: 'es' },
});

const i18nStrings = {
  es: {
    shareTitle: 'Compartir diagnóstico',
    shareSubtitle: 'Envía este diagnóstico a tu equipo',
    linkLabel: 'Enlace',
    copyLink: 'Copiar enlace',
    copied: '¡Copiado!',
    shareViaApps: 'Compartir vía apps',
    copyHint: 'Copia el enlace y compártelo por tu medio favorito',
  },
  en: {
    shareTitle: 'Share diagnostic',
    shareSubtitle: 'Send this diagnostic to your team',
    linkLabel: 'Link',
    copyLink: 'Copy link',
    copied: 'Copied!',
    shareViaApps: 'Share via apps',
    copyHint: 'Copy the link and share it through your preferred channel',
  },
};

const t = computed(() => i18nStrings[props.language] || i18nStrings.es);

const showModal = ref(false);
const copied = ref(false);
const currentUrl = ref('');
const canNativeShare = ref(false);

onMounted(() => {
  currentUrl.value = window.location.href;
  canNativeShare.value = !!navigator?.share;
});

function copyLink() {
  navigator.clipboard.writeText(currentUrl.value).then(() => {
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2500);
  });
}

function nativeShare() {
  navigator.share({
    title: document.title || '',
    url: currentUrl.value,
  }).catch(() => { /* user cancelled */ });
}

function closeModal() {
  showModal.value = false;
  copied.value = false;
}
</script>

<style scoped>
.share-modal-enter-active {
  transition: opacity 0.25s ease;
}
.share-modal-enter-active .share-modal-card {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.25s ease;
}
.share-modal-leave-active {
  transition: opacity 0.2s ease;
}
.share-modal-leave-active .share-modal-card {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.share-modal-enter-from {
  opacity: 0;
}
.share-modal-enter-from .share-modal-card {
  opacity: 0;
  transform: translateY(20px) scale(0.97);
}
.share-modal-leave-to {
  opacity: 0;
}
.share-modal-leave-to .share-modal-card {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}
</style>
