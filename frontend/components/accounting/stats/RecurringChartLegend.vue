<template>
  <ul class="divide-y divide-border-muted" data-testid="recurring-chart-legend">
    <li v-for="item in items" :key="item.key">
      <component
        :is="clickable ? 'button' : 'div'"
        :type="clickable ? 'button' : undefined"
        class="w-full flex items-center gap-3 px-2 py-2 text-left rounded-lg"
        :class="[
          clickable ? 'hover:bg-surface-raised focus:outline-none focus:ring-2 focus:ring-focus-ring' : '',
          activeKey === item.key ? 'bg-surface-raised' : '',
        ]"
        :aria-pressed="clickable ? String(activeKey === item.key) : undefined"
        :data-testid="`recurring-chart-legend-item-${item.key}`"
        @click="clickable && emit('select', item.key)"
      >
        <span
          class="shrink-0 w-3 h-3 rounded-sm"
          :style="{ backgroundColor: item.color }"
          aria-hidden="true"
        />
        <span class="flex-1 min-w-0 text-sm text-text-default truncate">{{ item.label }}</span>
        <span
          v-if="item.sub"
          class="hidden sm:block text-xs text-text-muted whitespace-nowrap"
        >{{ item.sub }}</span>
        <span class="text-sm text-text-default tabular-nums whitespace-nowrap">
          {{ formatMonthlyCop(item.total) }}
        </span>
        <span class="w-14 text-right text-xs text-text-muted tabular-nums whitespace-nowrap">
          {{ formatPercent(item.pct) }}
        </span>
      </component>
    </li>
  </ul>
</template>

<script setup>
import { formatPercent } from '~/utils/percent';
import { formatMonthlyCop } from '~/utils/recurring';

/**
 * The legend for the recurring charts — and, deliberately, more than a legend.
 *
 * It is also the table view: every value and share is written out, so nothing
 * is reachable only by hovering a slice. That matters most where the chart
 * cannot help — two of the four categories weigh about 1,4% each, arcs of five
 * degrees where no inline label fits.
 *
 * Identity comes from the swatch beside the text, never from coloring the text
 * itself: the lighter categorical hues are illegible as type on the surface.
 *
 * Items: [{ key, label, total, pct, color, sub? }].
 */
defineProps({
  items: { type: Array, default: () => [] },
  /** Key of the row currently drilled into, if any. */
  activeKey: { type: [String, Number], default: null },
  clickable: { type: Boolean, default: false },
});

const emit = defineEmits(['select']);
</script>
