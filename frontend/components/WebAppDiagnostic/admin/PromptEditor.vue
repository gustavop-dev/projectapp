<template>
  <div>
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <template v-if="!state.isEditing.value">
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-text-brand border border-emerald-200 dark:border-emerald-500/40 rounded-lg hover:bg-primary-soft dark:hover:bg-emerald-500/10"
          @click="startEdit"
        >Editar</button>
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-text-default border border-border-default rounded-lg hover:bg-surface-raised"
          @click="onCopy"
        >{{ copied ? '¡Copiado!' : 'Copiar' }}</button>
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-text-default border border-border-default rounded-lg hover:bg-surface-raised"
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
          class="px-3 py-1.5 text-xs font-medium text-white bg-primary rounded-lg hover:opacity-90"
          @click="saveEdit"
        >Guardar</button>
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium text-text-default border border-border-default rounded-lg hover:bg-surface-raised"
          @click="cancelEdit"
        >Cancelar</button>
      </template>
    </div>

    <div v-if="state.isEditing.value" class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
      <textarea
        v-model="buffer"
        rows="24"
        class="w-full px-4 py-3 text-xs font-mono leading-relaxed text-text-default bg-transparent focus:outline-none"
      ></textarea>
    </div>
    <div v-else class="bg-surface-muted rounded-xl border border-border-muted p-4 max-h-[520px] overflow-auto">
      <pre class="text-xs leading-relaxed text-text-default whitespace-pre-wrap font-mono break-words">{{ state.promptText.value }}</pre>
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
