<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
    @click.self="$emit('close')">
    <div class="bg-white dark:bg-esmerald rounded-xl shadow-xl max-w-lg w-full max-h-[85vh] flex flex-col border border-gray-200 dark:border-white/[0.08]">
      <header class="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-white/[0.06]">
        <h3 class="text-sm font-semibold text-gray-800 dark:text-white">
          Adjuntar desde Documentos
        </h3>
        <button type="button" class="text-gray-400 hover:text-gray-600 dark:hover:text-white/70"
          @click="$emit('close')">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </header>

      <div class="flex-1 overflow-y-auto px-5 py-3">
        <p v-if="!availableDocs.length" class="text-xs text-gray-400 dark:text-white/40 py-6 text-center">
          No hay documentos disponibles para adjuntar.
        </p>
        <ul v-else class="divide-y divide-gray-100 dark:divide-white/[0.06]">
          <li v-for="doc in availableDocs" :key="doc.key" class="py-2.5 flex items-center gap-3">
            <input :id="`attach-${doc.key}`" v-model="selectedKeys" type="checkbox" :value="doc.key"
              class="rounded border-gray-300 dark:border-white/[0.15] text-emerald-600 focus:ring-emerald-500" />
            <label :for="`attach-${doc.key}`" class="flex-1 min-w-0 cursor-pointer">
              <div class="text-sm text-gray-800 dark:text-white truncate">{{ doc.label }}</div>
              <div class="text-[11px] text-gray-400 dark:text-white/40 mt-0.5">{{ doc.description }}</div>
            </label>
          </li>
        </ul>
      </div>

      <footer class="flex items-center justify-end gap-2 px-5 py-3 border-t border-gray-100 dark:border-white/[0.06]">
        <button type="button"
          class="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-white/70 hover:text-gray-800 dark:hover:text-white"
          @click="$emit('close')">
          Cancelar
        </button>
        <button type="button" :disabled="!selectedKeys.length"
          class="px-4 py-1.5 text-xs font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
          @click="confirm">
          Adjuntar ({{ selectedKeys.length }})
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  open: { type: Boolean, default: false },
  /** 'proposal' | 'diagnostic' */
  source: { type: String, required: true },
  /** Proposal or Diagnostic object (with uploaded files list) */
  entity: { type: Object, required: true },
  /** Static diagnostic MD templates (only used when source === 'diagnostic') */
  templates: { type: Array, default: () => [] },
  /** Already-selected keys to pre-check */
  preselected: { type: Array, default: () => [] },
});

const emit = defineEmits(['close', 'attach']);

const selectedKeys = ref([...props.preselected]);

watch(() => props.open, (open) => {
  if (open) selectedKeys.value = [...props.preselected];
});

const availableDocs = computed(() => {
  if (props.source === 'proposal') return proposalDocs();
  if (props.source === 'diagnostic') return diagnosticDocs();
  return [];
});

function proposalDocs() {
  const proposal = props.entity || {};
  const list = [];
  const contract = (proposal.proposal_documents || []).find(d => d.document_type === 'contract');
  if (contract) {
    list.push({
      key: 'contract_pdf',
      label: 'Contrato de desarrollo (PDF)',
      description: 'Versión final generada',
      ref: { source: 'contract_pdf' },
    });
    list.push({
      key: 'contract_draft',
      label: 'Contrato de desarrollo (borrador)',
      description: 'PDF con marca de agua',
      ref: { source: 'contract_draft' },
    });
  }
  list.push({
    key: 'commercial_pdf',
    label: 'Propuesta comercial (PDF)',
    description: 'PDF con branding',
    ref: { source: 'commercial_pdf' },
  });
  list.push({
    key: 'technical_pdf',
    label: 'Detalle técnico (PDF)',
    description: 'PDF con branding',
    ref: { source: 'technical_pdf' },
  });
  for (const doc of (proposal.proposal_documents || [])) {
    if (doc.document_type === 'contract') continue;
    list.push({
      key: `proposal_document:${doc.id}`,
      label: doc.title,
      description: doc.document_type_display || 'Documento adjunto',
      ref: { source: 'proposal_document', id: doc.id },
    });
  }
  return list;
}

function diagnosticDocs() {
  const diagnostic = props.entity || {};
  const list = [];
  const nda = (diagnostic.attachments || []).find(
    (a) => a.document_type === 'confidentiality_agreement' && a.is_generated,
  );
  if (nda) {
    list.push({
      key: 'nda_final',
      label: 'Acuerdo de confidencialidad (PDF)',
      description: 'Versión final generada',
      ref: { source: 'nda_final' },
    });
    list.push({
      key: 'nda_draft',
      label: 'Acuerdo de confidencialidad (borrador)',
      description: 'PDF con marca de agua',
      ref: { source: 'nda_draft' },
    });
  }
  for (const t of (props.templates || [])) {
    list.push({
      key: `template:${t.slug}`,
      label: t.title,
      description: `${t.filename} · plantilla markdown`,
      ref: { source: 'template', slug: t.slug },
    });
  }
  for (const att of (diagnostic.attachments || [])) {
    if (att.document_type === 'confidentiality_agreement' && att.is_generated) continue;
    list.push({
      key: `attachment:${att.id}`,
      label: att.title,
      description: att.document_type_display || 'Documento adjunto',
      ref: { source: 'attachment', id: att.id },
    });
  }
  return list;
}

function confirm() {
  const picked = availableDocs.value.filter(d => selectedKeys.value.includes(d.key));
  emit('attach', picked.map(d => ({ key: d.key, label: d.label, ref: d.ref })));
  emit('close');
}
</script>
