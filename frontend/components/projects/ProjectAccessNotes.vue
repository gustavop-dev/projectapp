<script setup>
import { onBeforeUnmount, reactive, ref, watch } from 'vue'
import { normalizeApiError } from '~/stores/services/normalize_api_error'
import { useClipboardFeedback } from '~/composables/useClipboardFeedback'

const props = defineProps({
  notes: { type: Array, default: () => [] },
  api: { type: Object, required: true },
  onUpdated: { type: Function, required: true },
})

const { t } = useI18n()
const showCreateForm = ref(false)
const isBusy = ref(false)
const errorMessage = ref('')
const createErrors = reactive({ title: '', content: '' })
const createDraft = reactive({ title: '', content: '', is_sensitive: false })
const editingNoteId = ref(null)
const editDraft = reactive({ title: '', content: '', is_sensitive: false })
const revealedNotes = reactive({})
const visibleNotes = reactive({})
const deleteTarget = ref(null)
const { copyText, feedbackFor, clearAllFeedback } = useClipboardFeedback()

function resetCreate() {
  createDraft.title = ''
  createDraft.content = ''
  createDraft.is_sensitive = false
  createErrors.title = ''
  createErrors.content = ''
  showCreateForm.value = false
}

function validateCreate() {
  createErrors.title = createDraft.title.trim()
    ? ''
    : t('projectAccess.errors.noteTitleRequired')
  createErrors.content = createDraft.content.trim()
    ? ''
    : t('projectAccess.errors.noteContentRequired')
  return !createErrors.title && !createErrors.content
}

async function createNote() {
  if (!validateCreate()) return
  isBusy.value = true
  errorMessage.value = ''
  try {
    const detail = await props.api.createNote({ ...createDraft })
    props.onUpdated(detail)
    resetCreate()
  } catch (error) {
    const normalized = normalizeApiError(error, t('projectAccess.errors.createNote'))
    createErrors.title = normalized.fieldErrors?.title || ''
    createErrors.content = normalized.fieldErrors?.content || ''
    errorMessage.value = normalized.message
  } finally {
    isBusy.value = false
  }
}

function clearNoteSecret(noteId) {
  delete revealedNotes[noteId]
  delete visibleNotes[noteId]
}

async function startEditing(note) {
  isBusy.value = true
  errorMessage.value = ''
  try {
    let content = note.content || ''
    if (note.is_sensitive) {
      content = (await props.api.revealNote(note.id)).secret
    }
    editingNoteId.value = note.id
    editDraft.title = note.title
    editDraft.content = content
    editDraft.is_sensitive = note.is_sensitive
  } catch (error) {
    errorMessage.value = normalizeApiError(error, t('projectAccess.errors.revealNote')).message
  } finally {
    isBusy.value = false
  }
}

function cancelEditing() {
  if (editingNoteId.value) clearNoteSecret(editingNoteId.value)
  editingNoteId.value = null
  editDraft.title = ''
  editDraft.content = ''
  editDraft.is_sensitive = false
  errorMessage.value = ''
}

async function updateNote(noteId) {
  if (!editDraft.title.trim()) {
    errorMessage.value = t('projectAccess.errors.noteTitleRequired')
    return
  }
  if (!editDraft.content.trim()) {
    errorMessage.value = t('projectAccess.errors.noteContentRequired')
    return
  }
  isBusy.value = true
  errorMessage.value = ''
  try {
    const detail = await props.api.updateNote(noteId, { ...editDraft })
    props.onUpdated(detail)
    cancelEditing()
  } catch (error) {
    errorMessage.value = normalizeApiError(error, t('projectAccess.errors.updateNote')).message
  } finally {
    editDraft.content = ''
    isBusy.value = false
  }
}

async function toggleNoteReveal(note) {
  if (visibleNotes[note.id]) {
    clearNoteSecret(note.id)
    return
  }
  isBusy.value = true
  errorMessage.value = ''
  try {
    revealedNotes[note.id] = (await props.api.revealNote(note.id)).secret
    visibleNotes[note.id] = true
  } catch (error) {
    errorMessage.value = normalizeApiError(error, t('projectAccess.errors.revealNote')).message
  } finally {
    isBusy.value = false
  }
}

async function copyNoteContent(note) {
  isBusy.value = true
  errorMessage.value = ''
  try {
    const content = note.is_sensitive
      ? (visibleNotes[note.id]
        ? revealedNotes[note.id]
        : (await props.api.revealNote(note.id)).secret)
      : note.content
    await copyText({
      key: `note-content-${note.id}`,
      text: content,
      successLabel: t('projectAccess.actions.copied'),
      errorLabel: t('projectAccess.errors.copy'),
    })
  } catch (error) {
    errorMessage.value = normalizeApiError(error, t('projectAccess.errors.copyNote')).message
  } finally {
    isBusy.value = false
  }
}

function copyNoteTitle(note) {
  return copyText({
    key: `note-title-${note.id}`,
    text: note.title,
    successLabel: t('projectAccess.actions.copied'),
    errorLabel: t('projectAccess.errors.copy'),
  })
}

async function deleteNote() {
  if (!deleteTarget.value) return
  isBusy.value = true
  errorMessage.value = ''
  const noteId = deleteTarget.value.id
  try {
    const detail = await props.api.deleteNote(noteId)
    props.onUpdated(detail)
    clearNoteSecret(noteId)
    deleteTarget.value = null
  } catch (error) {
    errorMessage.value = normalizeApiError(error, t('projectAccess.errors.deleteNote')).message
  } finally {
    isBusy.value = false
  }
}

watch(
  () => props.notes.map((note) => note.id),
  (noteIds) => {
    const current = new Set(noteIds)
    Object.keys(revealedNotes).forEach((noteId) => {
      if (!current.has(Number(noteId))) clearNoteSecret(noteId)
    })
  },
)

onBeforeUnmount(() => {
  Object.keys(revealedNotes).forEach(clearNoteSecret)
  editDraft.content = ''
  createDraft.content = ''
  clearAllFeedback()
})
</script>

<template>
  <section class="space-y-4" aria-labelledby="project-access-notes-heading">
    <div class="flex flex-col gap-3 panel-portrait:flex-row panel-portrait:items-center panel-portrait:justify-between">
      <div>
        <h3 id="project-access-notes-heading" class="text-base font-semibold text-text-default">
          {{ t('projectAccess.notes.title') }}
        </h3>
        <p class="mt-1 text-xs text-text-subtle">{{ t('projectAccess.notes.help') }}</p>
      </div>
      <BaseButton
        v-if="!showCreateForm"
        variant="secondary"
        size="sm"
        data-testid="project-access-add-note"
        @click="showCreateForm = true"
      >
        <BaseActionIcon action="create" />
        {{ t('projectAccess.actions.addNote') }}
      </BaseButton>
    </div>

    <BaseAlert v-if="errorMessage" variant="danger" data-testid="project-access-notes-error">
      {{ errorMessage }}
    </BaseAlert>

    <article
      v-if="showCreateForm"
      class="space-y-4 rounded-xl border border-border-default bg-surface-raised p-4"
      data-testid="project-access-note-create"
    >
      <div class="space-y-1.5">
        <label for="project-access-note-title" class="text-sm font-medium text-text-default">
          {{ t('projectAccess.fields.noteTitle') }}
        </label>
        <BaseInput
          id="project-access-note-title"
          v-model="createDraft.title"
          :error="Boolean(createErrors.title)"
          maxlength="255"
          :placeholder="t('projectAccess.placeholders.noteTitle')"
        />
        <p v-if="createErrors.title" class="text-xs text-danger-strong" role="alert">{{ createErrors.title }}</p>
      </div>
      <div class="space-y-1.5">
        <label for="project-access-note-content" class="text-sm font-medium text-text-default">
          {{ t('projectAccess.fields.noteContent') }}
        </label>
        <BaseTextarea
          id="project-access-note-content"
          v-model="createDraft.content"
          :error="Boolean(createErrors.content)"
          rows="4"
          maxlength="10000"
          :placeholder="t('projectAccess.placeholders.noteContent')"
        />
        <p v-if="createErrors.content" class="text-xs text-danger-strong" role="alert">{{ createErrors.content }}</p>
      </div>
      <label class="flex items-center justify-between gap-4 rounded-lg bg-surface-muted p-3 text-sm text-text-default">
        <span>
          <span class="block font-medium">{{ t('projectAccess.fields.sensitive') }}</span>
          <span class="block text-xs text-text-subtle">{{ t('projectAccess.notes.sensitiveHelp') }}</span>
        </span>
        <BaseToggle
          v-model="createDraft.is_sensitive"
          :aria-label="t('projectAccess.fields.sensitive')"
        />
      </label>
      <div class="flex justify-end gap-2">
        <BaseButton variant="ghost" size="sm" :disabled="isBusy" @click="resetCreate">
          {{ t('projectAccess.actions.cancel') }}
        </BaseButton>
        <BaseButton variant="primary" size="sm" :loading="isBusy" data-testid="project-access-create-note-save" @click="createNote">
          {{ t('projectAccess.actions.save') }}
        </BaseButton>
      </div>
    </article>

    <BaseEmptyState
      v-if="!notes.length && !showCreateForm"
      :title="t('projectAccess.notes.emptyTitle')"
      :description="t('projectAccess.notes.emptyDescription')"
      data-testid="project-access-notes-empty"
    />

    <div v-else class="space-y-3" data-testid="project-access-notes-list">
      <article
        v-for="note in notes"
        :key="note.id"
        class="space-y-3 rounded-xl border border-border-default bg-surface-raised p-4"
        :data-testid="`project-access-note-${note.id}`"
      >
        <template v-if="editingNoteId === note.id">
          <BaseInput v-model="editDraft.title" maxlength="255" :disabled="isBusy" />
          <BaseTextarea v-model="editDraft.content" rows="5" maxlength="10000" :disabled="isBusy" />
          <label class="flex items-center justify-between gap-4 rounded-lg bg-surface-muted p-3 text-sm text-text-default">
            <span>{{ t('projectAccess.fields.sensitive') }}</span>
            <BaseToggle v-model="editDraft.is_sensitive" :disabled="isBusy" :aria-label="t('projectAccess.fields.sensitive')" />
          </label>
          <div class="flex justify-end gap-2">
            <BaseButton variant="ghost" size="sm" :disabled="isBusy" @click="cancelEditing">
              {{ t('projectAccess.actions.cancel') }}
            </BaseButton>
            <BaseButton variant="primary" size="sm" :loading="isBusy" :data-testid="`project-access-note-save-${note.id}`" @click="updateNote(note.id)">
              {{ t('projectAccess.actions.save') }}
            </BaseButton>
          </div>
        </template>

        <template v-else>
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h4 class="break-words text-sm font-semibold text-text-default">{{ note.title }}</h4>
                <BaseBadge v-if="note.is_sensitive" variant="warning" size="sm">
                  {{ t('projectAccess.notes.sensitiveBadge') }}
                </BaseBadge>
              </div>
              <p class="mt-1 text-xs text-text-subtle">
                {{ t('projectAccess.notes.updatedBy', { name: note.updated_by || t('projectAccess.notes.unknownEditor') }) }}
              </p>
            </div>
            <div class="flex shrink-0 flex-wrap items-center justify-end gap-1">
              <BaseActionButton
                action="copy"
                :label="t('projectAccess.actions.copyNoteTitle')"
                :status-label="feedbackFor(`note-title-${note.id}`).label"
                :status-tone="feedbackFor(`note-title-${note.id}`).tone"
                @click="copyNoteTitle(note)"
              />
              <BaseActionButton
                action="edit"
                :label="t('projectAccess.actions.editNote')"
                :disabled="isBusy"
                :data-testid="`project-access-note-edit-${note.id}`"
                @click="startEditing(note)"
              />
              <BaseActionButton
                action="delete"
                variant="danger-ghost"
                :label="t('projectAccess.actions.deleteNote')"
                :disabled="isBusy"
                :data-testid="`project-access-note-delete-${note.id}`"
                @click="deleteTarget = note"
              />
            </div>
          </div>

          <div class="rounded-lg bg-surface-muted p-3">
            <p class="whitespace-pre-wrap break-words font-mono text-sm text-text-default" aria-live="polite">
              {{ note.is_sensitive && !visibleNotes[note.id] ? '••••••••••••' : (revealedNotes[note.id] || note.content) }}
            </p>
            <div class="mt-2 flex justify-end gap-1">
              <BaseActionButton
                action="copy"
                :label="t('projectAccess.actions.copyNoteContent')"
                :status-label="feedbackFor(`note-content-${note.id}`).label"
                :status-tone="feedbackFor(`note-content-${note.id}`).tone"
                :disabled="isBusy"
                :data-testid="`project-access-note-copy-${note.id}`"
                @click="copyNoteContent(note)"
              />
              <BaseActionButton
                v-if="note.is_sensitive"
                :action="visibleNotes[note.id] ? 'hide' : 'view'"
                :label="visibleNotes[note.id] ? t('projectAccess.actions.hide') : t('projectAccess.actions.reveal')"
                :disabled="isBusy"
                :data-testid="`project-access-note-reveal-${note.id}`"
                @click="toggleNoteReveal(note)"
              />
            </div>
          </div>
        </template>
      </article>
    </div>

    <ConfirmModal
      :model-value="Boolean(deleteTarget)"
      :title="t('projectAccess.confirm.deleteNoteTitle')"
      :message="t('projectAccess.confirm.deleteNoteMessage', { title: deleteTarget?.title || '' })"
      :confirm-text="t('projectAccess.actions.delete')"
      :cancel-text="t('projectAccess.actions.cancel')"
      :loading="isBusy"
      variant="danger"
      @update:model-value="(open) => { if (!open) deleteTarget = null }"
      @confirm="deleteNote"
    />
  </section>
</template>
