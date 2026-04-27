<template>
  <section
    class="flex flex-col bg-gray-50/40 rounded-xl border border-border-default min-w-[260px] flex-1"
    :data-testid="`column-${status}`"
  >
    <header class="flex items-center justify-between px-4 py-3 border-b border-border-default">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full" :class="dotClass"></span>
        <h2 class="text-sm font-semibold text-text-default">{{ label }}</h2>
        <span class="text-[11px] text-gray-400 dark:text-text-muted">{{ tasks.length }}</span>
      </div>
      <button
        type="button"
        class="text-gray-400 hover:text-text-brand dark:hover:text-emerald-400 transition-colors"
        :aria-label="`New task in ${label}`"
        :data-testid="`add-task-${status}`"
        @click="$emit('add')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v14M5 12h14" />
        </svg>
      </button>
    </header>

    <div class="flex-1 flex flex-col gap-3 p-3 overflow-y-auto">
      <draggable
        v-if="!tasks.length"
        :model-value="[]"
        :group="{ name: 'tasks' }"
        item-key="id"
        class="min-h-[80px]"
        ghost-class="opacity-30"
        @change="(e) => handleGroupChange(e, 0)"
      >
        <template #item="{}"></template>
      </draggable>

      <div v-for="([name, groupTasks, groupOffset]) in groupedTasks" :key="name">
        <div class="text-[10px] font-semibold uppercase tracking-wide text-gray-400 dark:text-text-muted px-1 mb-1">
          {{ name }}
        </div>
        <draggable
          :model-value="groupTasks"
          :group="{ name: 'tasks' }"
          item-key="id"
          class="flex flex-col gap-2 min-h-[36px]"
          ghost-class="opacity-30"
          @change="(e) => handleGroupChange(e, groupOffset)"
        >
          <template #item="{ element }">
            <TaskCard :task="element" @click="$emit('edit', element)" />
          </template>
        </draggable>
      </div>
    </div>
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

const groupedTasks = computed(() => {
  const sorted = [...props.tasks].sort((a, b) => {
    if (!a.assignee_name && !b.assignee_name) return 0;
    if (!a.assignee_name) return 1;
    if (!b.assignee_name) return -1;
    return a.assignee_name.localeCompare(b.assignee_name);
  });
  const groups = {};
  for (const task of sorted) {
    const key = task.assignee_name || 'Unassigned';
    if (!groups[key]) groups[key] = [];
    groups[key].push(task);
  }
  let offset = 0;
  return Object.entries(groups).map(([name, list]) => {
    const entry = [name, list, offset];
    offset += list.length;
    return entry;
  });
});

function handleGroupChange(evt, offset) {
  if (evt.added) {
    emit('move', {
      taskId: evt.added.element.id,
      status: props.status,
      position: offset + evt.added.newIndex,
    });
  } else if (evt.moved) {
    emit('move', {
      taskId: evt.moved.element.id,
      status: props.status,
      position: offset + evt.moved.newIndex,
    });
  }
}
</script>
