<template>
  <Transition name="sticky-bar">
    <div
      v-if="showBar"
      class="proposal-response fixed bottom-0 left-0 right-0 z-40
             bg-white/95 backdrop-blur-sm border-t border-gray-100
             px-6 py-3 shadow-lg"
    >
      <div class="max-w-3xl mx-auto flex items-center justify-between gap-3 sm:gap-4">
        <p v-if="proposal?.total_investment" class="text-xs font-bold text-emerald-700 hidden sm:block whitespace-nowrap">
          {{ formatCurrency(proposal.total_investment) }} {{ proposal.currency }}
        </p>
        <p class="text-xs text-gray-400 hidden md:block">
          {{ t.question }}
        </p>
        <div class="ml-auto flex items-center gap-2">
          <!-- Secondary: options menu (negotiate/WhatsApp) -->
          <div v-if="!submitted" class="relative">
            <button
              class="px-4 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium
                     hover:bg-gray-200 transition-colors flex items-center gap-1.5 whitespace-nowrap"
              @click="showOptionsMenu = !showOptionsMenu"
            >
              💬 {{ t.optionsBtn }}
              <svg class="w-3 h-3 transition-transform" :class="showOptionsMenu ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <Transition name="options-menu">
              <div v-if="showOptionsMenu" class="absolute bottom-full right-0 mb-2 bg-white rounded-xl shadow-lg border border-gray-100 py-2 min-w-[200px] z-50">
                <button
                  class="w-full px-4 py-2.5 text-left text-sm text-amber-700 hover:bg-amber-50 transition-colors flex items-center gap-2"
                  @click="$emit('negotiate'); showOptionsMenu = false"
                >
                  🤝 {{ t.negotiateBtn }}
                </button>
                <a
                  v-if="whatsappUrl"
                  :href="whatsappUrl"
                  target="_blank"
                  class="w-full px-4 py-2.5 text-left text-sm text-green-700 hover:bg-green-50 transition-colors flex items-center gap-2"
                  @click="showOptionsMenu = false"
                >
                  📞 {{ t.questionsBtn }}
                </a>
                <button
                  class="w-full px-4 py-2.5 text-left text-sm text-gray-400 hover:bg-gray-50 transition-colors flex items-center gap-2"
                  @click="$emit('reject'); showOptionsMenu = false"
                >
                  {{ t.rejectBtn }}
                </button>
              </div>
            </Transition>
          </div>
          <!-- Primary: Accept -->
          <button
            v-if="!submitted"
            class="px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                   hover:bg-emerald-700 transition-colors shadow-sm flex items-center gap-2 whitespace-nowrap"
            :disabled="isSubmitting"
            @click="showAcceptConfirm = true"
          >
            <span>✅</span> {{ t.acceptBtn }}
          </button>
          <p v-else class="text-sm font-medium text-emerald-600 whitespace-nowrap">
            ✅ {{ t.accepted }}
          </p>
        </div>
      </div>
    </div>
  </Transition>

  <!-- Accept confirmation modal -->
  <teleport to="body">
    <div v-if="showAcceptConfirm" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showAcceptConfirm = false">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-8 text-center">
        <div class="text-5xl mb-4">🎉</div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">{{ t.confirmTitle }}</h3>
        <p class="text-gray-600 text-sm mb-6">{{ t.confirmText }}</p>
        <div class="flex gap-3 justify-center">
          <button
            class="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors"
            :disabled="isSubmitting"
            @click="confirmAccept"
          >{{ isSubmitting ? t.sending : t.confirmYes }}</button>
          <button class="px-6 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showAcceptConfirm = false">{{ t.cancel }}</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  proposal: { type: Object, default: null },
  visible: { type: Boolean, default: false },
  language: { type: String, default: 'es' },
  whatsappLink: { type: String, default: '' },
  proposalTitle: { type: String, default: '' },
  currentSectionTitle: { type: String, default: '' },
});

const whatsappUrl = computed(() => {
  if (props.whatsappLink) return props.whatsappLink;
  if (!props.proposalTitle) return '';
  let msg;
  if (props.language === 'en') {
    const sectionPart = props.currentSectionTitle
      ? ` and I have a question about "${props.currentSectionTitle}".`
      : ' and I have some questions...';
    msg = encodeURIComponent(
      `Hi, I'm reviewing the proposal "${props.proposalTitle}"${sectionPart}`
    );
  } else {
    const sectionPart = props.currentSectionTitle
      ? ` y tengo una pregunta sobre "${props.currentSectionTitle}".`
      : ' y tengo algunas preguntas...';
    msg = encodeURIComponent(
      `Hola, estoy revisando la propuesta "${props.proposalTitle}"${sectionPart}`
    );
  }
  return `https://wa.me/573238122373?text=${msg}`;
});

function formatCurrency(value) {
  if (!value) return '';
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return '$' + num.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

const i18nStrings = {
  es: {
    question: '¿Te convenció la propuesta?',
    acceptBtn: 'Acepto',
    questionsBtn: 'Hablar por WhatsApp',
    optionsBtn: 'Tengo dudas',
    negotiateBtn: 'Necesito ajustes',
    rejectBtn: 'No es el momento',
    accepted: '¡Propuesta aceptada!',
    confirmTitle: '¿Confirmar aceptación?',
    confirmText: 'Al aceptar, recibirás un email de confirmación con los próximos pasos.',
    confirmYes: 'Sí, acepto',
    cancel: 'Cancelar',
    sending: 'Enviando...',
  },
  en: {
    question: 'Convinced by the proposal?',
    acceptBtn: 'Accept',
    questionsBtn: 'Talk on WhatsApp',
    optionsBtn: 'I have questions',
    negotiateBtn: 'I need adjustments',
    rejectBtn: 'Not the right time',
    accepted: 'Proposal accepted!',
    confirmTitle: 'Confirm acceptance?',
    confirmText: 'By accepting, you will receive a confirmation email with the next steps.',
    confirmYes: 'Yes, I accept',
    cancel: 'Cancel',
    sending: 'Sending...',
  },
};

const t = computed(() => i18nStrings[props.language] || i18nStrings.es);

const proposalStore = useProposalStore();

const canRespond = computed(() => {
  const s = props.proposal?.status;
  return s === 'sent' || s === 'viewed';
});

const emit = defineEmits(['negotiate', 'reject']);

const isSubmitting = ref(false);
const submitted = ref(false);
const showAcceptConfirm = ref(false);
const showOptionsMenu = ref(false);

const showBar = computed(() => props.visible && canRespond.value && !submitted.value);

async function confirmAccept() {
  if (!props.proposal?.uuid) return;
  isSubmitting.value = true;
  try {
    const result = await proposalStore.respondToProposal(
      props.proposal.uuid, 'accepted',
    );
    if (result.success) {
      submitted.value = true;
      showAcceptConfirm.value = false;
    }
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.sticky-bar-enter-active,
.sticky-bar-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.sticky-bar-enter-from,
.sticky-bar-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

.options-menu-enter-active,
.options-menu-leave-active {
  transition: all 0.2s ease;
}
.options-menu-enter-from,
.options-menu-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
