<template>
  <section class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-white px-6">
    <div class="max-w-lg text-center">
      <div class="w-20 h-20 mx-auto mb-8 rounded-full bg-yellow-100 flex items-center justify-center">
        <svg class="w-10 h-10 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>

      <h1 class="text-3xl md:text-4xl font-light text-text-default mb-4">
        {{ clientName ? `${clientName}, esta` : 'Esta' }} propuesta ha expirado
      </h1>

      <p v-if="formattedExpiredAt" class="text-text-subtle text-sm mb-2">
        Expiró el {{ formattedExpiredAt }}
      </p>

      <p class="text-text-muted text-lg mb-4 leading-relaxed">
        La propuesta <strong v-if="proposalTitle" class="text-text-default">"{{ proposalTitle }}"</strong>
        ya no está vigente.
        <template v-if="sellerName">
          ¿Quieres que <strong class="text-text-default">{{ sellerName }}</strong> te envíe una versión actualizada?
        </template>
        <template v-else>
          Podemos reactivarla o preparar una versión actualizada para ti.
        </template>
      </p>

      <p class="text-text-subtle text-sm mb-10">
        Escríbenos y en menos de 24 horas tendrás una nueva propuesta lista.
      </p>

      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <a
          v-if="whatsappUrl"
          :href="whatsappUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center justify-center gap-2 px-6 py-3
                 bg-primary text-white rounded-xl font-medium
                 hover:bg-primary-strong transition-colors shadow-lg"
        >
          <svg class="w-5 h-5" viewBox="0 0 448 512" fill="currentColor">
            <path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222
              0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1
              c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157" />
          </svg>
          Solicitar versión actualizada
        </a>
        <a
          v-else
          :href="whatsappFallbackUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center justify-center gap-2 px-6 py-3
                 bg-primary text-white rounded-xl font-medium
                 hover:bg-primary-strong transition-colors shadow-lg"
        >
          <svg class="w-5 h-5" viewBox="0 0 448 512" fill="currentColor">
            <path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222
              0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1
              c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157" />
          </svg>
          Solicitar reactivación
        </a>

        <a
          href="mailto:team@projectapp.co"
          class="inline-flex items-center justify-center gap-2 px-6 py-3
                 bg-surface text-text-default rounded-xl font-medium border border-border-default
                 hover:bg-surface-muted transition-colors"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Email
        </a>
      </div>

      <!-- Magic link re-access -->
      <div class="mt-10 pt-8 border-t border-border-muted max-w-sm mx-auto">
        <p class="text-text-subtle text-sm mb-3">¿Perdiste el enlace? Ingresa tu email para recibirlo.</p>
        <form class="flex gap-2" @submit.prevent="handleMagicLink">
          <input
            v-model="magicEmail"
            type="email"
            placeholder="tu@email.com"
            required
            class="flex-1 px-4 py-2.5 border border-border-default rounded-xl text-sm
                   focus:ring-1 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
          />
          <button
            type="submit"
            :disabled="magicLoading"
            class="px-5 py-2.5 bg-gray-900 text-white rounded-xl text-sm font-medium
                   hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            {{ magicLoading ? '...' : 'Enviar' }}
          </button>
        </form>
        <p v-if="magicSent" class="text-text-brand text-xs mt-2">
          Si tenemos propuestas asociadas a ese email, recibirás un enlace en breve.
        </p>
      </div>

      <p class="mt-8 text-xs text-text-subtle">
        Project App. — projectapp.co
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useProposalStore } from '~/stores/proposals';

const props = defineProps({
  proposal: {
    type: Object,
    default: null,
  },
});

const clientName = computed(() => props.proposal?.client_name || '');
const proposalTitle = computed(() => props.proposal?.title || '');
const sellerName = computed(() => props.proposal?.seller_name || '');

const formattedExpiredAt = computed(() => {
  const raw = props.proposal?.expired_at;
  if (!raw) return '';
  try {
    return new Date(raw).toLocaleDateString('es-CO', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
  } catch { return ''; }
});

const whatsappUrl = computed(() => props.proposal?.whatsapp_url || '');

const whatsappFallbackUrl = computed(() => {
  const title = proposalTitle.value;
  const name = clientName.value;
  const greeting = name ? `Hola, soy ${name}. ` : 'Hola. ';
  const msg = title
    ? `${greeting}La propuesta "${title}" expiró y me gustaría reactivarla o recibir una versión actualizada.`
    : `${greeting}Mi propuesta expiró y me gustaría reactivarla o recibir una versión actualizada.`;
  return `https://wa.me/573238122373?text=${encodeURIComponent(msg)}`;
});

const proposalStore = useProposalStore();
const magicEmail = ref('');
const magicLoading = ref(false);
const magicSent = ref(false);

async function handleMagicLink() {
  if (!magicEmail.value) return;
  magicLoading.value = true;
  await proposalStore.requestMagicLink(magicEmail.value);
  magicLoading.value = false;
  magicSent.value = true;
}
</script>
