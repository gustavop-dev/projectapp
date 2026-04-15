<template>
  <section
    class="flex flex-col bg-gray-50 dark:bg-gray-900/40 rounded-xl border border-gray-200 dark:border-gray-700 min-w-[280px] max-w-[320px] w-full"
    :data-testid="`column-${status}`"
  >
    <header class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full" :class="dotClass"></span>
        <h2 class="text-sm font-semibold text-gray-800 dark:text-gray-200">{{ label }}</h2>
        <span class="text-[11px] text-gray-400 dark:text-gray-500">{{ tasks.length }}</span>
      </div>
      <button
        type="button"
        class="text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
        :aria-label="`Nueva tarea en ${label}`"
        :data-testid="`add-task-${status}`"
        @click="$emit('add')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v14M5 12h14" />
        </svg>
      </button>
    </header>

    <draggable
      :model-value="tasks"
      :group="{ name: 'tasks' }"
      item-key="id"
      class="flex-1 flex flex-col gap-2 p-3 min-h-[120px]"
      ghost-class="opacity-30"
      @change="handleChange"
    >
      <template #item="{ element }">
        <TaskCard :task="element" @click="$emit('edit', element)" />
      </template>
    </draggable>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import draggable from 'vuedraggable';
import TaskCard from './TaskCard.vue';

const props = defineProps({
  status: { type: String, required: true },
  label: { type: String, required: true },
  tasks: { type: Array, default: () => [] },
});

const emit = defineEmits(['add', 'edit', 'move']);

const dotClass = computed(() => {
  const map = {
    todo: 'bg-gray-400',
    in_progress: 'bg-blue-500',
    blocked: 'bg-red-500',
    done: 'bg-emerald-500',
  };
  return map[props.status] || 'bg-gray-400';
});

function handleChange(evt) {
  if (evt.added) {
    emit('move', {
      taskId: evt.added.element.id,
      status: props.status,
      position: evt.added.newIndex,
    });
  } else if (evt.moved) {
    emit('move', {
      taskId: evt.moved.element.id,
      status: props.status,
      position: evt.moved.newIndex,
    });
  }
}
</script>
