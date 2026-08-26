<template>
  <BaseModal
    :model-value="modelValue"
    size="lg"
    initial-focus="#document-client-note-subject"
    @update:model-value="updateOpenState"
  >
    <div class="space-y-6 p-6" data-testid="document-client-note-modal">
      <div>
        <h3 class="text-base font-semibold text-text-default">Notas</h3>
        <p class="mt-1 text-xs text-text-muted">
          Guarda textos listos para usar y observaciones privadas. No aparecen en el PDF ni en el portal del cliente.
        </p>
      </div>

      <section class="space-y-5" aria-labelledby="document-client-messages-heading">
        <h4 id="document-client-messages-heading" class="text-xs font-semibold uppercase tracking-wide text-text-muted">
          Mensajes para el cliente
        </h4>

        <div class="space-y-1.5">
          <div class="flex items-center justify-between gap-3">
            <label for="document-client-note-subject" class="text-sm font-medium text-text-default">Asunto del correo</label>
            <BaseActionButton
              action="copy"
              type="button"
              variant="ghost"
              size="sm"
              :label="copyLabel('subject', 'asunto')"
              :status-label="copyStatus('subject', 'asunto')"
              :disabled="isBusy || !draft.subject.trim()"
              data-testid="client-note-copy-subject"
              @click="copyText('subject', draft.subject)"
            />
          </div>
          <BaseInput
            id="document-client-note-subject"
            v-model="draft.subject"
            :disabled="readonly || isBusy"
            maxlength="255"
            placeholder="Asunto breve y concreto"
            data-testid="client-note-subject"
          />
        </div>

        <div class="space-y-1.5">
          <div class="flex items-center justify-between gap-3">
            <label for="document-client-note-email" class="text-sm font-medium text-text-default">Correo</label>
            <BaseActionButton
              action="copy"
              type="button"
              variant="ghost"
              size="sm"
              :label="copyLabel('email', 'correo')"
              :status-label="copyStatus('email', 'correo')"
              :disabled="isBusy || !draft.emailBody.trim()"
              data-testid="client-note-copy-email"
              @click="copyText('email', draft.emailBody)"
            />
          </div>
          <BaseTextarea
            id="document-client-note-email"
            v-model="draft.emailBody"
            :disabled="readonly || isBusy"
            rows="9"
            placeholder="Saludo, contenido y cierre del correo…"
            data-testid="client-note-email"
          />
        </div>

        <div class="space-y-1.5">
          <div class="flex items-center justify-between gap-3">
            <label for="document-client-note-whatsapp" class="text-sm font-medium text-text-default">WhatsApp</label>
            <BaseActionButton
              action="copy"
              type="button"
              variant="ghost"
              size="sm"
              :label="copyLabel('whatsapp', 'WhatsApp')"
              :status-label="copyStatus('whatsapp', 'WhatsApp')"
              :disabled="isBusy || !draft.whatsappMessage.trim()"
              data-testid="client-note-copy-whatsapp"
              @click="copyText('whatsapp', draft.whatsappMessage)"
            />
          </div>
          <BaseTextarea
            id="document-client-note-whatsapp"
            v-model="draft.whatsappMessage"
            :disabled="readonly || isBusy"
            rows="5"
            placeholder="Mensaje breve que invita a revisar el correo…"
            data-testid="client-note-whatsapp"
          />
        </div>
      </section>

      <section
        v-if="!documentId"
        class="space-y-3 border-t border-border-muted pt-5"
        aria-labelledby="document-custom-notes-heading"
      >
        <div class="flex items-center justify-between gap-3">
          <div>
            <h4 id="document-custom-notes-heading" class="text-sm font-semibold text-text-default">Notas adicionales</h4>
            <p class="mt-0.5 text-xs text-text-subtle">Agrega títulos y contenidos personalizados.</p>
          </div>
          <BaseButton
            v-if="!readonly"
            type="button"
            variant="secondary"
            size="sm"
            :disabled="isBusy"
            data-testid="client-note-add-custom"
            @click="addCustomNote"
          >
            <BaseActionIcon action="create" />
            Agregar nota
          </BaseButton>
        </div>

        <p v-if="!draft.customNotes.length" class="rounded-xl border border-dashed border-border-default bg-surface-raised px-4 py-3 text-sm text-text-subtle" data-testid="client-note-custom-empty">
          Aún no hay notas adicionales.
        </p>

        <article
          v-for="(note, index) in draft.customNotes"
          :key="note.key"
          class="space-y-3 rounded-xl border border-border-default bg-surface-raised p-4"
          :data-testid="`client-note-custom-${index}`"
        >
          <div class="flex items-center justify-between gap-3">
            <p class="text-xs font-semibold uppercase tracking-wide text-text-muted">Nota {{ index + 1 }}</p>
            <BaseActionButton
              v-if="!readonly"
              action="delete"
              type="button"
              variant="danger-ghost"
              size="sm"
              :label="`Eliminar nota ${index + 1}`"
              :disabled="isBusy"
              :data-testid="`client-note-custom-delete-${index}`"
              @click="removeCustomNote(index)"
            />
          </div>

          <div class="space-y-1.5">
            <div class="flex items-center justify-between gap-3">
              <label :for="`document-custom-note-title-${index}`" class="text-sm font-medium text-text-default">Título</label>
              <BaseActionButton
                action="copy"
                type="button"
                variant="ghost"
                size="sm"
                :label="copyLabel(`custom-title-${note.key}`, `título de la nota ${index + 1}`)"
                :status-label="copyStatus(`custom-title-${note.key}`, `título de la nota ${index + 1}`)"
                :disabled="isBusy || !note.title.trim()"
                :data-testid="`client-note-custom-copy-title-${index}`"
                @click="copyText(`custom-title-${note.key}`, note.title)"
              />
            </div>
            <BaseInput
              :id="`document-custom-note-title-${index}`"
              v-model="note.title"
              :disabled="readonly || isBusy"
              :error="validationAttempted && !note.title.trim()"
              maxlength="255"
              placeholder="Ej. Contexto para seguimiento"
              :data-testid="`client-note-custom-title-${index}`"
            />
            <p v-if="validationAttempted && !note.title.trim()" class="text-xs text-danger-strong" :data-testid="`client-note-custom-title-error-${index}`">
              El título es obligatorio.
            </p>
          </div>

          <div class="space-y-1.5">
            <div class="flex items-center justify-between gap-3">
              <label :for="`document-custom-note-content-${index}`" class="text-sm font-medium text-text-default">Contenido</label>
              <BaseActionButton
                action="copy"
                type="button"
                variant="ghost"
                size="sm"
                :label="copyLabel(`custom-content-${note.key}`, `contenido de la nota ${index + 1}`)"
                :status-label="copyStatus(`custom-content-${note.key}`, `contenido de la nota ${index + 1}`)"
                :disabled="isBusy || !note.content.trim()"
                :data-testid="`client-note-custom-copy-content-${index}`"
                @click="copyText(`custom-content-${note.key}`, note.content)"
              />
            </div>
            <BaseTextarea
              :id="`document-custom-note-content-${index}`"
              v-model="note.content"
              :disabled="readonly || isBusy"
              :error="validationAttempted && !note.content.trim()"
              rows="5"
              placeholder="Escribe el contenido de la nota…"
              :data-testid="`client-note-custom-content-${index}`"
            />
            <p v-if="validationAttempted && !note.content.trim()" class="text-xs text-danger-strong" :data-testid="`client-note-custom-content-error-${index}`">
              El contenido es obligatorio.
            </p>
          </div>
        </article>
      </section>

      <DocumentObservationManager
        v-else
        :key="`${documentId}-${modelValue}`"
        :document-id="documentId"
        :notes="localNotes"
        :readonly="readonly"
        class="border-t border-border-muted pt-5"
        @update:notes="localNotes = $event"
        @workflow-changed="emit('workflow-changed')"
        @busy-change="observationBusy = $event"
      />

      <p
        v-if="mode === 'draft' && !readonly"
        class="rounded-xl border border-warning-soft bg-warning-soft px-4 py-3 text-sm text-warning-strong"
        data-testid="client-note-draft-hint"
      >
        Estas notas se aplicarán al borrador. Quedarán guardadas cuando crees el documento.
      </p>

      <div class="flex justify-end gap-2 pt-1">
        <BaseButton type="button" variant="ghost" :disabled="isBusy" data-testid="client-note-cancel" @click="close">
          {{ readonly ? 'Cerrar' : 'Cancelar' }}
        </BaseButton>
        <BaseButton v-if="!readonly" type="button" variant="primary" :disabled="isBusy" :loading="saving" data-testid="client-note-submit" @click="submit">
          {{ mode === 'draft' ? 'Aplicar al borrador' : 'Guardar cambios' }}
        </BaseButton>
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import DocumentObservationManager from '~/components/panel/documents/DocumentObservationManager.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  subject: { type: String, default: '' },
  emailBody: { type: String, default: '' },
  whatsappMessage: { type: String, default: '' },
  customNotes: { type: Array, default: () => [] },
  documentId: { type: [Number, String], default: null },
  notes: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
  mode: {
    type: String,
    default: 'save',
    validator: (value) => ['save', 'draft'].includes(value),
  },
  saving: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue', 'submit', 'workflow-changed']);
const notify = usePanelNotify();
const copiedField = ref('');
const validationAttempted = ref(false);
const observationBusy = ref(false);
const localNotes = ref([]);
const isBusy = computed(() => props.saving || observationBusy.value);
const draft = reactive({ subject: '', emailBody: '', whatsappMessage: '', customNotes: [] });
let nextCustomNoteKey = 0;

function makeDraftNote(note = {}) {
  nextCustomNoteKey += 1;
  return {
    key: nextCustomNoteKey,
    title: typeof note.title === 'string' ? note.title : '',
    content: typeof note.content === 'string' ? note.content : '',
  };
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return;
    draft.subject = props.subject;
    draft.emailBody = props.emailBody;
    draft.whatsappMessage = props.whatsappMessage;
    draft.customNotes = props.customNotes.map(makeDraftNote);
    localNotes.value = props.notes.map((note) => ({ ...note }));
    copiedField.value = '';
    validationAttempted.value = false;
    observationBusy.value = false;
  },
  { immediate: true },
);

watch(
  () => props.notes,
  (notes) => { localNotes.value = notes.map((note) => ({ ...note })); },
  { deep: true },
);

function updateOpenState(open) {
  if (!open && isBusy.value) return;
  emit('update:modelValue', open);
}

function close() {
  if (isBusy.value) return;
  emit('update:modelValue', false);
}

function addCustomNote() {
  draft.customNotes.push(makeDraftNote());
}

function removeCustomNote(index) {
  draft.customNotes.splice(index, 1);
}

function submit() {
  validationAttempted.value = true;
  if (draft.customNotes.some((note) => !note.title.trim() || !note.content.trim())) return;
  emit('submit', {
    subject: draft.subject.trim(),
    emailBody: draft.emailBody.trim(),
    whatsappMessage: draft.whatsappMessage.trim(),
    customNotes: draft.customNotes.map((note) => ({
      title: note.title.trim(),
      content: note.content.trim(),
    })),
  });
}

function copyLabel(field, label) {
  return copiedField.value === field ? `Copiado: ${label}` : `Copiar ${label}`;
}

function copyStatus(field, label) {
  return copiedField.value === field ? `Copiado: ${label}` : '';
}

async function copyText(field, value) {
  try {
    await navigator.clipboard.writeText(value);
    copiedField.value = field;
  } catch {
    notify.error({
      title: 'No se pudo copiar al portapapeles',
      detail: 'Tu navegador bloqueó el acceso al portapapeles.',
    });
  }
}
</script>
