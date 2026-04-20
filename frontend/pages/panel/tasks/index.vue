<template>
  <div>
    <!-- Page header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">Tasks</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Tableros internos del equipo.</p>
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
      Cargando tableros…
    </div>

    <div v-else class="space-y-4">
      <!-- ── 4 collapsible boards ── -->
      <div
        v-for="board in boards"
        :key="board.key"
        class="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <!-- Board header (toggle) -->
        <button
          type="button"
          class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors text-left"
          @click="toggleBoard(board.key)"
        >
          <div class="flex items-center gap-3">
            <span class="text-base font-semibold text-gray-800 dark:text-gray-200">{{ board.label }}</span>
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ boardTaskCount(board.key) }} tarea{{ boardTaskCount(board.key) === 1 ? '' : 's' }}</span>
          </div>
          <svg
            class="w-4 h-4 text-gray-400 transition-transform"
            :class="openBoards[board.key] ? 'rotate-180' : ''"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <!-- Board content -->
        <div v-if="openBoards[board.key]" class="p-3">
          <!-- Macro board: flat card list -->
          <div v-if="board.key === 'macro'">
            <div v-if="!taskStore.boardTasks.macro.length" class="text-sm text-gray-400 py-4 text-center">Sin macro-tareas todavía.</div>
            <ul v-else class="space-y-2">
              <li
                v-for="task in taskStore.boardTasks.macro"
                :key="task.id"
                class="flex items-center justify-between px-4 py-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                @click="openEdit(task)"
              >
                <div class="flex items-center gap-3 min-w-0">
                  <span
                    class="inline-block w-2 h-2 rounded-full flex-shrink-0"
                    :class="priorityDot(task.priority)"
                  />
                  <span class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{{ task.title }}</span>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0 ml-3">
                  <span v-if="task.due_date" class="text-xs" :class="task.is_overdue ? 'text-red-500' : 'text-gray-400'">{{ task.due_date }}</span>
                  <span v-if="task.assignee_name" class="text-xs text-gray-400">{{ task.assignee_name }}</span>
                </div>
              </li>
            </ul>
            <button
              type="button"
              class="mt-3 text-xs text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
              @click="openCreateOnBoard('macro', 'todo')"
            >+ Agregar macro-tarea</button>
          </div>

          <!-- Kanban boards -->
          <div v-else class="flex gap-2 overflow-x-auto pb-2">
            <TaskColumn
              v-for="col in columns"
              :key="col.status"
              :status="col.status"
              :label="col.label"
              :tasks="(taskStore.boardTasks[board.key] || {})[col.status] || []"
              @add="openCreateOnBoard(board.key, col.status)"
              @edit="openEdit"
              @move="handleMove"
            />
          </div>
        </div>
      </div>

      <!-- ── Archived tasks accordion ── -->
      <div class="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <button
          type="button"
          class="w-full flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors text-left"
          @click="toggleArchive"
        >
          <div class="flex items-center gap-3">
            <span class="text-sm font-semibold text-gray-500 dark:text-gray-400">Archivadas</span>
            <span v-if="taskStore.archivedTasks.length" class="text-xs text-gray-400">{{ taskStore.archivedTasks.length }}</span>
          </div>
          <svg
            class="w-4 h-4 text-gray-400 transition-transform"
            :class="archiveOpen ? 'rotate-180' : ''"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        <div v-if="archiveOpen" class="p-4">
          <div v-if="taskStore.archivedLoading" class="text-sm text-gray-400 py-4 text-center">Cargando…</div>
          <div v-else-if="!taskStore.archivedTasks.length" class="text-sm text-gray-400 py-4 text-center">No hay tareas archivadas.</div>
          <ul v-else class="space-y-2">
            <li
              v-for="task in taskStore.archivedTasks"
              :key="task.id"
              class="flex items-center justify-between px-4 py-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
            >
              <div class="min-w-0">
                <p class="text-sm text-gray-600 dark:text-gray-300 font-medium truncate">{{ task.title }}</p>
                <p v-if="task.archive_reason" class="text-xs text-gray-400 truncate mt-0.5">{{ task.archive_reason }}</p>
                <p class="text-xs text-gray-300 dark:text-gray-600 mt-0.5">{{ boardLabel(task.board_type) }}</p>
              </div>
              <button
                type="button"
                :disabled="taskStore.isUpdating"
                class="ml-4 flex-shrink-0 text-xs text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 disabled:opacity-50"
                @click="handleUnarchive(task)"
              >Restaurar</button>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Task form modal -->
    <TaskFormModal
      v-model="showModal"
      :task="editingTask"
      :default-status="defaultStatus"
      :default-board-type="activeBoardForCreate"
      :busy="taskStore.isUpdating"
      :assignees="taskStore.assignees"
      @submit="handleSubmit"
      @delete="handleDelete"
      @archive="handleArchive"
    />

    <!-- Confirm modal -->
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
import { ref, reactive } from 'vue';
import TaskColumn from '~/components/Tasks/TaskColumn.vue';
import TaskFormModal from '~/components/Tasks/TaskFormModal.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const taskStore = useTaskStore();
const showModal = ref(false);
const editingTask = ref(null);
const defaultStatus = ref('todo');
const activeBoardForCreate = ref('standard');
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const boards = [
  { key: 'macro',    label: 'Macro-Tareas' },
  { key: 'standard', label: 'Sin periodicidad' },
  { key: 'weekly',   label: 'Semanal' },
  { key: 'monthly',  label: 'Mensual' },
];

const columns = [
  { status: 'todo',        label: 'TO DO' },
  { status: 'in_progress', label: 'In Progress' },
  { status: 'blocked',     label: 'Blocked' },
  { status: 'done',        label: 'Done' },
];

const BOARD_LABELS = {
  standard: 'Sin periodicidad',
  weekly:   'Semanal',
  monthly:  'Mensual',
  macro:    'Macro-Tareas',
};

const openBoards = reactive({ standard: true, weekly: false, monthly: false, macro: false });
const archiveOpen = ref(false);

function toggleBoard(key) {
  openBoards[key] = !openBoards[key];
}

function toggleArchive() {
  archiveOpen.value = !archiveOpen.value;
  if (archiveOpen.value && !taskStore.archivedTasks.length) {
    taskStore.fetchArchivedTasks();
  }
}

function boardTaskCount(boardKey) {
  const board = taskStore.boardTasks[boardKey];
  if (!board) return 0;
  if (Array.isArray(board)) return board.length;
  return Object.values(board).reduce((s, list) => s + list.length, 0);
}

function boardLabel(key) {
  return BOARD_LABELS[key] || key;
}

function priorityDot(priority) {
  if (priority === 'high') return 'bg-red-500';
  if (priority === 'medium') return 'bg-yellow-400';
  return 'bg-gray-300 dark:bg-white/20';
}

onMounted(() => {
  Promise.all([taskStore.fetchAllBoards(), taskStore.fetchAssignees()]);
});

function openCreate(status) {
  editingTask.value = null;
  defaultStatus.value = status || 'todo';
  activeBoardForCreate.value = 'standard';
  showModal.value = true;
}

function openCreateOnBoard(boardKey, status) {
  editingTask.value = null;
  defaultStatus.value = status || 'todo';
  activeBoardForCreate.value = boardKey;
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
    message: `"${task.title}" se eliminará de forma permanente. Esta acción no se puede deshacer.`,
    confirmText: 'Eliminar',
    variant: 'danger',
  });
  if (!confirmed) return;
  const result = await taskStore.deleteTask(task.id);
  if (result.success) showModal.value = false;
}

async function handleArchive(task, reason) {
  if (!task?.id) return;
  const result = await taskStore.archiveTask(task.id, reason);
  if (result.success) {
    showModal.value = false;
    taskStore.archivedTasks = [];
  }
}

async function handleUnarchive(task) {
  if (!task?.id) return;
  await taskStore.unarchiveTask(task.id);
}

async function handleMove({ taskId, status, position }) {
  await taskStore.moveTask(taskId, status, position);
}
</script>
