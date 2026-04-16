<template>
  <div class="diagnostic-doc-editor border rounded-lg overflow-hidden bg-white">
    <header
      class="flex items-center justify-between gap-3 border-b bg-gray-50 px-4 py-3"
    >
      <div class="flex items-center gap-3">
        <h3 class="text-base font-semibold text-gray-800">{{ doc.title }}</h3>
        <span
          v-if="doc.is_ready"
          class="text-xs font-medium text-emerald-700 bg-emerald-100 px-2 py-1 rounded"
        >Listo</span>
      </div>
      <div class="flex items-center gap-2 text-sm">
        <label class="inline-flex items-center gap-1 cursor-pointer">
          <input
            type="checkbox"
            :checked="doc.is_ready"
            @change="$emit('toggle-ready', $event.target.checked)"
          />
          <span>Marcar listo</span>
        </label>
        <button
          type="button"
          class="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-100"
          @click="$emit('restore')"
        >
          Restaurar template
        </button>
        <button
          type="button"
          class="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-100"
          @click="previewOnly = !previewOnly"
        >
          {{ previewOnly ? 'Editar' : 'Solo preview' }}
        </button>
      </div>
    </header>

    <div class="grid" :class="previewOnly ? 'grid-cols-1' : 'lg:grid-cols-2'">
      <textarea
        v-if="!previewOnly"
        class="font-mono text-sm p-4 outline-none resize-y min-h-[60vh] border-r border-gray-200"
        :value="doc.content_md"
        spellcheck="false"
        @input="$emit('update:content', $event.target.value)"
      />
      <div class="p-4 overflow-auto bg-gray-50/40 max-h-[80vh]">
        <DiagnosticDocumentViewer :markdown="previewMarkdown" />
      </div>
    </div>

    <footer class="px-4 py-2 border-t bg-gray-50 text-xs text-gray-500 flex flex-wrap gap-2">
      <span class="font-semibold">Variables:</span>
      <button
        v-for="v in availableVars"
        :key="v"
        type="button"
        class="px-2 py-0.5 rounded bg-white border border-gray-300 hover:bg-emerald-50 hover:border-emerald-300"
        @click="copyVar(v)"
      >{{ wrapVar(v) }}</button>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import DiagnosticDocumentViewer from './DiagnosticDocumentViewer.vue';

const props = defineProps({
  doc: { type: Object, required: true },
});

defineEmits(['update:content', 'toggle-ready', 'restore']);

const previewOnly = ref(false);

const previewMarkdown = computed(() => props.doc.rendered_md || props.doc.content_md);

const availableVars = [
  'client_name',
  'investment_amount',
  'currency',
  'payment_initial_pct',
  'payment_final_pct',
  'duration_label',
  'size_category_label',
  'stack_backend_name',
  'stack_backend_version',
  'stack_frontend_name',
  'stack_frontend_version',
  'entities_count',
  'routes_total',
  'routes_public',
  'routes_protected',
  'frontend_routes_count',
  'components_count',
  'external_integrations',
  'modules_count',
  'modules_list',
];

function wrapVar(name) { return '{{' + name + '}}'; }

async function copyVar(name) {
  const token = `{{${name}}}`;
  try {
    await navigator.clipboard.writeText(token);
  } catch (_) {
    // best effort
  }
}
</script>
