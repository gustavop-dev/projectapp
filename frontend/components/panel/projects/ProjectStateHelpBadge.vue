<script setup>
import { computed } from 'vue';
import { QuestionMarkCircleIcon } from '@heroicons/vue/24/outline';
import BaseTooltip from '~/components/base/BaseTooltip.vue';

const props = defineProps({
  state: { type: Object, default: null },
  position: { type: String, default: 'top' },
  testId: { type: String, default: '' },
});

const description = computed(() => (
  props.state?.description?.trim()
  || 'Estado administrable del ciclo del proyecto.'
));
const implications = computed(() => (
  props.state?.operational_effect_help?.trim()
  || 'Consulta las consecuencias antes de confirmar un cambio de estado.'
));
const tooltipTestId = computed(() => (
  props.testId || `project-state-help-${props.state?.id ?? 'unknown'}`
));
</script>

<template>
  <BaseTooltip
    v-if="state"
    :position="position"
    width="max-w-sm"
    min-width="min-w-[240px]"
    trigger-class="inline-flex"
  >
    <template #trigger="{ tooltipId }">
      <BaseButton
        unstyled
        icon-only
        type="button"
        class="inline-flex min-h-7 min-w-7 shrink-0 items-center justify-center rounded-full bg-info-soft text-info-strong transition-colors hover:bg-info-strong/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring [@media(pointer:coarse)]:min-h-11 [@media(pointer:coarse)]:min-w-11"
        :aria-label="`Ayuda sobre el estado ${state.name}`"
        :aria-describedby="tooltipId"
        :data-testid="tooltipTestId"
      >
        <QuestionMarkCircleIcon class="h-4 w-4" aria-hidden="true" />
      </BaseButton>
    </template>
    <div class="space-y-2" :data-testid="`${tooltipTestId}-content`">
      <p class="font-semibold">{{ state.name }}</p>
      <p>{{ description }}</p>
      <p><strong>Implica:</strong> {{ implications }}</p>
    </div>
  </BaseTooltip>
</template>
