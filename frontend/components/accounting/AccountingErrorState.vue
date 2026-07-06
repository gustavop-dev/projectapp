<template>
  <BaseAlert variant="danger" :title="title">
    <p v-if="detail" class="mb-3">{{ detail }}</p>
    <p v-else class="mb-3">
      Revisa tu conexión e intenta de nuevo. Si el problema persiste, contacta al administrador.
    </p>
    <BaseButton
      variant="secondary"
      size="sm"
      :disabled="retrying"
      data-testid="accounting-error-retry"
      @click="emit('retry')"
    >
      <ArrowPathIcon class="w-4 h-4" :class="retrying ? 'motion-safe:animate-spin' : ''" />
      <span>{{ retrying ? 'Reintentando...' : 'Reintentar' }}</span>
    </BaseButton>
  </BaseAlert>
</template>

<script setup>
import { ArrowPathIcon } from '@heroicons/vue/24/outline';
import BaseAlert from '~/components/base/BaseAlert.vue';
import BaseButton from '~/components/base/BaseButton.vue';

defineProps({
  title: { type: String, default: 'No se pudieron cargar los datos' },
  detail: { type: String, default: '' },
  retrying: { type: Boolean, default: false },
});

const emit = defineEmits(['retry']);
</script>
