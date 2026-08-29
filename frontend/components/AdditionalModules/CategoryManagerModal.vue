<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  categories: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
  errorMessage: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'save', 'status'])
const { t } = useI18n()
const editingId = ref(null)
const formOpen = ref(false)
const localError = ref('')
const form = reactive({ slug: '', name_es: '', name_en: '' })

watch(() => props.modelValue, (open) => {
  if (!open) return
  formOpen.value = false
  editingId.value = null
  localError.value = ''
})

function openCreate() {
  editingId.value = null
  form.slug = ''
  form.name_es = ''
  form.name_en = ''
  formOpen.value = true
  localError.value = ''
}

function openEdit(category) {
  editingId.value = category.id
  form.slug = category.slug
  form.name_es = category.name_es
  form.name_en = category.name_en
  formOpen.value = true
  localError.value = ''
}

function submit() {
  if (!form.slug.trim() || !form.name_es.trim() || !form.name_en.trim()) {
    localError.value = t('additionalModules.requiredFields')
    return
  }
  emit('save', {
    id: editingId.value,
    payload: {
      slug: form.slug.trim(),
      name_es: form.name_es.trim(),
      name_en: form.name_en.trim(),
    },
  })
}

function closeForm() {
  formOpen.value = false
  editingId.value = null
  localError.value = ''
}

defineExpose({ closeForm })
</script>

<template>
  <BaseModal
    :model-value="modelValue"
    kind="form-wide"
    padding="none"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex min-h-0 flex-col">
      <header class="flex items-start justify-between gap-4 border-b border-border-default px-5 py-5 sm:px-7">
        <div>
          <h2 class="text-xl font-medium text-text-brand">{{ t('additionalModules.categoryFormTitle') }}</h2>
          <p class="mt-1 text-sm text-text-muted">{{ t('additionalModules.orderHelp') }}</p>
        </div>
        <BaseButton variant="ghost" icon-only :aria-label="t('additionalModules.close')" @click="emit('update:modelValue', false)">
          <span aria-hidden="true" class="text-xl">×</span>
        </BaseButton>
      </header>

      <div class="space-y-4 overflow-y-auto px-5 py-5 sm:px-7">
        <div class="flex justify-end">
          <BaseButton variant="secondary" size="sm" data-testid="additional-category-add" @click="openCreate">
            {{ t('additionalModules.addCategory') }}
          </BaseButton>
        </div>

        <form v-if="formOpen" class="rounded-xl border border-border-default bg-surface-raised p-4" @submit.prevent="submit">
          <h3 class="mb-4 font-medium text-text-brand">
            {{ editingId ? t('additionalModules.editCategory') : t('additionalModules.addCategory') }}
          </h3>
          <div class="grid gap-4 sm:grid-cols-3">
            <BaseFormField :label="t('additionalModules.slug')" for="additional-category-slug" required>
              <BaseInput id="additional-category-slug" v-model="form.slug" />
            </BaseFormField>
            <BaseFormField :label="t('additionalModules.categoryNameEs')" for="additional-category-name-es" required>
              <BaseInput id="additional-category-name-es" v-model="form.name_es" />
            </BaseFormField>
            <BaseFormField :label="t('additionalModules.categoryNameEn')" for="additional-category-name-en" required>
              <BaseInput id="additional-category-name-en" v-model="form.name_en" />
            </BaseFormField>
          </div>
          <BaseAlert v-if="localError || errorMessage" class="mt-4" variant="danger">
            {{ localError || errorMessage }}
          </BaseAlert>
          <div class="mt-4 flex justify-end gap-2">
            <BaseButton type="button" variant="ghost" size="sm" @click="closeForm">{{ t('additionalModules.cancel') }}</BaseButton>
            <BaseButton type="submit" size="sm" :loading="saving">{{ t('additionalModules.save') }}</BaseButton>
          </div>
        </form>

        <ul class="space-y-3" data-testid="additional-category-list">
          <li
            v-for="category in categories"
            :key="category.id"
            class="flex flex-col gap-3 rounded-xl border border-border-default bg-surface p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <span class="font-medium text-text-brand">{{ category.name_es }}</span>
                <BaseBadge :variant="category.is_active ? 'success' : 'neutral'">
                  {{ category.is_active ? t('additionalModules.active') : t('additionalModules.retired') }}
                </BaseBadge>
              </div>
              <p class="mt-1 text-sm text-text-muted">{{ category.name_en }} · {{ category.slug }}</p>
              <p class="mt-1 text-xs text-text-subtle">
                {{ category.active_module_count }} / {{ category.module_count }} {{ t('additionalModules.title').toLowerCase() }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2">
              <BaseButton variant="secondary" size="sm" @click="openEdit(category)">{{ t('additionalModules.edit') }}</BaseButton>
              <BaseButton
                v-if="category.is_active"
                variant="danger-ghost"
                size="sm"
                :disabled="category.active_module_count > 0"
                :disabled-reason="category.active_module_count > 0 ? t('additionalModules.retireCategoryBlocked') : ''"
                @click="emit('status', { category, action: 'retire' })"
              >
                {{ t('additionalModules.retire') }}
              </BaseButton>
              <BaseButton
                v-else
                variant="secondary"
                size="sm"
                @click="emit('status', { category, action: 'restore' })"
              >
                {{ t('additionalModules.restore') }}
              </BaseButton>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </BaseModal>
</template>
