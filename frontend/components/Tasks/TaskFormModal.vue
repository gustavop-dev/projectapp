<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="close"
      >
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full p-6" data-testid="task-form-modal">
          <div class="flex items-center justify-between mb-5">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {{ isEditing ? 'Edit task' : 'New task' }}
            </h3>
            <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200" @click="close">✕</button>
          </div>

          <form class="space-y-4" @submit.prevent="handleSubmit">
            <div>
              <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Title</label>
              <input
                v-model="form.title"
                required
                type="text"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                data-testid="task-title-input"
              />
            </div>

            <div>
              <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Description</label>
              <textarea
                v-model="form.description"
                rows="3"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              ></textarea>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Status</label>
                <select
                  v-model="form.status"
                  class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100"
                >
                  <option value="todo">TO DO</option>
                  <option value="in_progress">In Progress</option>
                  <option value="blocked">Blocked</option>
                  <option value="done">Done</option>
                </select>
              </div>
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Priority</label>
                <select
                  v-model="form.priority"
                  class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Due date</label>
                <input
                  v-model="form.due_date"
                  type="date"
                  class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100"
                />
              </div>
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Assigned to</label>
                <select
                  v-model="form.assignee_id"
                  class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100"
                >
                  <option value="">Unassigned</option>
                  <option v-for="user in assignees" :key="user.id" :value="user.id">
                    {{ user.name }}
                  </option>
                </select>
              </div>
            </div>

            <!-- Alertas manuales (solo en edición) -->
            <div v-if="isEditing" class="pt-1">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Alertas</span>
                <span
                  v-if="alerts.length"
                  class="inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-medium rounded-full bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400"
                >{{ alerts.length }}</span>
              </div>

              <div v-if="store.alertsLoading" class="text-xs text-gray-400 py-1">Cargando alertas…</div>

              <ul v-else-if="alerts.length" class="space-y-1.5 mb-3">
                <li
                  v-for="alert in alerts"
                  :key="alert.id"
                  class="flex items-start justify-between gap-2 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-700/50 text-sm"
                >
                  <div class="flex-1 min-w-0">
                    <span class="font-medium text-gray-800 dark:text-gray-200">{{ formatAlertDate(alert.notify_at) }}</span>
                    <span
                      v-if="alert.sent"
                      class="ml-2 text-xs px-1.5 py-0.5 rounded-full bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400"
                    >Enviada</span>
                    <span
                      v-else
                      class="ml-2 text-xs px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500 dark:bg-gray-600 dark:text-gray-400"
                    >Pendiente</span>
                    <p v-if="alert.note" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">{{ alert.note }}</p>
                  </div>
                  <button
                    type="button"
                    class="text-gray-400 hover:text-red-500 dark:hover:text-red-400 flex-shrink-0 mt-0.5"
                    :disabled="deletingAlertId === alert.id"
                    @click="handleDeleteAlert(alert.id)"
                  >✕</button>
                </li>
              </ul>
              <p v-else class="text-xs text-gray-400 dark:text-gray-500 mb-3">No hay alertas definidas.</p>

              <!-- Add alert form -->
              <div class="flex gap-2 items-end">
                <div class="flex-shrink-0">
                  <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Fecha</label>
                  <input
                    v-model="newAlert.notify_at"
                    type="date"
                    class="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100 focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                  />
                </div>
                <div class="flex-1 min-w-0">
                  <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Nota <span class="text-gray-400">(opcional)</span></label>
                  <input
                    v-model="newAlert.note"
                    type="text"
                    placeholder="Ej: Revisar avance con el cliente"
                    class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100 focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                  />
                </div>
                <button
                  type="button"
                  :disabled="!newAlert.notify_at || isAddingAlert"
                  class="px-3 py-2 text-sm rounded-lg bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50 flex-shrink-0"
                  @click="handleAddAlert"
                >
                  {{ isAddingAlert ? '…' : '+ Agregar' }}
                </button>
              </div>
            </div>

            <div class="flex items-center justify-between pt-3">
              <button
                v-if="isEditing"
                type="button"
                class="text-sm text-red-600 hover:text-red-700 dark:text-red-400"
                :disabled="busy"
                @click="handleDelete"
              >
                Delete
              </button>
              <span v-else></span>
              <div class="flex gap-2">
                <button
                  type="button"
                  class="px-4 py-2 text-sm rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200"
                  @click="close"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  :disabled="busy || !form.title.trim()"
                  class="px-4 py-2 text-sm rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
                  data-testid="task-submit-btn"
                >
                  {{ busy ? 'Saving...' : (isEditing ? 'Save' : 'Create') }}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useTaskStore } from '~/stores/tasks';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  task: { type: Object, default: null },
  defaultStatus: { type: String, default: 'todo' },
  busy: { type: Boolean, default: false },
  assignees: { type: Array, default: () => [] },
});

const emit = defineEmits(['update:modelValue', 'submit', 'delete']);

const store = useTaskStore();

const isEditing = computed(() => Boolean(props.task?.id));
const alerts = computed(() => store.taskAlerts[props.task?.id] ?? []);

const form = ref(buildForm(props.task, props.defaultStatus));

const newAlert = ref({ notify_at: '', note: '' });
const isAddingAlert = ref(false);
const deletingAlertId = ref(null);

function buildForm(task, defaultStatus) {
  if (task) {
    return {
      title: task.title || '',
      description: task.description || '',
      status: task.status || 'todo',
      priority: task.priority || 'medium',
      due_date: task.due_date || '',
      assignee_id: task.assignee || '',
    };
  }
  return {
    title: '',
    description: '',
    status: defaultStatus || 'todo',
    priority: 'medium',
    due_date: '',
    assignee_id: '',
  };
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      form.value = buildForm(props.task, props.defaultStatus);
      newAlert.value = { notify_at: '', note: '' };
      if (props.task?.id) {
        store.fetchTaskAlerts(props.task.id);
      }
    }
  },
);

function formatAlertDate(dateStr) {
  if (!dateStr) return '';
  const [y, m, d] = dateStr.split('-');
  return new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString('es-CO', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
}

function close() {
  emit('update:modelValue', false);
}

function handleSubmit() {
  const payload = {
    title: form.value.title.trim(),
    description: form.value.description,
    status: form.value.status,
    priority: form.value.priority,
  };
  if (form.value.due_date) payload.due_date = form.value.due_date;
  else payload.due_date = null;
  if (form.value.assignee_id) payload.assignee_id = Number(form.value.assignee_id);
  else payload.assignee_id = null;
  emit('submit', payload);
}

function handleDelete() {
  emit('delete', props.task);
}

async function handleAddAlert() {
  if (!newAlert.value.notify_at) return;
  isAddingAlert.value = true;
  const payload = { notify_at: newAlert.value.notify_at };
  if (newAlert.value.note.trim()) payload.note = newAlert.value.note.trim();
  const result = await store.createTaskAlert(props.task.id, payload);
  if (result.success) {
    newAlert.value = { notify_at: '', note: '' };
  }
  isAddingAlert.value = false;
}

async function handleDeleteAlert(alertId) {
  deletingAlertId.value = alertId;
  await store.deleteTaskAlert(props.task.id, alertId);
  deletingAlertId.value = null;
}
</script>
