<template>
  <div class="section-editor">
    <!-- JSON editor for content_json -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        Contenido (JSON)
      </label>
      <textarea
        v-model="jsonText"
        rows="12"
        class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm font-mono
               focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
               bg-gray-50 resize-y"
        :class="{ 'border-red-300 bg-red-50': jsonError }"
        @input="validateJson"
      />
      <p v-if="jsonError" class="text-xs text-red-500 mt-1">{{ jsonError }}</p>
      <p class="text-xs text-gray-400 mt-1">
        Edita el JSON directamente. Este contenido se pasa como props al componente Vue.
      </p>
    </div>

    <!-- Section title -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 mb-1">Título de la sección</label>
      <input
        v-model="sectionTitle"
        type="text"
        class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
               focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
      />
    </div>

    <!-- Wide panel toggle -->
    <div class="mb-6">
      <label class="flex items-center gap-2 text-sm">
        <input
          v-model="isWidePanel"
          type="checkbox"
          class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
        />
        <span class="text-gray-700">Panel ancho (para secciones con scroll horizontal interno)</span>
      </label>
    </div>

    <!-- Save button -->
    <div class="flex items-center gap-3">
      <button
        type="button"
        :disabled="!!jsonError || isSaving"
        class="px-5 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium
               hover:bg-emerald-700 transition-colors disabled:opacity-50"
        @click="handleSave"
      >
        {{ isSaving ? 'Guardando...' : 'Guardar Sección' }}
      </button>
      <span v-if="savedMsg" class="text-xs text-green-600">{{ savedMsg }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  section: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['save']);

const jsonText = ref(JSON.stringify(props.section.content_json || {}, null, 2));
const jsonError = ref('');
const sectionTitle = ref(props.section.title);
const isWidePanel = ref(props.section.is_wide_panel);
const isSaving = ref(false);
const savedMsg = ref('');

watch(() => props.section, (newSection) => {
  jsonText.value = JSON.stringify(newSection.content_json || {}, null, 2);
  sectionTitle.value = newSection.title;
  isWidePanel.value = newSection.is_wide_panel;
}, { deep: true });

function validateJson() {
  jsonError.value = '';
  try {
    const parsed = JSON.parse(jsonText.value);
    if (typeof parsed !== 'object' || Array.isArray(parsed)) {
      jsonError.value = 'content_json debe ser un objeto JSON (no array).';
    }
  } catch (e) {
    jsonError.value = `JSON inválido: ${e.message}`;
  }
}

async function handleSave() {
  validateJson();
  if (jsonError.value) return;

  isSaving.value = true;
  savedMsg.value = '';

  try {
    const contentJson = JSON.parse(jsonText.value);
    emit('save', {
      sectionId: props.section.id,
      payload: {
        title: sectionTitle.value,
        is_wide_panel: isWidePanel.value,
        content_json: contentJson,
      },
    });
    savedMsg.value = '✓ Guardado';
    setTimeout(() => { savedMsg.value = ''; }, 3000);
  } catch {
    jsonError.value = 'Error al procesar el JSON.';
  } finally {
    isSaving.value = false;
  }
}
</script>
