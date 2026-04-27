<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="close"
      >
        <div class="bg-surface rounded-2xl shadow-2xl max-w-lg w-full p-6" data-testid="task-form-modal">
          <div class="flex items-center justify-between mb-5">
            <h3 class="text-lg font-semibold text-text-default">
              {{ isEditing ? 'Edit task' : 'New task' }}
            </h3>
            <button class="text-gray-400 hover:text-text-muted dark:hover:text-gray-200" @click="close">✕</button>
          </div>

          <form class="space-y-4" @submit.prevent="handleSubmit">
            <div>
              <label class="block text-xs text-text-muted dark:text-gray-400 mb-1">Title</label>
              <input
                v-model="form.title"
                required
                type="text"
                class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500"
                data-testid="task-title-input"
              />
            </div>

            <div>
              <label class="block text-xs text-text-muted dark:text-gray-400 mb-1">Description</label>
              <textarea
                v-model="form.description"
                rows="3"
                class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500"
              ></textarea>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-text-muted dark:text-gray-400 mb-1">Status</label>
                <select
                  v-model="form.status"
                  class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface"
                >
                  <option value="todo">TO DO</option>
                  <option value="in_progress">In Progress</option>
                  <option value="blocked">Blocked</option>
                  <option value="done">Done</option>
                </select>
              </div>
              <div>
                <label class="block text-xs text-text-muted dark:text-gray-400 mb-1">Priority</label>
                <select
                  v-model="form.priority"
                  class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs text-text-muted dark:text-gray-400 mb-1">Tablero</label>
              <select
                v-model="form.board_type"
                class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface"
              >
                <option value="standard">Sin periodicidad</option>
                <option value="weekly">Semanal</option>
                <option value="monthly">Mensual</option>
                <option value="macro">Macro-tarea</option>
              </select>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-text-muted dark:text-gray-400 mb-1">Due date</label>
                <input
                  v-model="form.due_date"
                  type="date"
                  class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface"
                />
              </div>
              <div>
                <label class="block text-xs text-text-muted dark:text-gray-400 mb-1">Assigned to</label>
                <select
                  v-model="form.assignee_id"
                  class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface"
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
                <span class="text-xs font-semibold text-text-muted dark:text-gray-400 uppercase tracking-wide">Alertas</span>
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
                  class="flex items-start justify-between gap-2 px-3 py-2 rounded-lg bg-gray-50/50 text-sm"
                >
                  <div class="flex-1 min-w-0">
                    <span class="font-medium text-text-default">{{ formatAlertDate(alert.notify_at) }}</span>
                    <span
                      v-if="alert.sent"
                      class="ml-2 text-xs px-1.5 py-0.5 rounded-full bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400"
                    >Enviada</span>
                    <span
                      v-else
                      class="ml-2 text-xs px-1.5 py-0.5 rounded-full bg-gray-100 text-text-muted dark:text-gray-400"
                    >Pendiente</span>
                    <p v-if="alert.note" class="text-xs text-text-muted dark:text-gray-400 mt-0.5 truncate">{{ alert.note }}</p>
                  </div>
                  <button
                    type="button"
                    class="text-gray-400 hover:text-red-500 dark:hover:text-red-400 flex-shrink-0 mt-0.5"
                    :disabled="deletingAlertId === alert.id"
                    @click="handleDeleteAlert(alert.id)"
                  >✕</button>
                </li>
              </ul>
              <p v-else class="text-xs text-gray-400 dark:text-text-muted mb-3">No hay alertas definidas.</p>

              <!-- Add alert form -->
              <div class="flex gap-2 items-end">
                <div class="flex-shrink-0">
                  <label class="block text-xs text-text-muted dark:text-gray-400 mb-1">Fecha</label>
                  <input
                    v-model="newAlert.notify_at"
                    type="date"
                    class="px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
                  />
                </div>
                <div class="flex-1 min-w-0">
                  <label class="block text-xs text-text-muted dark:text-gray-400 mb-1">Nota <span class="text-gray-400">(opcional)</span></label>
                  <input
                    v-model="newAlert.note"
                    type="text"
                    placeholder="Ej: Revisar avance con el cliente"
                    class="w-full px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
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

            <!-- Comment thread (edit mode only) -->
            <div v-if="isEditing" class="pt-1">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-semibold text-text-muted dark:text-gray-400 uppercase tracking-wide">Comentarios</span>
                <span
                  v-if="comments.length"
                  class="inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                >{{ comments.length }}</span>
              </div>

              <div v-if="store.commentsLoading" class="text-xs text-gray-400 py-1">Cargando…</div>

              <ul v-else-if="comments.length" class="space-y-2 mb-3 max-h-40 overflow-y-auto">
                <li
                  v-for="comment in comments"
                  :key="comment.id"
                  class="flex items-start gap-2 px-3 py-2 rounded-lg bg-gray-50/50 text-sm"
                >
                  <div class="flex-1 min-w-0">
                    <div class="flex items-baseline gap-2">
                      <span class="font-medium text-text-default text-xs">{{ comment.author_name }}</span>
                      <span class="text-[10px] text-gray-400">{{ formatCommentDate(comment.created_at) }}</span>
                    </div>
                    <p class="mt-0.5 text-xs text-text-muted whitespace-pre-wrap">{{ comment.text }}</p>
                  </div>
                  <button
                    type="button"
                    class="text-gray-300 hover:text-red-500 dark:hover:text-red-400 flex-shrink-0 mt-0.5 text-xs"
                    @click="handleDeleteComment(comment.id)"
                  >✕</button>
                </li>
              </ul>
              <p v-else class="text-xs text-gray-400 dark:text-text-muted mb-3">Sin comentarios aún.</p>

              <div class="flex gap-2">
                <input
                  v-model="newComment"
                  type="text"
                  placeholder="Agregar comentario…"
                  class="flex-1 px-3 py-2 border border-border-default rounded-lg text-sm bg-surface focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  @keydown.enter.prevent="handleAddComment"
                />
                <button
                  type="button"
                  :disabled="!newComment.trim() || isAddingComment"
                  class="px-3 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 flex-shrink-0"
                  @click="handleAddComment"
                >{{ isAddingComment ? '…' : '+ Agregar' }}</button>
              </div>
            </div>

            <!-- Archive section (edit mode only) -->
            <div v-if="isEditing" class="pt-1">
              <!-- Already archived: show badge + reason -->
              <div v-if="props.task?.is_archived" class="flex items-start gap-2 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-700/40">
                <span class="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-semibold rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400 flex-shrink-0">Archivada</span>
                <p v-if="props.task.archive_reason" class="text-xs text-amber-700 dark:text-amber-400 flex-1">{{ props.task.archive_reason }}</p>
                <p v-else class="text-xs text-gray-400 italic flex-1">Sin motivo registrado.</p>
              </div>
              <!-- Not archived: show archive trigger / form -->
              <div v-else-if="!showArchiveForm" class="flex items-center gap-2">
                <button
                  type="button"
                  class="text-xs text-amber-600 hover:text-amber-700 dark:text-amber-400 underline"
                  @click="showArchiveForm = true"
                >Archivar tarea</button>
              </div>
              <div v-else class="space-y-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-700/40">
                <label class="block text-xs font-medium text-amber-700 dark:text-amber-400">Motivo del archivo <span class="text-gray-400">(opcional)</span></label>
                <textarea
                  v-model="archiveReason"
                  rows="2"
                  placeholder="Ej: Descartada por cambio de prioridades…"
                  class="w-full px-3 py-2 border border-amber-200 rounded-lg text-sm bg-surface focus:ring-2 focus:ring-amber-500"
                ></textarea>
                <div class="flex gap-2">
                  <button
                    type="button"
                    :disabled="busy"
                    class="px-3 py-1.5 text-xs rounded-lg bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50"
                    @click="handleArchive"
                  >Confirmar archivo</button>
                  <button type="button" class="text-xs text-text-muted hover:text-text-default" @click="showArchiveForm = false">Cancelar</button>
                </div>
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
                  class="px-4 py-2 text-sm rounded-lg bg-gray-100 text-text-default hover:bg-gray-200"
                  @click="close"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  :disabled="busy || !form.title.trim()"
                  class="px-4 py-2 text-sm rounded-lg bg-primary text-white hover:bg-primary-strong disabled:opacity-50"
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
  defaultBoardType: { type: String, default: 'standard' },
  busy: { type: Boolean, default: false },
  assignees: { type: Array, default: () => [] },
});

const emit = defineEmits(['update:modelValue', 'submit', 'delete', 'archive']);

const store = useTaskStore();

const isEditing = computed(() => Boolean(props.task?.id));
const alerts = computed(() => store.taskAlerts[props.task?.id] ?? []);
const comments = computed(() => store.comments[props.task?.id] ?? []);

const form = ref(buildForm(props.task, props.defaultStatus));

const newAlert = ref({ notify_at: '', note: '' });
const isAddingAlert = ref(false);
const deletingAlertId = ref(null);

const newComment = ref('');
const isAddingComment = ref(false);

const showArchiveForm = ref(false);
const archiveReason = ref('');

function buildForm(task, defaultStatus, defaultBoardType) {
  if (task) {
    return {
      title: task.title || '',
      description: task.description || '',
      status: task.status || 'todo',
      priority: task.priority || 'medium',
      board_type: task.board_type || 'standard',
      due_date: task.due_date || '',
      assignee_id: task.assignee || '',
    };
  }
  return {
    title: '',
    description: '',
    status: defaultStatus || 'todo',
    priority: 'medium',
    board_type: props.defaultBoardType || 'standard',
    due_date: '',
    assignee_id: '',
  };
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      form.value = buildForm(props.task, props.defaultStatus, props.defaultBoardType);
      newAlert.value = { notify_at: '', note: '' };
      newComment.value = '';
      showArchiveForm.value = false;
      archiveReason.value = '';
      if (props.task?.id) {
        store.fetchTaskAlerts(props.task.id);
        store.fetchTaskComments(props.task.id);
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
    board_type: form.value.board_type,
  };
  if (form.value.due_date) payload.due_date = form.value.due_date;
  else payload.due_date = null;
  if (form.value.assignee_id) payload.assignee_id = Number(form.value.assignee_id);
  else payload.assignee_id = null;
  emit('submit', payload);
}

async function handleAddComment() {
  const text = newComment.value.trim();
  if (!text) return;
  isAddingComment.value = true;
  const result = await store.addTaskComment(props.task.id, text);
  if (result.success) newComment.value = '';
  isAddingComment.value = false;
}

async function handleDeleteComment(commentId) {
  await store.deleteTaskComment(props.task.id, commentId);
}

async function handleArchive() {
  emit('archive', props.task, archiveReason.value.trim());
}

function formatCommentDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('es-CO', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
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
