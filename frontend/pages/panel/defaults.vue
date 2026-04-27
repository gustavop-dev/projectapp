<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-text-default">Valores por Defecto</h1>
        <p class="text-sm text-text-muted mt-1">
          Configura los valores iniciales que se aplicarán a las nuevas propuestas o diagnósticos.
        </p>
      </div>
      <NuxtLink
        :to="backLink.to"
        class="inline-flex items-center gap-2 px-4 py-2 text-sm text-text-muted hover:text-text-default transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        {{ backLink.label }}
      </NuxtLink>
    </div>

    <!-- Mode switch: Proposal / Diagnostic -->
    <div class="mb-6 flex items-center gap-3 flex-wrap" data-testid="defaults-mode-switch">
      <span class="text-xs font-medium text-text-muted uppercase tracking-wider">Modo:</span>
      <div class="inline-flex rounded-lg p-0.5 bg-surface-raised">
        <button
          v-for="opt in modeOptions"
          :key="opt.value"
          type="button"
          :class="['px-3 py-1.5 text-xs font-medium rounded-md transition-all',
            mode === opt.value
              ? 'bg-surface text-text-brand shadow-sm'
              : 'text-text-muted hover:text-text-default']"
          :data-testid="`defaults-mode-${opt.value}`"
          @click="setMode(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <ProposalDefaultsPanel v-if="mode === 'proposal'" />
    <DiagnosticDefaultsPanel v-else />
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue';

const ProposalDefaultsPanel = defineAsyncComponent(
  () => import('~/components/panel/defaults/ProposalDefaultsPanel.vue'),
);
const DiagnosticDefaultsPanel = defineAsyncComponent(
  () => import('~/components/panel/defaults/DiagnosticDefaultsPanel.vue'),
);

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();

const modeOptions = [
  { value: 'proposal', label: 'Propuesta' },
  { value: 'diagnostic', label: 'Diagnóstico' },
];

const mode = computed(() => (route.query.mode === 'diagnostic' ? 'diagnostic' : 'proposal'));

function setMode(next) {
  if (next === mode.value) return;
  router.replace({ query: { ...route.query, mode: next, tab: undefined } });
}

const backLink = computed(() => (
  mode.value === 'diagnostic'
    ? { to: localePath('/panel/diagnostics'), label: 'Volver a Diagnósticos' }
    : { to: localePath('/panel/proposals'), label: 'Volver a Propuestas' }
));
</script>
