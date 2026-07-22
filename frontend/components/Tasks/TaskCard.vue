<template>
  <div
    class="group bg-surface border border-border-default rounded-lg p-3 shadow-card hover:shadow-raised cursor-pointer transition-all"
    data-testid="task-card"
  >
    <div class="flex items-start justify-between gap-2 mb-2">
      <h3 class="text-sm font-medium text-text-default line-clamp-2 flex-1">
        {{ task.title }}
      </h3>
      <span
        class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide flex-shrink-0"
        :class="priorityBadgeClass"
      >
        {{ priorityLabel }}
      </span>
    </div>

    <p
      v-if="task.description"
      class="text-xs text-text-muted line-clamp-2 mb-2"
    >
      {{ task.description }}
    </p>

    <div class="flex items-center justify-between text-[11px] text-text-muted">
      <span v-if="task.assignee_name" class="truncate" :title="task.assignee_email || ''">
        👤 {{ task.assignee_name }}
      </span>
      <span v-else class="text-text-subtle">Unassigned</span>

      <span
        v-if="task.due_date"
        :class="task.is_overdue ? 'text-danger-strong font-semibold' : ''"
      >
        📅 {{ formatDayMonth(task.due_date) }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { formatDayMonth } from '~/utils/formatDate';

const props = defineProps({
  task: { type: Object, required: true },
});

const priorityLabel = computed(() => {
  const map = { low: 'Low', medium: 'Medium', high: 'High' };
  return map[props.task.priority] || props.task.priority;
});

const priorityBadgeClass = computed(() => {
  const map = {
    low: 'bg-surface-raised text-text-muted',
    medium: 'bg-info-soft text-info-strong',
    high: 'bg-danger-soft text-danger-strong',
  };
  return map[props.task.priority] || map.medium;
});
</script>
