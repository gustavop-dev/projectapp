<template>
  <BaseModal :model-value="open" size="2xl" full-height @update:model-value="emit('close')">
    <div class="flex flex-col h-full" data-testid="email-body-modal">
      <header class="px-5 py-4 border-b border-border-muted">
        <h2 class="text-lg font-bold text-text-default">El correo como salió</h2>
        <p v-if="entry" class="text-sm text-text-muted mt-1">
          {{ entry.subject || 'Sin asunto' }} · {{ entry.recipient }}
        </p>
      </header>

      <div class="flex-1 overflow-auto p-5">
        <p v-if="isLoading" class="text-sm text-text-subtle text-center py-10">
          Cargando el correo...
        </p>
        <p
          v-else-if="error"
          class="text-sm text-danger-strong text-center py-10"
          data-testid="email-body-error"
        >
          {{ error }}
        </p>
        <!-- Rendered in a sandboxed iframe with srcdoc, the same way the
             composer previews a branded email: the stored HTML is a document,
             not a fragment, and it must not touch the panel's own styles. -->
        <iframe
          v-else-if="html"
          :srcdoc="html"
          sandbox="allow-same-origin"
          title="Contenido del correo"
          class="w-full h-[60vh] bg-surface border border-border-muted rounded-lg"
          data-testid="email-body-frame"
        />
        <pre
          v-else
          class="whitespace-pre-wrap text-sm text-text-default"
          data-testid="email-body-text"
        >{{ text }}</pre>
      </div>

      <footer class="px-5 py-3 border-t border-border-muted flex justify-end">
        <BaseButton variant="secondary" size="sm" @click="emit('close')">
          Cerrar
        </BaseButton>
      </footer>
    </div>
  </BaseModal>
</template>

<script setup>
import { ref, watch } from 'vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import { useAccountingStore } from '~/stores/accounting';

const props = defineProps({
  open: { type: Boolean, default: false },
  /** The row being inspected; only its id is used to fetch. */
  entry: { type: Object, default: null },
});

const emit = defineEmits(['close']);

const store = useAccountingStore();
const isLoading = ref(false);
const error = ref('');
const html = ref('');
const text = ref('');

async function load(id) {
  isLoading.value = true;
  error.value = '';
  html.value = '';
  text.value = '';
  const result = await store.fetchEmailBody(id);
  if (result.success) {
    html.value = result.data.html || '';
    text.value = result.data.text || '';
  } else {
    error.value = result.message || 'No se pudo cargar el correo.';
  }
  isLoading.value = false;
}

watch(
  () => [props.open, props.entry?.id],
  ([isOpen, id]) => {
    if (isOpen && id) load(id);
  },
  { immediate: true },
);
</script>
