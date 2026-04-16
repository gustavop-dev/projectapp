<template>
  <div
    class="group bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-sm hover:shadow-md cursor-pointer transition-all"
    data-testid="task-card"
  >
    <div class="flex items-start justify-between gap-2 mb-2">
      <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-2 flex-1">
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
      class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-2"
    >
      {{ task.description }}
    </p>

    <div class="flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400">
      <span v-if="task.assignee_name" class="truncate" :title="task.assignee_email || ''">
        👤 {{ task.assignee_name }}
      </span>
      <span v-else class="text-gray-300 dark:text-gray-600">Unassigned</span>

      <span
        v-if="task.due_date"
        :class="task.is_overdue ? 'text-red-600 dark:text-red-400 font-semibold' : ''"
      >
        📅 {{ formatDate(task.due_date) }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  task: { type: Object, required: true },
});

const priorityLabel = computed(() => {
  const map = { low: 'Low', medium: 'Medium', high: 'High' };
  return map[props.task.priority] || props.task.priority;
});

const priorityBadgeClass = computed(() => {
  const map = {
    low: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
    medium: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    high: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  };
  return map[props.task.priority] || map.medium;
});

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(`${dateStr}T00:00:00`);
  return d.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
}
</script>
