<template>
  <div>
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <template v-if="!state.isEditing.value">
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/40 rounded-lg hover:bg-emerald-50 dark:hover:bg-emerald-500/10"
          @click="startEdit"
        >Editar</button>
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
          @click="onCopy"
        >{{ copied ? '¡Copiado!' : 'Copiar' }}</button>
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
          @click="onDownload"
        >Descargar .md</button>
        <button
          v-if="isCustom"
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-500/40 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-500/10"
          @click="onReset"
        >Restaurar original</button>
      </template>
      <template v-else>
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700"
          @click="saveEdit"
        >Guardar</button>
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
          @click="cancelEdit"
        >Cancelar</button>
      </template>
    </div>

    <div v-if="state.isEditing.value" class="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      <textarea
        v-model="buffer"
        rows="24"
        class="w-full px-4 py-3 text-xs font-mono leading-relaxed text-gray-800 dark:text-gray-100 bg-transparent focus:outline-none"
      ></textarea>
    </div>
    <div v-else class="bg-gray-50 dark:bg-gray-900/60 rounded-xl border border-gray-100 dark:border-gray-700 p-4 max-h-[520px] overflow-auto">
      <pre class="text-xs leading-relaxed text-gray-700 dark:text-gray-200 whitespace-pre-wrap font-mono break-words">{{ state.promptText.value }}</pre>
    </div>

    <p v-if="isCustom" class="text-xs text-amber-600 dark:text-amber-400 mt-3">
      Este prompt ha sido personalizado. «Restaurar original» vuelve al valor por defecto.
    </p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  state: { type: Object, required: true },
  downloadFilename: { type: String, required: true },
});

const buffer = ref('');
const copied = ref(false);

const isCustom = computed(() => props.state.promptText.value !== props.state.defaultPrompt);

function startEdit() {
  buffer.value = props.state.promptText.value;
  props.state.isEditing.value = true;
}

function cancelEdit() {
  props.state.isEditing.value = false;
}

function saveEdit() {
  props.state.save(buffer.value);
  props.state.isEditing.value = false;
}

function onReset() {
  props.state.reset();
}

async function onCopy() {
  await props.state.copy();
  copied.value = true;
  setTimeout(() => { copied.value = false; }, 1500);
}

function onDownload() {
  props.state.download(props.downloadFilename);
}
</script>
