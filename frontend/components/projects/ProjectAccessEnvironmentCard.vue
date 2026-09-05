<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { normalizeApiError } from '~/stores/services/normalize_api_error'
import { useClipboardFeedback } from '~/composables/useClipboardFeedback'
import ProjectAccessInlineField from './ProjectAccessInlineField.vue'

const props = defineProps({
  environment: { type: Object, required: true },
  api: { type: Object, required: true },
  onUpdated: { type: Function, required: true },
})

const { t } = useI18n()
const isEditingPassword = ref(false)
const passwordDraft = ref('')
const revealedPassword = ref('')
const isPasswordVisible = ref(false)
const isPasswordBusy = ref(false)
const passwordError = ref('')
const confirmDeleteOpen = ref(false)
const { copyText, feedbackFor, clearAllFeedback } = useClipboardFeedback()

const environmentKey = () => props.environment.environment

async function saveEnvironmentField(field, value) {
  const detail = await props.api.updateField({
    environment: environmentKey(),
    [field]: value,
  })
  props.onUpdated(detail)
}

function startPasswordEdit() {
  clearPasswordSecret()
  passwordDraft.value = ''
  passwordError.value = ''
  isEditingPassword.value = true
}

function cancelPasswordEdit() {
  passwordDraft.value = ''
  passwordError.value = ''
  isEditingPassword.value = false
}

function clearPasswordSecret() {
  revealedPassword.value = ''
  isPasswordVisible.value = false
}

async function savePassword() {
  if (!passwordDraft.value) {
    passwordError.value = t('projectAccess.errors.passwordRequired')
    return
  }
  isPasswordBusy.value = true
  passwordError.value = ''
  try {
    const detail = await props.api.updateField({
      environment: environmentKey(),
      admin_password: passwordDraft.value,
    })
    props.onUpdated(detail)
    cancelPasswordEdit()
    clearPasswordSecret()
  } catch (error) {
    const normalized = normalizeApiError(error, t('projectAccess.errors.savePassword'))
    passwordError.value = normalized.fieldErrors?.admin_password || normalized.message
  } finally {
    passwordDraft.value = ''
    isPasswordBusy.value = false
  }
}

async function togglePassword() {
  if (isPasswordVisible.value) {
    clearPasswordSecret()
    return
  }
  isPasswordBusy.value = true
  passwordError.value = ''
  try {
    const response = await props.api.revealPassword(environmentKey())
    revealedPassword.value = response.secret
    isPasswordVisible.value = true
  } catch (error) {
    passwordError.value = normalizeApiError(
      error,
      t('projectAccess.errors.revealPassword'),
    ).message
  } finally {
    isPasswordBusy.value = false
  }
}

async function copyPassword() {
  isPasswordBusy.value = true
  passwordError.value = ''
  try {
    const secret = isPasswordVisible.value
      ? revealedPassword.value
      : (await props.api.revealPassword(environmentKey())).secret
    await copyText({
      key: `${environmentKey()}-password`,
      text: secret,
      successLabel: t('projectAccess.actions.copied'),
      errorLabel: t('projectAccess.errors.copy'),
    })
  } catch (error) {
    passwordError.value = normalizeApiError(
      error,
      t('projectAccess.errors.copyPassword'),
    ).message
  } finally {
    isPasswordBusy.value = false
  }
}

async function deletePassword() {
  isPasswordBusy.value = true
  passwordError.value = ''
  try {
    const detail = await props.api.deletePassword(environmentKey())
    props.onUpdated(detail)
    clearPasswordSecret()
    confirmDeleteOpen.value = false
  } catch (error) {
    passwordError.value = normalizeApiError(
      error,
      t('projectAccess.errors.deletePassword'),
    ).message
  } finally {
    isPasswordBusy.value = false
  }
}

watch(
  () => props.environment.has_password,
  (hasPassword) => {
    if (!hasPassword) clearPasswordSecret()
  },
)

onBeforeUnmount(() => {
  passwordDraft.value = ''
  clearPasswordSecret()
  clearAllFeedback()
})
</script>

<template>
  <section
    class="space-y-5 rounded-2xl border border-border-default bg-surface-raised p-4 panel-portrait:p-5"
    :data-testid="`project-access-environment-${environment.environment}`"
  >
    <div>
      <h3 class="text-base font-semibold text-text-default">{{ environment.label }}</h3>
      <p class="mt-1 text-xs text-text-subtle">
        {{ t(`projectAccess.environmentHelp.${environment.environment}`) }}
      </p>
    </div>

    <ProjectAccessInlineField
      :label="t('projectAccess.fields.siteUrl')"
      :value="environment.site_url"
      :field-key="`${environment.environment}-site_url`"
      :placeholder="t('projectAccess.placeholders.siteUrl')"
      is-url
      :save-value="(value) => saveEnvironmentField('site_url', value)"
    />

    <ProjectAccessInlineField
      :label="t('projectAccess.fields.adminUrl')"
      :value="environment.admin_url"
      :field-key="`${environment.environment}-admin_url`"
      :placeholder="t('projectAccess.placeholders.adminUrl')"
      is-url
      :save-value="(value) => saveEnvironmentField('admin_url', value)"
    />

    <ProjectAccessInlineField
      :label="t('projectAccess.fields.username')"
      :value="environment.admin_username"
      :field-key="`${environment.environment}-admin_username`"
      :placeholder="t('projectAccess.placeholders.username')"
      :save-value="(value) => saveEnvironmentField('admin_username', value)"
    />

    <div class="space-y-2" :data-testid="`project-access-password-${environment.environment}`">
      <div class="flex items-center justify-between gap-3">
        <span class="text-xs font-semibold uppercase tracking-wide text-text-muted">
          {{ t('projectAccess.fields.password') }}
        </span>
        <div v-if="!isEditingPassword" class="flex items-center gap-1">
          <BaseActionButton
            v-if="environment.has_password"
            action="copy"
            :label="t('projectAccess.actions.copyPassword')"
            :status-label="feedbackFor(`${environment.environment}-password`).label"
            :status-tone="feedbackFor(`${environment.environment}-password`).tone"
            :disabled="isPasswordBusy"
            :data-testid="`project-access-copy-password-${environment.environment}`"
            @click="copyPassword"
          />
          <BaseActionButton
            v-if="environment.has_password"
            :action="isPasswordVisible ? 'hide' : 'view'"
            :label="isPasswordVisible ? t('projectAccess.actions.hide') : t('projectAccess.actions.reveal')"
            :loading="isPasswordBusy"
            :data-testid="`project-access-reveal-password-${environment.environment}`"
            @click="togglePassword"
          />
          <BaseActionButton
            action="edit"
            :label="t('projectAccess.actions.editPassword')"
            :data-testid="`project-access-edit-password-${environment.environment}`"
            @click="startPasswordEdit"
          />
          <BaseActionButton
            v-if="environment.has_password"
            action="delete"
            variant="danger-ghost"
            :label="t('projectAccess.actions.deletePassword')"
            :data-testid="`project-access-delete-password-${environment.environment}`"
            @click="confirmDeleteOpen = true"
          />
        </div>
      </div>

      <template v-if="isEditingPassword">
        <BaseInput
          v-model="passwordDraft"
          type="password"
          autocomplete="new-password"
          :placeholder="t('projectAccess.placeholders.password')"
          :error="Boolean(passwordError)"
          :disabled="isPasswordBusy"
          :data-testid="`project-access-password-input-${environment.environment}`"
          @keydown.enter.prevent="savePassword"
          @keydown.esc.prevent="cancelPasswordEdit"
        />
        <div class="flex justify-end gap-2">
          <BaseButton variant="ghost" size="sm" :disabled="isPasswordBusy" @click="cancelPasswordEdit">
            {{ t('projectAccess.actions.cancel') }}
          </BaseButton>
          <BaseButton
            variant="primary"
            size="sm"
            :loading="isPasswordBusy"
            :data-testid="`project-access-save-password-${environment.environment}`"
            @click="savePassword"
          >
            {{ t('projectAccess.actions.save') }}
          </BaseButton>
        </div>
      </template>
      <p v-else class="break-all font-mono text-sm text-text-default" aria-live="polite">
        <template v-if="environment.has_password">
          {{ isPasswordVisible ? revealedPassword : '••••••••••••' }}
        </template>
        <span v-else class="font-sans text-text-subtle">{{ t('projectAccess.emptyValue') }}</span>
      </p>
      <p v-if="passwordError" class="text-xs text-danger-strong" role="alert">
        {{ passwordError }}
      </p>
    </div>

    <ConfirmModal
      v-model="confirmDeleteOpen"
      :title="t('projectAccess.confirm.deletePasswordTitle')"
      :message="t('projectAccess.confirm.deletePasswordMessage', { environment: environment.label })"
      :confirm-text="t('projectAccess.actions.delete')"
      :cancel-text="t('projectAccess.actions.cancel')"
      :loading="isPasswordBusy"
      variant="danger"
      @confirm="deletePassword"
    />
  </section>
</template>
