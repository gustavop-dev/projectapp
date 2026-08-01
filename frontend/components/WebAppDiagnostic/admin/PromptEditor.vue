<template>
  <div>
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <template v-if="!state.isEditing.value">
        <BaseButton variant="secondary" size="sm" @click="startEdit">Editar</BaseButton>
        <BaseButton variant="secondary" size="sm" @click="onCopy">{{ copied ? '¡Copiado!' : 'Copiar' }}</BaseButton>
        <BaseButton variant="secondary" size="sm" @click="onDownload">Descargar .md</BaseButton>
        <BaseButton variant="secondary" size="sm" v-if="isCustom" @click="onReset">Restaurar original</BaseButton>
      </template>
      <template v-else>
        <BaseButton variant="primary" size="sm" @click="saveEdit">Guardar</BaseButton>
        <BaseButton variant="ghost" size="sm" @click="cancelEdit">Cancelar</BaseButton>
      </template>
    </div>

    <div v-if="state.isEditing.value" class="bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
      <textarea
        v-model="buffer"
        rows="24"
        class="w-full px-4 py-3 text-xs font-mono leading-relaxed text-text-default bg-transparent focus:outline-none"
        data-testid="prompt-editor-textarea"
      ></textarea>
    </div>
    <div v-else class="bg-surface-muted rounded-xl border border-border-muted p-4 max-h-[520px] overflow-auto">
      <pre class="text-xs leading-relaxed text-text-default whitespace-pre-wrap font-mono break-words" data-testid="prompt-editor-display">{{ state.promptText.value }}</pre>
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
