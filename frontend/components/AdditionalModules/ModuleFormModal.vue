<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  module: { type: Object, default: null },
  categories: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
  errorMessage: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'save'])
const { t } = useI18n()
const languageTab = ref('es')
const localError = ref('')

const form = reactive({
  category: '',
  slug: '',
  icon: '',
  name_es: '',
  name_en: '',
  summary_es: '',
  summary_en: '',
  what_is_es: '',
  what_is_en: '',
  purpose_es: '',
  purpose_en: '',
  problems_solved_es: '',
  problems_solved_en: '',
  integrations_es: '',
  integrations_en: '',
  implementation_requirements_es: '',
  implementation_requirements_en: '',
})

const listText = (value) => (Array.isArray(value) ? value.join('\n') : '')
const parseLines = (value) => value.split('\n').map((item) => item.trim()).filter(Boolean)

function resetForm() {
  const module = props.module
  form.category = module?.category || props.categories.find((item) => item.is_active)?.id || ''
  form.slug = module?.slug || ''
  form.icon = module?.icon || ''
  for (const field of ['name', 'summary', 'what_is', 'purpose']) {
    form[`${field}_es`] = module?.[`${field}_es`] || ''
    form[`${field}_en`] = module?.[`${field}_en`] || ''
  }
  for (const field of ['problems_solved', 'integrations', 'implementation_requirements']) {
    form[`${field}_es`] = listText(module?.[`${field}_es`])
    form[`${field}_en`] = listText(module?.[`${field}_en`])
  }
  languageTab.value = 'es'
  localError.value = ''
}

watch(() => props.modelValue, (open) => {
  if (open) resetForm()
})

function close() {
  emit('update:modelValue', false)
}

function submit() {
  const required = [
    form.category,
    form.slug,
    form.name_es,
    form.name_en,
    form.summary_es,
    form.summary_en,
    form.what_is_es,
    form.what_is_en,
    form.purpose_es,
    form.purpose_en,
  ]
  const listFields = [
    'problems_solved_es', 'problems_solved_en',
    'integrations_es', 'integrations_en',
    'implementation_requirements_es', 'implementation_requirements_en',
  ]
  if (required.some((value) => !String(value).trim()) || listFields.some((field) => parseLines(form[field]).length === 0)) {
    localError.value = t('additionalModules.requiredFields')
    return
  }
  localError.value = ''
  emit('save', {
    category: Number(form.category),
    slug: form.slug.trim(),
    icon: form.icon.trim(),
    name_es: form.name_es.trim(),
    name_en: form.name_en.trim(),
    summary_es: form.summary_es.trim(),
    summary_en: form.summary_en.trim(),
    what_is_es: form.what_is_es.trim(),
    what_is_en: form.what_is_en.trim(),
    purpose_es: form.purpose_es.trim(),
    purpose_en: form.purpose_en.trim(),
    problems_solved_es: parseLines(form.problems_solved_es),
    problems_solved_en: parseLines(form.problems_solved_en),
    integrations_es: parseLines(form.integrations_es),
    integrations_en: parseLines(form.integrations_en),
    implementation_requirements_es: parseLines(form.implementation_requirements_es),
    implementation_requirements_en: parseLines(form.implementation_requirements_en),
  })
}
</script>

<template>
  <BaseModal
    :model-value="modelValue"
    kind="form-wide"
    padding="none"
    @update:model-value="emit('update:modelValue', $event)"
    @close="close"
  >
    <form class="flex min-h-0 flex-col" data-testid="additional-module-form" @submit.prevent="submit">
      <header class="border-b border-border-default px-5 py-5 sm:px-7">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-medium text-text-brand">
              {{ module ? t('additionalModules.moduleEditTitle') : t('additionalModules.moduleCreateTitle') }}
            </h2>
            <p class="mt-1 text-sm text-text-muted">{{ t('additionalModules.noPriceNotice') }}</p>
          </div>
          <BaseButton variant="ghost" icon-only :aria-label="t('additionalModules.close')" @click="close">
            <span aria-hidden="true" class="text-xl">×</span>
          </BaseButton>
        </div>
      </header>

      <div class="space-y-5 overflow-y-auto px-5 py-5 sm:px-7">
        <div class="grid gap-4 sm:grid-cols-[1fr_1fr_7rem]">
          <BaseFormField :label="t('additionalModules.category')" for="additional-module-category" required>
            <BaseSelect
              id="additional-module-category"
              v-model="form.category"
              :options="categories.map((category) => ({ value: category.id, label: category.name_es }))"
              data-testid="additional-module-category"
            />
          </BaseFormField>
          <BaseFormField :label="t('additionalModules.slug')" for="additional-module-slug" required>
            <BaseInput id="additional-module-slug" v-model="form.slug" data-testid="additional-module-slug" />
          </BaseFormField>
          <BaseFormField :label="t('additionalModules.icon')" for="additional-module-icon">
            <BaseInput id="additional-module-icon" v-model="form.icon" data-testid="additional-module-icon" />
          </BaseFormField>
        </div>

        <BaseSegmented
          v-model="languageTab"
          :options="[
            { value: 'es', label: t('additionalModules.spanish') },
            { value: 'en', label: t('additionalModules.english') },
          ]"
          data-testid="additional-module-language-tabs"
        />

        <div v-show="languageTab === 'es'" class="space-y-4">
          <BaseFormField :label="t('additionalModules.name')" for="additional-module-name-es" required>
            <BaseInput id="additional-module-name-es" v-model="form.name_es" data-testid="additional-module-name-es" />
          </BaseFormField>
          <BaseFormField :label="t('additionalModules.summary')" for="additional-module-summary-es" required>
            <BaseTextarea id="additional-module-summary-es" v-model="form.summary_es" rows="2" />
          </BaseFormField>
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseFormField :label="t('additionalModules.whatIsField')" for="additional-module-what-es" required>
              <BaseTextarea id="additional-module-what-es" v-model="form.what_is_es" rows="5" />
            </BaseFormField>
            <BaseFormField :label="t('additionalModules.purposeField')" for="additional-module-purpose-es" required>
              <BaseTextarea id="additional-module-purpose-es" v-model="form.purpose_es" rows="5" />
            </BaseFormField>
          </div>
          <BaseFormField :label="t('additionalModules.problemsField')" for="additional-module-problems-es" required>
            <BaseTextarea id="additional-module-problems-es" v-model="form.problems_solved_es" rows="4" />
          </BaseFormField>
          <BaseFormField :label="t('additionalModules.integrationsField')" for="additional-module-integrations-es" required>
            <BaseTextarea id="additional-module-integrations-es" v-model="form.integrations_es" rows="4" />
          </BaseFormField>
          <BaseFormField :label="t('additionalModules.requirementsField')" for="additional-module-requirements-es" required>
            <BaseTextarea id="additional-module-requirements-es" v-model="form.implementation_requirements_es" rows="4" />
          </BaseFormField>
        </div>

        <div v-show="languageTab === 'en'" class="space-y-4">
          <BaseFormField :label="t('additionalModules.name')" for="additional-module-name-en" required>
            <BaseInput id="additional-module-name-en" v-model="form.name_en" />
          </BaseFormField>
          <BaseFormField :label="t('additionalModules.summary')" for="additional-module-summary-en" required>
            <BaseTextarea id="additional-module-summary-en" v-model="form.summary_en" rows="2" />
          </BaseFormField>
          <div class="grid gap-4 sm:grid-cols-2">
            <BaseFormField :label="t('additionalModules.whatIsField')" for="additional-module-what-en" required>
              <BaseTextarea id="additional-module-what-en" v-model="form.what_is_en" rows="5" />
            </BaseFormField>
            <BaseFormField :label="t('additionalModules.purposeField')" for="additional-module-purpose-en" required>
              <BaseTextarea id="additional-module-purpose-en" v-model="form.purpose_en" rows="5" />
            </BaseFormField>
          </div>
          <BaseFormField :label="t('additionalModules.problemsField')" for="additional-module-problems-en" required>
            <BaseTextarea id="additional-module-problems-en" v-model="form.problems_solved_en" rows="4" />
          </BaseFormField>
          <BaseFormField :label="t('additionalModules.integrationsField')" for="additional-module-integrations-en" required>
            <BaseTextarea id="additional-module-integrations-en" v-model="form.integrations_en" rows="4" />
          </BaseFormField>
          <BaseFormField :label="t('additionalModules.requirementsField')" for="additional-module-requirements-en" required>
            <BaseTextarea id="additional-module-requirements-en" v-model="form.implementation_requirements_en" rows="4" />
          </BaseFormField>
        </div>

        <BaseAlert v-if="localError || errorMessage" variant="danger">
          {{ localError || errorMessage }}
        </BaseAlert>
      </div>

      <footer class="flex flex-wrap justify-end gap-2 border-t border-border-default px-5 py-4 sm:px-7">
        <BaseButton type="button" variant="ghost" @click="close">{{ t('additionalModules.cancel') }}</BaseButton>
        <BaseButton type="submit" :loading="saving" data-testid="additional-module-save">
          {{ t('additionalModules.save') }}
        </BaseButton>
      </footer>
    </form>
  </BaseModal>
</template>
