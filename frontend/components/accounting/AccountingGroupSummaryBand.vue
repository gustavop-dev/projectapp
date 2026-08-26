<template>
  <div
    role="row"
    class="accounting-group-summary"
    :class="{ 'accounting-group-summary--with-statuses': statuses.length > 0 }"
  >
    <div class="accounting-group-summary__identity">
      <slot />
    </div>

    <div
      v-for="metric in metrics"
      :key="metric.key"
      role="cell"
      class="accounting-group-summary__metric text-xs leading-tight whitespace-nowrap"
    >
      <span class="block text-[10px] uppercase tracking-wider text-text-subtle">
        {{ metric.label }}
      </span>
      <span
        class="block font-medium tabular-nums"
        :class="metricToneClass(metric.tone)"
        :data-testid="metric.testId"
      >{{ metric.value }}</span>
    </div>

    <dl
      v-if="statuses.length"
      class="accounting-group-summary__statuses flex flex-wrap items-center gap-x-3 gap-y-1"
      aria-label="Desglose por estado"
    >
      <div
        v-for="status in statuses"
        :key="status.key"
        class="inline-flex items-baseline gap-1 text-[11px] whitespace-nowrap"
        :data-testid="status.testId"
      >
        <dt class="text-text-subtle">{{ status.label }}</dt>
        <dd class="font-semibold tabular-nums" :class="statusToneClass(status.tone)">
          {{ status.value }}
        </dd>
      </div>
    </dl>
  </div>
</template>

<script setup>
defineProps({
  metrics: { type: Array, default: () => [] },
  statuses: { type: Array, default: () => [] },
});

const METRIC_TONES = {
  default: 'text-text-default',
  muted: 'text-text-muted',
  warning: 'text-warning-strong',
  success: 'text-success-strong',
  danger: 'text-danger-strong',
};

const STATUS_TONES = {
  default: 'text-text-default',
  muted: 'text-text-muted',
  brand: 'text-text-brand',
  warning: 'text-warning-strong',
  success: 'text-success-strong',
  danger: 'text-danger-strong',
};

function metricToneClass(tone) {
  return METRIC_TONES[tone] || METRIC_TONES.default;
}

function statusToneClass(tone) {
  return STATUS_TONES[tone] || STATUS_TONES.default;
}
</script>

<style scoped>
.accounting-group-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  column-gap: 1.25rem;
  row-gap: 0.25rem;
  width: 0;
  min-width: 100%;
}

.accounting-group-summary__identity {
  min-width: 0;
}

.accounting-group-summary__metric {
  flex: 0 0 auto;
}

.accounting-group-summary__statuses {
  flex: 1 0 100%;
  min-width: 0;
}

@media (max-width: 1023px) {
  .accounting-group-summary {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.5rem 1rem;
    align-items: start;
  }

  .accounting-group-summary__identity,
  .accounting-group-summary__statuses {
    grid-column: 1 / -1;
  }

  .accounting-group-summary__metric:last-of-type:nth-child(4) {
    grid-column: 1 / -1;
  }
}

@media (min-width: 1024px) {
  .accounting-group-summary:not(.accounting-group-summary--with-statuses) {
    flex-wrap: nowrap;
  }

  .accounting-group-summary__identity {
    flex: 0 1 auto;
  }
}
</style>
