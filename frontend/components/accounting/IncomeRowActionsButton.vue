<script setup>
import { ArrowPathIcon, EllipsisVerticalIcon } from '@heroicons/vue/24/outline';
import BaseButton from '~/components/base/BaseButton.vue';

/**
 * The kebab that opens an income's action menu.
 *
 * Extracted because the grouped and the classic table each render one: the
 * two copies were identical and had to be kept in step by hand, which is the
 * same drift that had already cost the classic table its mute action.
 *
 * `busy` covers the one action that cannot act on the spot. Duplicating has
 * to fetch its prefill first and the menu closes on click, so without a mark
 * here the row sits silent until the form appears.
 */
defineProps({
  row: { type: Object, required: true },
  busy: { type: Boolean, default: false },
});

const emit = defineEmits(['open']);
</script>

<template>
  <div class="flex items-center justify-end">
    <BaseButton
      variant="ghost"
      icon-only
      size="sm"
      :aria-label="busy ? 'Preparando duplicado' : 'Acciones'"
      :title="busy ? 'Preparando duplicado' : 'Acciones'"
      :disabled="busy"
      :data-testid="`income-actions-${row.id}`"
      @click.stop="emit('open', row)"
    >
      <ArrowPathIcon v-if="busy" class="w-5 h-5 animate-spin" />
      <EllipsisVerticalIcon v-else class="w-5 h-5" />
    </BaseButton>
  </div>
</template>
