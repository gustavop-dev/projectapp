<template>
  <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
    <div
      v-for="month in months"
      :key="month.period"
      class="bg-surface rounded-xl border border-border-muted shadow-sm p-4"
      :data-testid="`statement-month-${month.period}`"
    >
      <div class="flex items-center justify-between gap-2 mb-2">
        <p class="text-sm font-medium text-text-default capitalize">{{ month.label }}</p>
        <span
          v-if="month.statements.length === 0"
          class="text-[10px] px-2 py-0.5 rounded-full font-medium bg-surface-raised text-text-subtle"
        >
          Pendiente
        </span>
      </div>
      <div v-if="month.statements.length" class="space-y-1.5">
        <button
          v-for="statement in month.statements"
          :key="statement.id"
          type="button"
          class="w-full flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-lg text-left transition-colors border"
          :class="statement.id === selectedId
            ? 'border-primary bg-primary-soft'
            : 'border-border-muted hover:bg-surface-raised'"
          :data-testid="`statement-chip-${statement.id}`"
          @click="$emit('select', statement.id)"
        >
          <span class="text-xs text-text-default truncate">{{ statement.card_name }}</span>
          <span
            class="text-[10px] px-2 py-0.5 rounded-full font-medium flex-shrink-0"
            :class="statement.status === 'processed'
              ? 'bg-success-soft text-success-strong'
              : 'bg-warning-soft text-warning-strong'"
          >
            {{ statement.status_label }}
          </span>
        </button>
      </div>
      <p v-else class="text-xs text-text-subtle">Sin extracto procesado.</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  months: { type: Array, required: true },
  selectedId: { type: Number, default: null },
});

defineEmits(['select']);
</script>
