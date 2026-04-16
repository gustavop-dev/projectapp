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
              {{ isEditing ? 'Editar tarea' : 'Nueva tarea' }}
            </h3>
            <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200" @click="close">✕</button>
          </div>

          <form class="space-y-4" @submit.prevent="handleSubmit">
            <div>
              <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Título</label>
              <input
                v-model="form.title"
                required
                type="text"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                data-testid="task-title-input"
              />
            </div>

            <div>
              <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Descripción</label>
              <textarea
                v-model="form.description"
                rows="3"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              ></textarea>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Estado</label>
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
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Prioridad</label>
                <select
                  v-model="form.priority"
                  class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100"
                >
                  <option value="low">Baja</option>
                  <option value="medium">Media</option>
                  <option value="high">Alta</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Fecha límite</label>
                <input
                  v-model="form.due_date"
                  type="date"
                  class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100"
                />
              </div>
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Asignado a</label>
                <select
                  v-model="form.assignee_id"
                  class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 dark:text-gray-100"
                >
                  <option value="">Sin asignar</option>
                  <option v-for="user in assignees" :key="user.id" :value="user.id">
                    {{ user.name }}
                  </option>
                </select>
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
                Eliminar
              </button>
              <span v-else></span>
              <div class="flex gap-2">
                <button
                  type="button"
                  class="px-4 py-2 text-sm rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200"
                  @click="close"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  :disabled="busy || !form.title.trim()"
                  class="px-4 py-2 text-sm rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
                  data-testid="task-submit-btn"
                >
                  {{ busy ? 'Guardando...' : (isEditing ? 'Guardar' : 'Crear') }}
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

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  task: { type: Object, default: null },
  defaultStatus: { type: String, default: 'todo' },
  busy: { type: Boolean, default: false },
  assignees: { type: Array, default: () => [] },
});

const emit = defineEmits(['update:modelValue', 'submit', 'delete']);

const isEditing = computed(() => Boolean(props.task?.id));

const form = ref(buildForm(props.task, props.defaultStatus));

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
    if (open) form.value = buildForm(props.task, props.defaultStatus);
  },
);

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
</script>
