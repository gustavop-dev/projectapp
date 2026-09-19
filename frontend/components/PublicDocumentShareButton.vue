<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { useClipboardFeedback } from '~/composables/useClipboardFeedback'
import { useFocusTrap } from '~/composables/useFocusTrap'
import PublicDocumentAction from '~/components/PublicDocumentAction.vue'

const props = defineProps({
  isDark: { type: Boolean, default: false },
  namespace: { type: String, default: 'additionalModules' },
  testIdPrefix: { type: String, default: 'additional-modules' },
  triggerTestId: { type: String, default: 'additional-modules-share-floating' },
  triggerClass: { type: String, default: 'additional-modules-share-btn share-btn' },
})

const { t } = useI18n()
const label = (key) => t(`${props.namespace}.${key}`)
const nativeShareFailed = ref(false)
const showModal = ref(false)
const currentUrl = ref('')
const canNativeShare = ref(false)
const dialogRef = ref(null)
const clipboard = useClipboardFeedback()
const copyFeedback = computed(() => clipboard.feedbackFor('catalog-url'))

useFocusTrap(dialogRef, {
  active: showModal,
  initialFocus: () => dialogRef.value?.querySelector(`[data-testid="${props.testIdPrefix}-copy-link"]`),
})

function refreshCurrentUrl() {
  if (typeof window !== 'undefined') currentUrl.value = window.location.href
}

function openModal() {
  refreshCurrentUrl()
  nativeShareFailed.value = false
  clipboard.clearFeedback('catalog-url')
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  clipboard.clearFeedback('catalog-url')
}

async function copyLink() {
  await clipboard.copyText({
    key: 'catalog-url',
    text: currentUrl.value,
    successLabel: label('copied'),
    errorLabel: label('copyFailed'),
  })
}

async function nativeShare() {
  nativeShareFailed.value = false
  try {
    await navigator.share({
      title: document.title || label('title'),
      url: currentUrl.value,
    })
  } catch (error) {
    nativeShareFailed.value = error?.name !== 'AbortError'
  }
}

function onKeydown(event) {
  if (event.key === 'Escape' && showModal.value) closeModal()
}

onMounted(() => {
  refreshCurrentUrl()
  canNativeShare.value = typeof navigator !== 'undefined' && Boolean(navigator.share)
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div>
    <PublicDocumentAction
      action="share"
      :class="triggerClass"
      :label="label('shareCurrent')"
      :data-testid="triggerTestId"
      @click="openModal"
    />

    <Teleport to="body">
      <Transition name="share-modal">
        <div
          v-if="showModal"
          ref="dialogRef"
          tabindex="-1"
          :data-theme="isDark ? 'dark' : 'light'"
          class="public-document-theme fixed inset-0 z-[9990] flex items-end justify-center bg-black/40 backdrop-blur-sm sm:items-center"
          role="dialog"
          aria-modal="true"
          :aria-label="label('shareCurrent')"
          :data-testid="`${testIdPrefix}-share-dialog`"
          @click.self="closeModal"
        >
          <div class="share-modal-card w-full rounded-t-3xl border border-border-default bg-surface p-6 shadow-overlay sm:mx-4 sm:max-w-md sm:rounded-2xl sm:p-8">
            <div class="mb-6 flex items-start justify-between gap-4">
              <div class="min-w-0">
                <h2 class="text-lg font-medium text-text-default">
                  {{ label('shareCurrent') }}
                </h2>
                <p class="mt-1 text-sm leading-6 text-text-muted">
                  {{ label('shareCurrentHelp') }}
                </p>
              </div>
              <BaseButton
                unstyled
                icon-only
                type="button"
                class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-surface-raised text-text-muted hover:text-text-default"
                :aria-label="label('close')"
                @click="closeModal"
              >
                <span aria-hidden="true" class="text-xl">×</span>
              </BaseButton>
            </div>

            <div class="flex min-w-0 items-center gap-3 rounded-xl border border-border-default bg-surface-raised p-3 sm:p-4">
              <div class="min-w-0 flex-1">
                <p class="text-xs font-medium uppercase tracking-wide text-text-subtle">
                  {{ label('linkLabel') }}
                </p>
                <p class="mt-1 truncate text-sm text-text-default" :data-testid="`${testIdPrefix}-share-url`">
                  {{ currentUrl }}
                </p>
              </div>
              <BaseButton
                size="sm"
                type="button"
                :data-testid="`${testIdPrefix}-copy-link`"
                @click="copyLink"
              >
                {{ label('copyLink') }}
              </BaseButton>
            </div>

            <p
              v-if="copyFeedback.label"
              class="mt-3 text-sm font-medium"
              :class="copyFeedback.tone === 'danger' ? 'text-danger-strong' : 'text-success-strong'"
              :role="copyFeedback.tone === 'danger' ? 'alert' : 'status'"
              :data-testid="`${testIdPrefix}-share-feedback`"
            >
              {{ copyFeedback.label }}
            </p>

            <p v-if="nativeShareFailed" role="alert" class="mt-3 text-sm text-danger-strong">
              {{ label('shareFailed') }}
            </p>

            <BaseButton
              v-if="canNativeShare"
              class="mt-5 w-full"
              type="button"
              :data-testid="`${testIdPrefix}-native-share`"
              @click="nativeShare"
            >
              {{ label('shareViaApps') }}
            </BaseButton>
            <p v-else class="mt-4 text-center text-xs text-text-subtle">
              {{ label('copyHint') }}
            </p>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.share-modal-enter-active,
.share-modal-leave-active {
  transition: opacity 0.2s ease;
}

.share-modal-enter-active .share-modal-card,
.share-modal-leave-active .share-modal-card {
  transition: transform 0.25s ease, opacity 0.2s ease;
}

.share-modal-enter-from,
.share-modal-leave-to,
.share-modal-enter-from .share-modal-card,
.share-modal-leave-to .share-modal-card {
  opacity: 0;
}

.share-modal-enter-from .share-modal-card,
.share-modal-leave-to .share-modal-card {
  transform: translateY(1rem);
}

@media (prefers-reduced-motion: reduce) {
  .share-modal-enter-active,
  .share-modal-leave-active,
  .share-modal-enter-active .share-modal-card,
  .share-modal-leave-active .share-modal-card {
    transition: none;
  }
}
</style>
