<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">Tareas</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Tablero Kanban interno del equipo.</p>
      </div>
      <button
        type="button"
        class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
        data-testid="new-task-btn"
        @click="openCreate('todo')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nueva tarea
      </button>
    </div>

    <div v-if="taskStore.isLoading" class="text-center py-12 text-gray-400 text-sm">
      Cargando tablero...
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <TaskColumn
        v-for="col in columns"
        :key="col.status"
        :status="col.status"
        :label="col.label"
        :tasks="taskStore.columns[col.status] || []"
        @add="openCreate(col.status)"
        @edit="openEdit"
        @move="handleMove"
      />
    </div>

    <TaskFormModal
      v-model="showModal"
      :task="editingTask"
      :default-status="defaultStatus"
      :busy="taskStore.isUpdating"
      :assignees="taskStore.assignees"
      @submit="handleSubmit"
      @delete="handleDelete"
    />

    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import TaskColumn from '~/components/Tasks/TaskColumn.vue';
import TaskFormModal from '~/components/Tasks/TaskFormModal.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const taskStore = useTaskStore();
const showModal = ref(false);
const editingTask = ref(null);
const defaultStatus = ref('todo');
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const columns = [
  { status: 'todo', label: 'TO DO' },
  { status: 'in_progress', label: 'In Progress' },
  { status: 'blocked', label: 'Blocked' },
  { status: 'done', label: 'Done' },
];

onMounted(() => {
  Promise.all([taskStore.fetchTasks(), taskStore.fetchAssignees()]);
});

function openCreate(status) {
  editingTask.value = null;
  defaultStatus.value = status || 'todo';
  showModal.value = true;
}

function openEdit(task) {
  editingTask.value = task;
  showModal.value = true;
}

async function handleSubmit(payload) {
  const result = editingTask.value?.id
    ? await taskStore.updateTask(editingTask.value.id, payload)
    : await taskStore.createTask(payload);
  if (result.success) {
    showModal.value = false;
  }
}

async function handleDelete(task) {
  if (!task?.id) return;
  const confirmed = await requestConfirm({
    title: 'Eliminar tarea',
    message: `Se eliminará permanentemente "${task.title}". Esta acción no se puede deshacer.`,
    confirmText: 'Eliminar',
    variant: 'danger',
  });
  if (!confirmed) return;
  const result = await taskStore.deleteTask(task.id);
  if (result.success) showModal.value = false;
}

async function handleMove({ taskId, status, position }) {
  await taskStore.moveTask(taskId, status, position);
}
</script>
