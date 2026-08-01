<template>
  <!--
    An ARIA grid of divs rather than a <table>: sortablejs cannot reliably drag
    a <tr>, because the clone it drags is detached from the table and collapses
    to zero width. Roles keep the semantics a table would have given us.
  -->
  <div
    class="overflow-x-auto bg-surface rounded-xl border border-border-muted shadow-sm"
    role="table"
    :aria-busy="loading ? 'true' : undefined"
    aria-label="Pagos recurrentes por categoría"
  >
    <p class="sr-only" aria-live="polite">
      {{ loading ? 'Cargando registros...' : `${rowCount} registros en ${groups.length} categorías` }}
    </p>

    <div class="min-w-[1120px]">
      <!-- Header -->
      <div
        role="row"
        class="grid gap-3 items-end bg-surface-raised px-4 py-3 text-xs text-text-muted uppercase tracking-wider leading-tight"
        :style="gridStyle"
      >
        <span v-if="dragEnabled" role="columnheader" class="sr-only">Orden</span>
        <span
          v-for="col in columns"
          :key="col.key"
          role="columnheader"
          :class="alignClass(col)"
        >{{ col.label }}</span>
        <span role="columnheader" class="text-right">Acciones</span>
      </div>

      <!-- Skeleton -->
      <div v-if="loading" class="divide-y divide-border-muted">
        <div
          v-for="n in skeletonRows"
          :key="`skeleton-${n}`"
          class="px-4 py-3.5 bg-surface"
          data-testid="accounting-skeleton-row"
        >
          <div class="h-3 w-32 rounded bg-surface-raised motion-safe:animate-pulse" />
        </div>
      </div>

      <template v-else>
        <div v-for="group in localGroups" :key="group.id" role="rowgroup">
          <!-- Group header -->
          <div
            role="row"
            class="flex items-center justify-between gap-3 bg-surface-raised border-y border-border-muted px-4 py-2.5"
            :data-testid="`recurring-group-${group.id}`"
          >
            <button
              type="button"
              role="columnheader"
              class="inline-flex items-center gap-2 text-sm font-medium text-text-default rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
              :aria-expanded="!isCollapsed(group.id)"
              :aria-controls="`recurring-group-body-${group.id}`"
              :data-testid="`recurring-group-toggle-${group.id}`"
              @click="emit('toggle-group', group.id)"
            >
              <ChevronDownIcon
                class="w-4 h-4 text-text-subtle transition-transform"
                :class="isCollapsed(group.id) ? '-rotate-90' : ''"
              />
              <span>{{ group.name }}</span>
              <span class="text-xs text-text-subtle font-normal">({{ group.rows.length }})</span>
            </button>
            <span class="text-sm tabular-nums text-text-muted whitespace-nowrap">
              <span :data-testid="`recurring-group-total-${group.id}`">
                {{ formatMonthlyCop(group.monthlyCopTotal) }}
              </span>
              <span class="text-xs text-text-subtle"> /mes</span>
            </span>
          </div>

          <!-- Rows -->
          <draggable
            v-show="!isCollapsed(group.id)"
            :id="`recurring-group-body-${group.id}`"
            v-model="group.rows"
            tag="div"
            class="divide-y divide-border-muted"
            item-key="id"
            handle=".recurring-drag-handle"
            ghost-class="opacity-30"
            :group="{ name: 'recurring' }"
            :disabled="!dragEnabled"
            @end="onDragEnd"
          >
            <template #item="{ element: row }">
              <div
                role="row"
                :data-testid="`accounting-row-${row.id}`"
                class="grid gap-3 items-center px-4 py-3 bg-surface hover:bg-surface-raised transition-colors text-sm"
                :class="row.id === highlightId ? 'accounting-row-flash' : ''"
                :style="gridStyle"
              >
                <span v-if="dragEnabled" role="cell">
                  <span
                    class="recurring-drag-handle cursor-grab select-none text-text-subtle"
                    :data-testid="`recurring-drag-handle-${row.id}`"
                    title="Arrastra para reordenar"
                  >⠿</span>
                </span>
                <span
                  v-for="col in columns"
                  :key="col.key"
                  role="cell"
                  class="min-w-0"
                  :class="cellClass(col)"
                >
                  <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                    <template v-if="col.format === 'money'">
                      {{ formatMoney(row[col.key], 'COP') }}
                    </template>
                    <HighlightText
                      v-else-if="highlightQuery"
                      :text="row[col.key] ?? ''"
                      :query="highlightQuery"
                    />
                    <template v-else>{{ row[col.key] }}</template>
                  </slot>
                </span>
                <span role="cell" class="text-right whitespace-nowrap">
                  <button
                    type="button"
                    aria-label="Editar"
                    :data-testid="`accounting-edit-${row.id}`"
                    class="p-2 rounded-lg text-text-subtle hover:text-text-brand hover:bg-primary-soft transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
                    @click.stop="emit('edit', row)"
                  >
                    <PencilSquareIcon class="w-5 h-5" />
                  </button>
                  <button
                    type="button"
                    aria-label="Eliminar"
                    :data-testid="`accounting-delete-${row.id}`"
                    class="p-2 rounded-lg text-text-subtle hover:text-danger-strong hover:bg-danger-soft transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring/50"
                    @click.stop="emit('delete', row)"
                  >
                    <TrashIcon class="w-5 h-5" />
                  </button>
                </span>
              </div>
            </template>
          </draggable>
        </div>

        <!-- Grand total -->
        <div
          role="row"
          class="flex items-center justify-between gap-3 bg-surface-raised border-t-2 border-border-muted px-4 py-3"
        >
          <span role="cell" class="text-xs uppercase tracking-wider text-text-muted">
            Total mensual (COP)
          </span>
          <span
            role="cell"
            class="tabular-nums font-medium text-text-default whitespace-nowrap"
            data-testid="recurring-monthly-grand-total"
          >
            {{ formatMonthlyCop(grandTotal) }}
          </span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import draggable from 'vuedraggable';
import {
  ChevronDownIcon,
  PencilSquareIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline';
import HighlightText from '~/components/ui/HighlightText.vue';
import { formatMoney } from '~/utils/formatMoney';
import { formatMonthlyCop, UNCATEGORIZED_KEY } from '~/utils/recurring';

const props = defineProps({
  /** Same column config shape as AccountingTable ({ key, label, format, align }). */
  columns: { type: Array, required: true },
  /** [{ id, name, rows, monthlyCopTotal }] — already ordered and subtotaled. */
  groups: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  skeletonRows: { type: Number, default: 5 },
  highlightId: { type: [String, Number], default: null },
  highlightQuery: { type: String, default: '' },
  /** Drag handles only render when reordering is meaningful (no active filter). */
  dragEnabled: { type: Boolean, default: false },
  /** Ids of the collapsed groups. */
  collapsedIds: { type: Array, default: () => [] },
});

const emit = defineEmits(['edit', 'delete', 'reorder', 'toggle-group']);

/**
 * Mutable mirror of `groups`: vuedraggable has to own the arrays it reorders.
 * Rebuilt whenever the page pushes new groups, which is also how a failed
 * reorder snaps the row back — the store restores the old order, the prop
 * changes, and the mirror follows.
 */
const localGroups = ref([]);

watch(
  () => props.groups,
  (groups) => {
    localGroups.value = groups.map((group) => ({ ...group, rows: [...group.rows] }));
  },
  { immediate: true, deep: true },
);

/**
 * Header, rows and the drag handle column must line up, so every row shares one
 * track list. Amounts get a floor wide enough to never truncate — a clipped
 * "$1.200.000 …" defeats the point of the table — while the name column takes
 * the remaining slack.
 */
function trackFor(col, index) {
  if (index === 0) return 'minmax(9rem, 1.4fr)';
  if (col.format === 'money' || col.align === 'right') return 'minmax(7.5rem, 1fr)';
  if (col.align === 'center') return '3.5rem';
  return 'minmax(5.5rem, 0.9fr)';
}

const gridStyle = computed(() => ({
  gridTemplateColumns: [
    ...(props.dragEnabled ? ['1.5rem'] : []),
    ...props.columns.map(trackFor),
    '5.5rem',
  ].join(' '),
}));

const rowCount = computed(
  () => props.groups.reduce((total, group) => total + group.rows.length, 0),
);

const grandTotal = computed(
  () => props.groups.reduce((total, group) => total + (group.monthlyCopTotal || 0), 0),
);

function isCollapsed(id) {
  return props.collapsedIds.includes(id);
}

function alignClass(col) {
  const align = col.align || (col.format === 'money' ? 'right' : 'left');
  if (align === 'right') return 'text-right';
  if (align === 'center') return 'text-center';
  return 'text-left';
}

function cellClass(col) {
  const classes = [alignClass(col)];
  // Amounts must never wrap or clip; free text may truncate.
  if (col.format === 'money' || col.align === 'right') {
    classes.push('tabular-nums whitespace-nowrap');
    classes.push(col.format === 'money' ? 'text-text-muted' : 'text-text-default');
  } else {
    classes.push('truncate text-text-default');
  }
  return classes;
}

/**
 * Emit the whole board once, after the drag settles.
 *
 * `end` fires a single time per drag, and by then vuedraggable has already
 * mutated both the source and the target list — so a cross-group move is just
 * another state to read off `localGroups`, with no double emit to dedupe.
 */
function onDragEnd() {
  const items = localGroups.value.flatMap((group) =>
    group.rows.map((row, index) => ({
      id: row.id,
      // The uncategorized bucket is a UI-only group; it maps back to null.
      category: group.id === UNCATEGORIZED_KEY ? null : group.id,
      order: index,
    })),
  );
  emit('reorder', items);
}
</script>

<style scoped>
/* Same feedback flash as AccountingTable for the row just created or edited. */
@keyframes accounting-row-flash {
  0%,
  55% {
    background-color: var(--color-primary-soft);
  }
  100% {
    background-color: transparent;
  }
}
.accounting-row-flash {
  animation: accounting-row-flash 2.5s ease-out;
}
@media (prefers-reduced-motion: reduce) {
  .accounting-row-flash {
    animation: none;
    background-color: var(--color-primary-soft);
  }
}
</style>
