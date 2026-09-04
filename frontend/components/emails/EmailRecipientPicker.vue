<template>
  <BaseFormField
    :label="label"
    :for="inputId"
    :required="required"
    :error="localError"
    standalone
  >
    <div ref="ownerRef" class="relative space-y-2">
      <div
        class="flex min-h-11 flex-wrap items-center gap-2 rounded-xl border border-input-border bg-input-bg px-2 py-1.5 focus-within:border-focus-ring focus-within:ring-2 focus-within:ring-focus-ring/30"
        :data-testid="`${testId}-field`"
      >
        <span
          v-for="recipient in normalizedRecipients"
          :key="recipient.email"
          class="inline-flex min-w-0 max-w-full items-center gap-1.5 rounded-lg bg-primary-soft px-2 py-1 text-xs text-text-brand"
        >
          <span class="min-w-0 truncate">
            {{ recipient.name ? `${recipient.name} · ${recipient.email}` : recipient.email }}
          </span>
          <BaseButton
            unstyled
            icon-only
            type="button"
            :aria-label="`Quitar ${recipient.email}`"
            :title="`Quitar ${recipient.email}`"
            :data-testid="`${testId}-remove-${recipient.email}`"
            @click="removeRecipient(recipient.email)"
          >
            <BaseActionIcon action="close" class="size-3" />
          </BaseButton>
        </span>

        <input
          :id="inputId"
          ref="inputRef"
          v-model="draft"
          type="text"
          autocomplete="off"
          :placeholder="normalizedRecipients.length ? 'Agregar otro correo…' : placeholder"
          class="min-w-48 flex-1 border-0 bg-transparent px-1 py-1.5 text-sm text-input-text outline-none placeholder:text-text-subtle"
          role="combobox"
          :aria-expanded="showResults"
          :aria-controls="listboxId"
          :aria-invalid="localError ? 'true' : undefined"
          :data-testid="testId"
          @input="handleInput"
          @focus="handleFocus"
          @blur="addDraft"
          @keydown="handleKeydown"
          @paste="handlePaste"
        />
        <BaseButton
          type="button"
          variant="ghost"
          size="sm"
          :disabled="!draft.trim()"
          :title="draft.trim() ? 'Agregar correo' : 'Escribe un correo para agregarlo'"
          :data-testid="`${testId}-add`"
          @click="addDraft"
        >
          Agregar
        </BaseButton>
      </div>

      <p class="text-[11px] text-text-subtle">
        Busca un cliente o escribe un correo. Enter, coma y punto y coma agregan direcciones.
      </p>

      <BaseFloatingListbox
        :id="listboxId"
        :open="showResults"
        :anchor="inputRef"
        :owner="ownerRef"
        :max-height="260"
        @close="showResults = false"
      >
        <p v-if="isSearching" class="px-3 py-3 text-xs text-text-subtle">Buscando clientes…</p>
        <p v-else-if="searchFailed" class="px-3 py-3 text-xs text-danger-strong">No se pudieron buscar clientes.</p>
        <p v-else-if="!results.length" class="px-3 py-3 text-xs text-text-subtle">
          No hay clientes coincidentes. Puedes agregar el correo manualmente.
        </p>
        <template v-else>
          <!-- design-tokens: allow-raw-button — each row is a listbox option. -->
          <button
            v-for="client in results"
            :key="client.id"
            type="button"
            role="option"
            class="flex w-full items-start justify-between gap-3 px-3 py-2.5 text-left hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="client.is_email_placeholder || isUnavailable(client.email)"
            :aria-selected="hasEmail(client.email)"
            :title="unavailableTitle(client)"
            :data-testid="`${testId}-client-${client.id}`"
            @click="addClient(client)"
          >
            <span class="min-w-0">
              <span class="block truncate text-sm font-medium text-text-default">{{ client.name }}</span>
              <span class="block truncate text-xs text-text-muted">{{ client.email }}</span>
              <span v-if="client.company" class="block truncate text-[11px] text-text-subtle">{{ client.company }}</span>
            </span>
            <span v-if="client.is_email_placeholder" class="text-[10px] text-warning-strong">Sin correo real</span>
            <span v-else-if="hasEmail(client.email)" class="text-[10px] text-success-strong">Agregado</span>
            <span v-else-if="isExcluded(client.email)" class="text-[10px] text-warning-strong">Ya está en otro campo</span>
          </button>
        </template>
      </BaseFloatingListbox>
    </div>
  </BaseFormField>
</template>

<script setup>
import { computed, ref, useId } from 'vue';
import { useDebounceFn } from '@vueuse/core';
import BaseFloatingListbox from '~/components/base/BaseFloatingListbox.vue';
import { useProposalClientsStore } from '~/stores/proposal_clients';
import { emailRecipient, recipientEmails } from '~/utils/emailRecipients';

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: { type: String, required: true },
  placeholder: { type: String, default: 'correo@ejemplo.com' },
  required: { type: Boolean, default: false },
  excludedEmails: { type: Array, default: () => [] },
  totalCount: { type: Number, default: 0 },
  maxTotal: { type: Number, default: 10 },
  testId: { type: String, required: true },
});

const emit = defineEmits(['update:modelValue']);
const clientsStore = useProposalClientsStore();
const ownerRef = ref(null);
const inputRef = ref(null);
const draft = ref('');
const results = ref([]);
const isSearching = ref(false);
const searchFailed = ref(false);
const showResults = ref(false);
const localError = ref('');
const inputId = `${useId()}-${props.testId}`;
const listboxId = `${inputId}-listbox`;

const normalizedRecipients = computed(() => (props.modelValue || []).map((item) => (
  typeof item === 'string' ? emailRecipient(item) : item
)));
const currentEmails = computed(() => new Set(recipientEmails(normalizedRecipients.value)));
const excluded = computed(() => new Set(
  props.excludedEmails.map((email) => String(email || '').trim().toLowerCase()),
));

function hasEmail(email) {
  return currentEmails.value.has(String(email || '').trim().toLowerCase());
}

function isExcluded(email) {
  return excluded.value.has(String(email || '').trim().toLowerCase());
}

function isUnavailable(email) {
  return hasEmail(email) || isExcluded(email) || props.totalCount >= props.maxTotal;
}

function unavailableTitle(client) {
  if (client.is_email_placeholder) return 'Este cliente no tiene un correo real.';
  if (hasEmail(client.email)) return 'Este correo ya está agregado.';
  if (isExcluded(client.email)) return 'Este correo ya está agregado en otro campo.';
  if (props.totalCount >= props.maxTotal) {
    return `Se alcanzó el máximo de ${props.maxTotal} destinatarios.`;
  }
  return `Agregar ${client.email}`;
}

function validEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function addEntries(entries) {
  const nextRecipients = [...normalizedRecipients.value];
  const knownEmails = new Set(currentEmails.value);
  let validationError = '';

  for (const entry of entries) {
    const email = String(entry.email || '').trim().toLowerCase();
    if (!validEmail(email)) {
      validationError = `El correo "${entry.email || ''}" no es válido.`;
      continue;
    }
    if (email.endsWith('@temp.example.com')) {
      validationError = 'Los correos temporales de clientes no pueden recibir mensajes.';
      continue;
    }
    if (knownEmails.has(email)) {
      validationError = `${email} ya está agregado en ${props.label}.`;
      continue;
    }
    if (excluded.value.has(email)) {
      validationError = `${email} ya está agregado en otro campo.`;
      continue;
    }
    if (props.totalCount + nextRecipients.length - normalizedRecipients.value.length >= props.maxTotal) {
      validationError = `Puedes agregar máximo ${props.maxTotal} destinatarios entre Para y CC.`;
      break;
    }
    knownEmails.add(email);
    nextRecipients.push({ ...entry, email });
  }

  const added = nextRecipients.length > normalizedRecipients.value.length;
  if (added) emit('update:modelValue', nextRecipients);
  localError.value = validationError;
  return added;
}

function addEntry(entry) {
  return addEntries([entry]);
}

function addDraft() {
  const values = draft.value.split(/[;,\n]+/).map((value) => value.trim()).filter(Boolean);
  if (!values.length) return;
  const added = addEntries(values.map((email) => emailRecipient(email)));
  if (added) {
    draft.value = '';
    showResults.value = false;
  }
}

function addClient(client) {
  if (client.is_email_placeholder || isUnavailable(client.email)) return;
  if (addEntry(emailRecipient(client.email, { name: client.name, clientId: client.id }))) {
    draft.value = '';
    showResults.value = false;
    inputRef.value?.focus();
  }
}

function removeRecipient(email) {
  emit(
    'update:modelValue',
    normalizedRecipients.value.filter((recipient) => recipient.email !== email),
  );
  localError.value = '';
}

function removeLastWhenEmpty(event) {
  if (draft.value || !normalizedRecipients.value.length) return;
  event.preventDefault();
  removeRecipient(normalizedRecipients.value.at(-1).email);
}

function handleKeydown(event) {
  if (event.key === 'Backspace') {
    removeLastWhenEmpty(event);
    return;
  }
  if (!['Enter', ',', ';'].includes(event.key)) return;
  event.preventDefault();
  addDraft();
}

function handlePaste(event) {
  const pasted = event.clipboardData?.getData('text') || '';
  if (!/[;,\n]/.test(pasted)) return;
  event.preventDefault();
  draft.value = pasted;
  addDraft();
}

async function runSearch(query) {
  if (!query) {
    results.value = [];
    showResults.value = false;
    return;
  }
  isSearching.value = true;
  searchFailed.value = false;
  showResults.value = true;
  const result = await clientsStore.searchClients(query, { limit: 10 });
  isSearching.value = false;
  if (result?.cancelled) return;
  if (!result?.success) {
    searchFailed.value = true;
    results.value = [];
    return;
  }
  results.value = result.data || [];
}

const debouncedSearch = useDebounceFn(runSearch, 200);

function handleInput() {
  localError.value = '';
  debouncedSearch(draft.value.trim());
}

function handleFocus() {
  if (draft.value.trim()) runSearch(draft.value.trim());
}
</script>
