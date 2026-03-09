<template>
  <div class="share-proposal">
    <!-- Quick-copy toast -->
    <Transition name="fade-toast">
      <div v-if="quickCopied" class="fixed bottom-[5.5rem] right-4 z-40 bg-emerald-600 text-white text-xs font-medium px-4 py-2 rounded-xl shadow-lg whitespace-nowrap">
        {{ t.copied }} ✅
      </div>
    </Transition>

    <!-- Floating share button: click = copy link, long-press = open modal -->
    <button
      data-testid="share-proposal-btn"
      class="fixed bottom-20 right-4 z-30 w-11 h-11 bg-white border border-gray-200
             rounded-full shadow-lg flex items-center justify-center
             hover:bg-gray-50 transition-colors group"
      :title="t.shareTitle"
      @click="quickCopyLink"
      @contextmenu.prevent="showModal = true"
    >
      <svg class="w-5 h-5 text-gray-500 group-hover:text-emerald-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
      </svg>
    </button>

    <!-- Share modal -->
    <teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="showModal = false"
      >
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-5 sm:p-8">
          <!-- Step 1: Enter info -->
          <template v-if="!shareResult">
            <div class="text-center mb-6">
              <div class="w-14 h-14 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <svg class="w-7 h-7 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
              </div>
              <h3 class="text-xl font-bold text-gray-900 mb-1">{{ t.shareTitle }}</h3>
              <p class="text-sm text-gray-500">{{ t.shareSubtitle }}</p>
            </div>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t.nameLabel }} *</label>
                <input
                  v-model="shareName"
                  type="text"
                  :placeholder="t.namePlaceholder"
                  class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                         focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">{{ t.emailLabel }}</label>
                <input
                  v-model="shareEmail"
                  type="email"
                  :placeholder="t.emailPlaceholder"
                  class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                         focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>
            </div>

            <div class="flex gap-3 justify-end mt-6">
              <button
                class="px-5 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium
                       hover:bg-gray-200 transition-colors"
                @click="showModal = false"
              >{{ t.cancel }}</button>
              <button
                class="px-5 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium
                       hover:bg-emerald-700 transition-colors"
                :disabled="isSharing || !shareName.trim()"
                @click="createShareLink"
              >{{ isSharing ? t.creating : t.createLink }}</button>
            </div>
          </template>

          <!-- Step 2: Show share link -->
          <template v-else>
            <div class="text-center mb-6">
              <div class="text-5xl mb-3">🔗</div>
              <h3 class="text-xl font-bold text-gray-900 mb-1">{{ t.linkReady }}</h3>
              <p class="text-sm text-gray-500">{{ t.linkReadySub }}</p>
            </div>

            <div class="bg-gray-50 border border-gray-200 rounded-xl p-4 flex items-center gap-3">
              <input
                ref="linkInput"
                type="text"
                :value="shareUrl"
                readonly
                class="flex-1 bg-transparent text-sm text-gray-700 outline-none truncate"
              />
              <button
                class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-medium
                       hover:bg-emerald-700 transition-colors whitespace-nowrap"
                @click="copyLink"
              >{{ copied ? t.copied : t.copy }}</button>
            </div>

            <div class="flex justify-center mt-6">
              <button
                class="px-5 py-2 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium
                       hover:bg-gray-200 transition-colors"
                @click="closeAndReset"
              >{{ t.done }}</button>
            </div>
          </template>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  proposalUuid: { type: String, required: true },
  language: { type: String, default: 'es' },
});

const i18nStrings = {
  es: {
    shareTitle: 'Compartir propuesta',
    shareSubtitle: 'Comparte esta propuesta con tu equipo para que puedan revisarla.',
    nameLabel: 'Tu nombre',
    namePlaceholder: 'Ej: Juan Pérez',
    emailLabel: 'Tu email (opcional)',
    emailPlaceholder: 'juan@empresa.com',
    cancel: 'Cancelar',
    createLink: 'Crear enlace',
    creating: 'Creando...',
    linkReady: '¡Enlace listo!',
    linkReadySub: 'Comparte este enlace con quien quieras que revise la propuesta.',
    copy: 'Copiar',
    copied: '¡Copiado!',
    done: 'Listo',
  },
  en: {
    shareTitle: 'Share proposal',
    shareSubtitle: 'Share this proposal with your team so they can review it.',
    nameLabel: 'Your name',
    namePlaceholder: 'e.g. John Doe',
    emailLabel: 'Your email (optional)',
    emailPlaceholder: 'john@company.com',
    cancel: 'Cancel',
    createLink: 'Create link',
    creating: 'Creating...',
    linkReady: 'Link ready!',
    linkReadySub: 'Share this link with anyone you want to review the proposal.',
    copy: 'Copy',
    copied: 'Copied!',
    done: 'Done',
  },
};

const t = computed(() => i18nStrings[props.language] || i18nStrings.es);

const proposalStore = useProposalStore();

const showModal = ref(false);
const shareName = ref('');
const shareEmail = ref('');
const isSharing = ref(false);
const shareResult = ref(null);
const copied = ref(false);
const linkInput = ref(null);

const quickCopied = ref(false);

const shareUrl = computed(() => {
  if (!shareResult.value?.uuid) return '';
  const base = window.location.origin;
  return `${base}/proposal/shared/${shareResult.value.uuid}`;
});

function quickCopyLink() {
  const url = window.location.href;
  navigator.clipboard.writeText(url).then(() => {
    quickCopied.value = true;
    setTimeout(() => { quickCopied.value = false; }, 2000);
  });
  // Track analytics
  proposalStore.trackProposalEvent?.(props.proposalUuid, 'share_link_copied');
}

async function createShareLink() {
  if (!shareName.value.trim()) return;
  isSharing.value = true;
  try {
    const result = await proposalStore.shareProposal(props.proposalUuid, {
      name: shareName.value.trim(),
      email: shareEmail.value.trim(),
    });
    if (result.success) {
      shareResult.value = result.data;
    }
  } finally {
    isSharing.value = false;
  }
}

function copyLink() {
  if (shareUrl.value) {
    navigator.clipboard.writeText(shareUrl.value);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  }
}

function closeAndReset() {
  showModal.value = false;
  shareResult.value = null;
  shareName.value = '';
  shareEmail.value = '';
  copied.value = false;
}
</script>
