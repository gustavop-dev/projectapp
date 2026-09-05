<script setup>
import { ref, watch } from 'vue'
import { normalizeApiError } from '~/stores/services/normalize_api_error'
import { useClipboardFeedback } from '~/composables/useClipboardFeedback'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: String, default: '' },
  inputType: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  isUrl: { type: Boolean, default: false },
  fieldKey: { type: String, required: true },
  saveValue: { type: Function, required: true },
})

const { t } = useI18n()
const isEditing = ref(false)
const isSaving = ref(false)
const draft = ref(props.value || '')
const errorMessage = ref('')
const { copyText, feedbackFor } = useClipboardFeedback()

watch(() => props.value, (value) => {
  if (!isEditing.value) draft.value = value || ''
})

function startEditing() {
  draft.value = props.value || ''
  errorMessage.value = ''
  isEditing.value = true
}

function cancelEditing() {
  draft.value = props.value || ''
  errorMessage.value = ''
  isEditing.value = false
}

async function save() {
  isSaving.value = true
  errorMessage.value = ''
  try {
    await props.saveValue(draft.value)
    isEditing.value = false
  } catch (error) {
    const normalized = normalizeApiError(error, t('projectAccess.errors.save'))
    errorMessage.value = normalized.fieldErrors?.[props.fieldKey]
      || normalized.message
  } finally {
    isSaving.value = false
  }
}

function copyValue() {
  return copyText({
    key: props.fieldKey,
    text: props.value,
    successLabel: t('projectAccess.actions.copied'),
    errorLabel: t('projectAccess.errors.copy'),
  })
}
</script>

<template>
  <div class="space-y-2" :data-testid="`project-access-field-${fieldKey}`">
    <div class="flex items-center justify-between gap-3">
      <span class="text-xs font-semibold uppercase tracking-wide text-text-muted">
        {{ label }}
      </span>
      <div class="flex items-center gap-1">
        <BaseActionButton
          v-if="value && !isEditing"
          action="copy"
          :label="`${t('projectAccess.actions.copy')} ${label}`"
          :status-label="feedbackFor(fieldKey).label"
          :status-tone="feedbackFor(fieldKey).tone"
          :data-testid="`project-access-copy-${fieldKey}`"
          @click="copyValue"
        />
        <BaseActionButton
          v-if="!isEditing"
          action="edit"
          :label="`${t('projectAccess.actions.edit')} ${label}`"
          :data-testid="`project-access-edit-${fieldKey}`"
          @click="startEditing"
        />
      </div>
    </div>

    <template v-if="isEditing">
      <BaseInput
        v-model="draft"
        :type="inputType"
        :placeholder="placeholder"
        :error="Boolean(errorMessage)"
        :disabled="isSaving"
        :data-testid="`project-access-input-${fieldKey}`"
        @keydown.enter.prevent="save"
        @keydown.esc.prevent="cancelEditing"
      />
      <p v-if="errorMessage" class="text-xs text-danger-strong" role="alert">
        {{ errorMessage }}
      </p>
      <div class="flex justify-end gap-2">
        <BaseButton variant="ghost" size="sm" :disabled="isSaving" @click="cancelEditing">
          {{ t('projectAccess.actions.cancel') }}
        </BaseButton>
        <BaseButton
          variant="primary"
          size="sm"
          :loading="isSaving"
          :data-testid="`project-access-save-${fieldKey}`"
          @click="save"
        >
          {{ t('projectAccess.actions.save') }}
        </BaseButton>
      </div>
    </template>

    <template v-else>
      <a
        v-if="isUrl && value"
        :href="value"
        target="_blank"
        rel="noopener noreferrer"
        class="block break-all text-sm text-text-brand hover:underline"
        :data-testid="`project-access-value-${fieldKey}`"
      >
        {{ value }}
      </a>
      <p
        v-else
        class="break-all text-sm"
        :class="value ? 'text-text-default' : 'text-text-subtle'"
        :data-testid="`project-access-value-${fieldKey}`"
      >
        {{ value || t('projectAccess.emptyValue') }}
      </p>
    </template>
  </div>
</template>
