<template>
  <BaseModal
    :model-value="modelValue"
    size="lg"
    initial-focus="#document-client-note-subject"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <form class="p-6 space-y-6" data-testid="document-client-note-modal" @submit.prevent="apply">
      <div>
        <h3 class="text-base font-semibold text-text-default">Notas</h3>
        <p class="text-xs text-text-muted mt-1">
          Guarda textos listos para usar y notas adicionales. Son privadas y no aparecen en el PDF ni en el portal del cliente.
        </p>
      </div>

      <section class="space-y-5" aria-labelledby="document-client-messages-heading">
        <h4 id="document-client-messages-heading" class="text-xs uppercase tracking-wide font-semibold text-text-muted">
          Mensajes para el cliente
        </h4>

        <div class="space-y-1.5">
          <div class="flex items-center justify-between gap-3">
            <label for="document-client-note-subject" class="text-sm font-medium text-text-default">
              Asunto del correo
            </label>
            <BaseButton
              type="button"
              variant="ghost"
              size="sm"
              icon-only
              :aria-label="copyLabel('subject', 'asunto')"
              :title="copyLabel('subject', 'asunto')"
              :disabled="!draft.subject.trim()"
              data-testid="client-note-copy-subject"
              @click="copyText('subject', draft.subject)"
            >
              <span aria-hidden="true">{{ copyEmoji('subject') }}</span>
            </BaseButton>
          </div>
          <BaseInput
            id="document-client-note-subject"
            v-model="draft.subject"
            :disabled="readonly"
            maxlength="255"
            placeholder="Asunto breve y concreto"
            data-testid="client-note-subject"
          />
        </div>

        <div class="space-y-1.5">
          <div class="flex items-center justify-between gap-3">
            <label for="document-client-note-email" class="text-sm font-medium text-text-default">
              Correo
            </label>
            <BaseButton
              type="button"
              variant="ghost"
              size="sm"
              icon-only
              :aria-label="copyLabel('email', 'correo')"
              :title="copyLabel('email', 'correo')"
              :disabled="!draft.emailBody.trim()"
              data-testid="client-note-copy-email"
              @click="copyText('email', draft.emailBody)"
            >
              <span aria-hidden="true">{{ copyEmoji('email') }}</span>
            </BaseButton>
          </div>
          <BaseTextarea
            id="document-client-note-email"
            v-model="draft.emailBody"
            :disabled="readonly"
            rows="9"
            placeholder="Saludo, contenido y cierre del correo..."
            data-testid="client-note-email"
          />
        </div>

        <div class="space-y-1.5">
          <div class="flex items-center justify-between gap-3">
            <label for="document-client-note-whatsapp" class="text-sm font-medium text-text-default">
              WhatsApp
            </label>
            <BaseButton
              type="button"
              variant="ghost"
              size="sm"
              icon-only
              :aria-label="copyLabel('whatsapp', 'WhatsApp')"
              :title="copyLabel('whatsapp', 'WhatsApp')"
              :disabled="!draft.whatsappMessage.trim()"
              data-testid="client-note-copy-whatsapp"
              @click="copyText('whatsapp', draft.whatsappMessage)"
            >
              <span aria-hidden="true">{{ copyEmoji('whatsapp') }}</span>
            </BaseButton>
          </div>
          <BaseTextarea
            id="document-client-note-whatsapp"
            v-model="draft.whatsappMessage"
            :disabled="readonly"
            rows="5"
            placeholder="Mensaje breve que invita a revisar el correo..."
            data-testid="client-note-whatsapp"
          />
        </div>
      </section>

      <section v-if="!documentId || (!notes.length && customNotes.length)" class="space-y-3 border-t border-border-muted pt-5" aria-labelledby="document-custom-notes-heading">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h4 id="document-custom-notes-heading" class="text-sm font-semibold text-text-default">
              Notas adicionales
            </h4>
            <p class="text-xs text-text-subtle mt-0.5">Agrega títulos y contenidos personalizados.</p>
          </div>
          <BaseButton
            v-if="!readonly"
            type="button"
            variant="secondary"
            size="sm"
            data-testid="client-note-add-custom"
            @click="addCustomNote"
          >
            + Agregar nota
          </BaseButton>
        </div>

        <p
          v-if="!draft.customNotes.length"
          class="rounded-xl border border-dashed border-border-default bg-surface-raised px-4 py-3 text-sm text-text-subtle"
          data-testid="client-note-custom-empty"
        >
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
            <BaseButton
              v-if="!readonly"
              type="button"
              variant="danger-ghost"
              size="sm"
              icon-only
              :aria-label="`Eliminar nota ${index + 1}`"
              :title="`Eliminar nota ${index + 1}`"
              :data-testid="`client-note-custom-delete-${index}`"
              @click="removeCustomNote(index)"
            >
              <TrashIcon class="w-4 h-4" />
            </BaseButton>
          </div>

          <div class="space-y-1.5">
            <div class="flex items-center justify-between gap-3">
              <label :for="`document-custom-note-title-${index}`" class="text-sm font-medium text-text-default">
                Título
              </label>
              <BaseButton
                type="button"
                variant="ghost"
                size="sm"
                icon-only
                :aria-label="copyLabel(`custom-title-${note.key}`, `título de la nota ${index + 1}`)"
                :title="copyLabel(`custom-title-${note.key}`, `título de la nota ${index + 1}`)"
                :disabled="!note.title.trim()"
                :data-testid="`client-note-custom-copy-title-${index}`"
                @click="copyText(`custom-title-${note.key}`, note.title)"
              >
                <span aria-hidden="true">{{ copyEmoji(`custom-title-${note.key}`) }}</span>
              </BaseButton>
            </div>
            <BaseInput
              :id="`document-custom-note-title-${index}`"
              v-model="note.title"
              :disabled="readonly"
              :error="validationAttempted && !note.title.trim()"
              maxlength="255"
              placeholder="Ej. Contexto para seguimiento"
              :data-testid="`client-note-custom-title-${index}`"
            />
            <p
              v-if="validationAttempted && !note.title.trim()"
              class="text-xs text-danger-strong"
              :data-testid="`client-note-custom-title-error-${index}`"
            >
              El título es obligatorio.
            </p>
          </div>

          <div class="space-y-1.5">
            <div class="flex items-center justify-between gap-3">
              <label :for="`document-custom-note-content-${index}`" class="text-sm font-medium text-text-default">
                Contenido
              </label>
              <BaseButton
                type="button"
                variant="ghost"
                size="sm"
                icon-only
                :aria-label="copyLabel(`custom-content-${note.key}`, `contenido de la nota ${index + 1}`)"
                :title="copyLabel(`custom-content-${note.key}`, `contenido de la nota ${index + 1}`)"
                :disabled="!note.content.trim()"
                :data-testid="`client-note-custom-copy-content-${index}`"
                @click="copyText(`custom-content-${note.key}`, note.content)"
              >
                <span aria-hidden="true">{{ copyEmoji(`custom-content-${note.key}`) }}</span>
              </BaseButton>
            </div>
            <BaseTextarea
              :id="`document-custom-note-content-${index}`"
              v-model="note.content"
              :disabled="readonly"
              :error="validationAttempted && !note.content.trim()"
              rows="5"
              placeholder="Escribe el contenido de la nota..."
              :data-testid="`client-note-custom-content-${index}`"
            />
            <p
              v-if="validationAttempted && !note.content.trim()"
              class="text-xs text-danger-strong"
              :data-testid="`client-note-custom-content-error-${index}`"
            >
              El contenido es obligatorio.
            </p>
          </div>
        </article>
      </section>

      <section v-else class="space-y-4 border-t border-border-muted pt-5" aria-labelledby="document-observations-heading">
        <div>
          <h4 id="document-observations-heading" class="text-sm font-semibold text-text-default">
            Observaciones del documento
          </h4>
          <p class="mt-0.5 text-xs text-text-subtle">
            Cada observación queda en el historial y puede abrir la señal Solucionar bug.
          </p>
        </div>

        <div v-if="localNotes.length" class="space-y-2" data-testid="document-observation-list">
          <article
            v-for="note in localNotes"
            :key="note.id"
            class="rounded-xl border border-border-default bg-surface-raised p-3"
          >
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="text-sm font-medium text-text-default">{{ note.title || 'Observación' }}</p>
                <p class="mt-1 whitespace-pre-wrap text-sm text-text-muted">{{ note.content }}</p>
              </div>
              <BaseBadge :variant="note.status === 'open' ? 'warning' : 'neutral'" size="sm">
                {{ noteStatusLabel(note.status) }}
              </BaseBadge>
            </div>
            <div class="mt-2 flex justify-end">
              <BaseButton
                type="button"
                variant="ghost"
                size="sm"
                :aria-label="copyLabel(`observation-${note.id}`, `observación ${note.title || note.id}`)"
                :data-testid="`document-observation-copy-${note.id}`"
                @click="copyText(`observation-${note.id}`, note.content)"
              >
                {{ copyEmoji(`observation-${note.id}`) }} Copiar
              </BaseButton>
            </div>
            <p v-if="note.resolution_note" class="mt-2 text-xs text-text-subtle">
              Cierre: {{ note.resolution_note }}
            </p>
            <div v-if="note.status === 'open' && !readonly" class="mt-3 flex flex-wrap justify-end gap-2">
              <BaseButton type="button" variant="ghost" size="sm" :data-testid="`document-observation-edit-${note.id}`" @click="editObservation(note)">Editar</BaseButton>
              <BaseButton type="button" variant="danger-ghost" size="sm" :data-testid="`document-observation-discard-${note.id}`" @click="finishObservation(note, 'discarded')">Descartar</BaseButton>
              <BaseButton type="button" variant="secondary" size="sm" :data-testid="`document-observation-resolve-${note.id}`" @click="finishObservation(note, 'resolved')">Resolver</BaseButton>
            </div>
          </article>
        </div>
        <p v-else class="rounded-xl border border-dashed border-border-default px-4 py-3 text-sm text-text-subtle">
          Aún no hay observaciones.
        </p>

        <div v-if="!readonly" class="space-y-3 rounded-xl border border-border-default bg-surface p-4">
          <p class="text-xs font-semibold uppercase tracking-wide text-text-muted">Nueva observación</p>
          <BaseInput
            v-model="observationDraft.title"
            maxlength="120"
            placeholder="Título breve (opcional)"
            data-testid="document-observation-title"
          />
          <BaseTextarea
            v-model="observationDraft.content"
            rows="4"
            placeholder="Describe la observación…"
            data-testid="document-observation-content"
          />
          <label class="flex items-center gap-2 text-sm text-text-muted">
            <BaseToggle v-model="observationDraft.markNeedsFix" size="sm" />
            Marcar también Solucionar bug
          </label>
          <div class="flex justify-end">
            <BaseButton
              type="button"
              variant="secondary"
              size="sm"
              :loading="observationBusy"
              :disabled="!observationDraft.content.trim()"
              data-testid="document-observation-add"
              @click="addObservation"
            >
              Agregar observación
            </BaseButton>
          </div>
        </div>
      </section>

      <div class="flex justify-end gap-2 pt-1">
        <BaseButton type="button" variant="ghost" data-testid="client-note-cancel" @click="close">
          {{ readonly ? 'Cerrar' : 'Cancelar' }}
        </BaseButton>
        <BaseButton
          v-if="!readonly"
          type="submit"
          variant="primary"
          data-testid="client-note-apply"
        >
          Aplicar al documento
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>

<script setup>
import { reactive, ref, watch } from 'vue';
import { TrashIcon } from '@heroicons/vue/24/outline';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useDocumentStateStore } from '~/stores/document_states';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  subject: { type: String, default: '' },
  emailBody: { type: String, default: '' },
  whatsappMessage: { type: String, default: '' },
  customNotes: { type: Array, default: () => [] },
  documentId: { type: [Number, String], default: null },
  notes: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue', 'apply', 'workflow-changed']);
const notify = usePanelNotify();
const stateStore = useDocumentStateStore();
const copiedField = ref('');
const validationAttempted = ref(false);
const observationBusy = ref(false);
const localNotes = ref([]);
const observationDraft = reactive({ title: '', content: '', markNeedsFix: true });
const draft = reactive({
  subject: '',
  emailBody: '',
  whatsappMessage: '',
  customNotes: [],
});
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
    observationDraft.title = '';
    observationDraft.content = '';
    observationDraft.markNeedsFix = true;
    copiedField.value = '';
    validationAttempted.value = false;
  },
  { immediate: true },
);

watch(
  () => props.notes,
  (notes) => { localNotes.value = notes.map((note) => ({ ...note })); },
  { deep: true },
);

function close() {
  emit('update:modelValue', false);
}

function addCustomNote() {
  draft.customNotes.push(makeDraftNote());
}

function removeCustomNote(index) {
  draft.customNotes.splice(index, 1);
}

function apply() {
  validationAttempted.value = true;
  if (draft.customNotes.some((note) => !note.title.trim() || !note.content.trim())) return;

  emit('apply', {
    subject: draft.subject.trim(),
    emailBody: draft.emailBody.trim(),
    whatsappMessage: draft.whatsappMessage.trim(),
    customNotes: draft.customNotes.map((note) => ({
      title: note.title.trim(),
      content: note.content.trim(),
    })),
  });
  close();
}

function copyEmoji(field) {
  return copiedField.value === field ? '✅' : '📋';
}

function copyLabel(field, label) {
  return copiedField.value === field ? `Copiado: ${label}` : `Copiar ${label}`;
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

function noteStatusLabel(status) {
  return { open: 'Pendiente', resolved: 'Resuelta', discarded: 'Descartada' }[status] || status;
}

async function addObservation() {
  if (!props.documentId || !observationDraft.content.trim() || observationBusy.value) return;
  observationBusy.value = true;
  const result = await stateStore.createNote(props.documentId, {
    title: observationDraft.title.trim(),
    content: observationDraft.content.trim(),
    mark_needs_fix: observationDraft.markNeedsFix,
  });
  observationBusy.value = false;
  if (!result.success) {
    notify.error({ title: 'No se pudo agregar la observación', detail: result.message });
    return;
  }
  localNotes.value.push(result.data);
  observationDraft.title = '';
  observationDraft.content = '';
  emit('workflow-changed');
}

async function editObservation(note) {
  const title = window.prompt('Título de la observación', note.title || '');
  if (title === null) return;
  const content = window.prompt('Contenido de la observación', note.content || '');
  if (content === null || !content.trim()) return;
  const result = await stateStore.updateNote(props.documentId, note.id, {
    title: title.trim(),
    content: content.trim(),
  });
  if (!result.success) {
    notify.error({ title: 'No se pudo editar la observación', detail: result.message });
    return;
  }
  Object.assign(note, result.data);
  emit('workflow-changed');
}

async function finishObservation(note, outcome) {
  const resolutionNote = window.prompt(
    outcome === 'resolved' ? '¿Qué se hizo? (opcional)' : '¿Por qué se descarta? (opcional)',
    '',
  );
  if (resolutionNote === null) return;

  const isLastForEpisode = note.episode && !localNotes.value.some(
    (candidate) => candidate.id !== note.id
      && candidate.status === 'open'
      && candidate.episode === note.episode,
  );
  const closeLinkedState = Boolean(isLastForEpisode) && window.confirm(
    outcome === 'resolved'
      ? '¿Cerrar también Solucionar bug?'
      : '¿Quitar también Solucionar bug porque la observación no aplicaba?',
  );
  const moveCycle = closeLinkedState
    && outcome === 'resolved'
    && window.confirm('¿Mover el ciclo del documento a Bug atendido?');

  const result = await stateStore.finishNote(props.documentId, note.id, {
    outcome,
    resolution_note: resolutionNote.trim(),
    close_linked_state: closeLinkedState,
    move_cycle_to_bug_attended: moveCycle,
  });
  if (!result.success) {
    notify.error({ title: 'No se pudo cerrar la observación', detail: result.message });
    return;
  }
  Object.assign(note, result.data.note);
  emit('workflow-changed');
}
</script>
