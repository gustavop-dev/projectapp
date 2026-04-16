<template>
  <section>
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 mb-4">
      <div class="flex flex-wrap items-center gap-2">
        <select
          v-model="form.change_type"
          class="px-3 py-2 border border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 rounded-xl text-sm sm:w-44"
        >
          <option v-for="opt in changeTypes" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <input
          v-model="form.description"
          type="text"
          placeholder="Descripción de la actividad…"
          class="flex-1 px-3 py-2 border border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 rounded-xl text-sm"
          @keydown.enter.prevent="submit"
        />
        <button
          type="button"
          :disabled="!form.description.trim() || submitting"
          class="px-4 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 whitespace-nowrap"
          @click="submit"
        >Registrar</button>
      </div>
    </div>

    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
      <div class="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">
        Historial
      </div>
      <div v-if="!logs.length" class="text-sm text-gray-400 italic">
        Sin actividad registrada todavía.
      </div>
      <ol v-else class="relative border-l border-gray-200 dark:border-gray-700 pl-6 space-y-4">
        <li v-for="log in logs" :key="log.id" class="relative">
          <span
            class="absolute -left-6 top-1 w-[18px] h-[18px] rounded-full border-2 border-white dark:border-gray-800 shadow-sm flex items-center justify-center text-[10px]"
            :class="dotClass(log.change_type)"
          >{{ iconFor(log.change_type) }}</span>
          <div class="flex flex-wrap items-baseline gap-2">
            <span class="text-xs font-semibold" :class="labelClass(log.change_type)">
              {{ labelFor(log.change_type) }}
            </span>
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ formatDate(log.created_at) }}</span>
            <span v-if="log.actor_type" class="text-[10px] uppercase tracking-wide text-gray-400 dark:text-gray-500">
              · {{ log.actor_type }}
            </span>
          </div>
          <p v-if="log.description" class="text-sm text-gray-700 dark:text-gray-200 mt-1">{{ log.description }}</p>
          <p v-if="log.old_value || log.new_value" class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
            {{ log.field_name || 'valor' }}: {{ log.old_value || '∅' }} → {{ log.new_value || '∅' }}
          </p>
        </li>
      </ol>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { ACTIVITY_CHANGE_TYPES } from '~/stores/diagnostics_constants';

const props = defineProps({
  diagnostic: { type: Object, required: true },
});
const emit = defineEmits(['log', 'refresh']);

const submitting = ref(false);
const form = reactive({ change_type: 'note', description: '' });

const logs = computed(() => props.diagnostic?.change_logs || []);

const changeTypes = ACTIVITY_CHANGE_TYPES;

const META = {
  note: { icon: '✎', dot: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-200', text: 'text-gray-700 dark:text-gray-200', label: 'Nota' },
  call: { icon: '☎', dot: 'bg-blue-100 text-blue-600', text: 'text-blue-700', label: 'Llamada' },
  meeting: { icon: '🤝', dot: 'bg-purple-100 text-purple-600', text: 'text-purple-700', label: 'Reunión' },
  followup: { icon: '↻', dot: 'bg-amber-100 text-amber-700', text: 'text-amber-700', label: 'Seguimiento' },
  status_change: { icon: '→', dot: 'bg-indigo-100 text-indigo-700', text: 'text-indigo-700', label: 'Cambio de estado' },
  section_updated: { icon: '✎', dot: 'bg-emerald-100 text-emerald-700', text: 'text-emerald-700', label: 'Sección editada' },
  email_sent: { icon: '✉', dot: 'bg-sky-100 text-sky-700', text: 'text-sky-700', label: 'Email enviado' },
  created: { icon: '✦', dot: 'bg-green-100 text-green-700', text: 'text-green-700', label: 'Creado' },
  updated: { icon: '⟳', dot: 'bg-gray-100 text-gray-600', text: 'text-gray-700', label: 'Actualizado' },
  sent: { icon: '↗', dot: 'bg-sky-100 text-sky-700', text: 'text-sky-700', label: 'Enviado' },
  accepted: { icon: '✓', dot: 'bg-emerald-100 text-emerald-700', text: 'text-emerald-700', label: 'Aceptado' },
  rejected: { icon: '✕', dot: 'bg-rose-100 text-rose-700', text: 'text-rose-700', label: 'Rechazado' },
};

function iconFor(t) { return META[t]?.icon || '•'; }
function labelFor(t) { return META[t]?.label || t; }
function dotClass(t) { return META[t]?.dot || META.note.dot; }
function labelClass(t) { return META[t]?.text || 'text-gray-700'; }

const dateFormatter = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
function formatDate(iso) {
  if (!iso) return '';
  return dateFormatter.format(new Date(iso));
}

async function submit() {
  if (!form.description.trim() || submitting.value) return;
  submitting.value = true;
  try {
    await emit('log', { change_type: form.change_type, description: form.description.trim() });
    form.description = '';
  } finally {
    submitting.value = false;
  }
}
</script>
