<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { normalizeApiError } from '~/stores/services/normalize_api_error'
import { useClipboardFeedback } from '~/composables/useClipboardFeedback'
import ProjectAccessEnvironmentCard from './ProjectAccessEnvironmentCard.vue'
import ProjectAccessInlineField from './ProjectAccessInlineField.vue'
import ProjectAccessNotes from './ProjectAccessNotes.vue'

const props = defineProps({
  api: { type: Object, required: true },
})

const { t } = useI18n()
const detail = ref(null)
const isLoading = ref(true)
const isClassifying = ref(false)
const errorMessage = ref('')
const classificationError = ref('')
const { copyText, feedbackFor, clearAllFeedback } = useClipboardFeedback()

function applyDetail(payload) {
  detail.value = payload
}

async function load() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    applyDetail(await props.api.load())
  } catch (error) {
    errorMessage.value = normalizeApiError(error, t('projectAccess.errors.load')).message
  } finally {
    isLoading.value = false
  }
}

async function saveRepository(value) {
  applyDetail(await props.api.updateField({ repository_url: value }))
}

async function classifyLegacy(environment) {
  isClassifying.value = true
  classificationError.value = ''
  try {
    applyDetail(await props.api.classifyLegacy(environment))
  } catch (error) {
    classificationError.value = normalizeApiError(
      error,
      t('projectAccess.errors.classify'),
    ).message
  } finally {
    isClassifying.value = false
  }
}

function copyLegacy(field, value) {
  return copyText({
    key: `legacy-${field}`,
    text: value,
    successLabel: t('projectAccess.actions.copied'),
    errorLabel: t('projectAccess.errors.copy'),
  })
}

onMounted(load)
onBeforeUnmount(() => {
  detail.value = null
  clearAllFeedback()
})
</script>

<template>
  <div class="space-y-6" data-testid="project-access-editor">
    <div v-if="isLoading" class="space-y-4" aria-live="polite" data-testid="project-access-loading">
      <div class="h-24 animate-pulse rounded-xl bg-surface-muted" />
      <div class="grid gap-4 panel-landscape:grid-cols-2">
        <div class="h-80 animate-pulse rounded-xl bg-surface-muted" />
        <div class="h-80 animate-pulse rounded-xl bg-surface-muted" />
      </div>
      <span class="sr-only">{{ t('projectAccess.loading') }}</span>
    </div>

    <BaseAlert v-else-if="errorMessage" variant="danger" data-testid="project-access-load-error">
      <div class="flex flex-col gap-3 panel-portrait:flex-row panel-portrait:items-center panel-portrait:justify-between">
        <span>{{ errorMessage }}</span>
        <BaseButton variant="secondary" size="sm" @click="load">
          {{ t('projectAccess.actions.retry') }}
        </BaseButton>
      </div>
    </BaseAlert>

    <template v-else-if="detail">
      <header class="rounded-xl border border-border-muted bg-surface-muted p-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-text-muted">
          {{ t('projectAccess.contextLabel') }}
        </p>
        <h2 class="mt-1 break-words text-lg font-semibold text-text-default">
          {{ detail.project.name }}
        </h2>
        <p class="mt-1 text-sm text-text-subtle">
          {{ t('projectAccess.clientLabel', { name: detail.project.client_name }) }}
        </p>
      </header>

      <BaseAlert
        v-if="detail.legacy_access"
        variant="warning"
        data-testid="project-access-legacy"
      >
        <div class="space-y-4">
          <div>
            <p class="font-medium">{{ t('projectAccess.legacy.title') }}</p>
            <p class="mt-1 text-sm">{{ t('projectAccess.legacy.help') }}</p>
          </div>
          <dl class="grid gap-3 panel-portrait:grid-cols-2">
            <div v-if="detail.legacy_access.admin_url" class="min-w-0">
              <dt class="text-xs font-semibold uppercase tracking-wide">{{ t('projectAccess.fields.adminUrl') }}</dt>
              <dd class="mt-1 flex items-start gap-2">
                <a :href="detail.legacy_access.admin_url" target="_blank" rel="noopener noreferrer" class="min-w-0 flex-1 break-all text-sm underline">
                  {{ detail.legacy_access.admin_url }}
                </a>
                <BaseActionButton
                  action="copy"
                  :label="t('projectAccess.actions.copy')"
                  :status-label="feedbackFor('legacy-admin_url').label"
                  :status-tone="feedbackFor('legacy-admin_url').tone"
                  @click="copyLegacy('admin_url', detail.legacy_access.admin_url)"
                />
              </dd>
            </div>
            <div v-if="detail.legacy_access.admin_username" class="min-w-0">
              <dt class="text-xs font-semibold uppercase tracking-wide">{{ t('projectAccess.fields.username') }}</dt>
              <dd class="mt-1 flex items-start gap-2">
                <span class="min-w-0 flex-1 break-all font-mono text-sm">{{ detail.legacy_access.admin_username }}</span>
                <BaseActionButton
                  action="copy"
                  :label="t('projectAccess.actions.copy')"
                  :status-label="feedbackFor('legacy-admin_username').label"
                  :status-tone="feedbackFor('legacy-admin_username').tone"
                  @click="copyLegacy('admin_username', detail.legacy_access.admin_username)"
                />
              </dd>
            </div>
          </dl>
          <p v-if="detail.legacy_access.has_password" class="text-sm">
            {{ t('projectAccess.legacy.passwordPresent') }}
          </p>
          <p v-if="classificationError" class="text-sm text-danger-strong" role="alert">
            {{ classificationError }}
          </p>
          <div class="flex flex-wrap gap-2">
            <BaseButton variant="secondary" size="sm" :loading="isClassifying" @click="classifyLegacy('production')">
              {{ t('projectAccess.legacy.moveToProduction') }}
            </BaseButton>
            <BaseButton variant="secondary" size="sm" :disabled="isClassifying" @click="classifyLegacy('staging')">
              {{ t('projectAccess.legacy.moveToStaging') }}
            </BaseButton>
          </div>
        </div>
      </BaseAlert>

      <section class="rounded-2xl border border-border-default bg-surface-raised p-4 panel-portrait:p-5">
        <ProjectAccessInlineField
          :label="t('projectAccess.fields.repositoryUrl')"
          :value="detail.repository_url"
          field-key="repository_url"
          :placeholder="t('projectAccess.placeholders.repositoryUrl')"
          is-url
          :save-value="saveRepository"
        />
      </section>

      <div class="grid grid-cols-1 gap-4 panel-landscape:grid-cols-2" data-testid="project-access-environments">
        <ProjectAccessEnvironmentCard
          v-for="environment in detail.environments"
          :key="environment.environment"
          :environment="environment"
          :api="api"
          :on-updated="applyDetail"
        />
      </div>

      <ProjectAccessNotes
        :notes="detail.notes"
        :api="api"
        :on-updated="applyDetail"
      />
    </template>
  </div>
</template>
