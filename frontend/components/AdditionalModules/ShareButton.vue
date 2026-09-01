<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { useClipboardFeedback } from '~/composables/useClipboardFeedback'
import { useFocusTrap } from '~/composables/useFocusTrap'

const props = defineProps({
  isDark: { type: Boolean, default: false },
})

const { t } = useI18n()
const showModal = ref(false)
const currentUrl = ref('')
const canNativeShare = ref(false)
const dialogRef = ref(null)
const clipboard = useClipboardFeedback()
const copyFeedback = computed(() => clipboard.feedbackFor('catalog-url'))

useFocusTrap(dialogRef, {
  active: showModal,
  initialFocus: () => dialogRef.value?.querySelector('[data-testid="additional-modules-copy-link"]'),
})

function refreshCurrentUrl() {
  if (typeof window !== 'undefined') currentUrl.value = window.location.href
}

function openModal() {
  refreshCurrentUrl()
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
    successLabel: t('additionalModules.copied'),
    errorLabel: t('additionalModules.copyFailed'),
  })
}

async function nativeShare() {
  try {
    await navigator.share({
      title: document.title || t('additionalModules.title'),
      url: currentUrl.value,
    })
  } catch {
    // Closing the native share sheet is not an application error.
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
    <BaseButton
      unstyled
      icon-only
      type="button"
      class="additional-modules-share-btn share-btn fixed bottom-[8.5rem] right-4 z-40 flex h-12 w-12 items-center justify-center rounded-full border border-border-default bg-surface text-text-muted shadow-lg transition-colors hover:bg-surface-muted hover:text-text-brand"
      :title="t('additionalModules.shareCurrent')"
      :aria-label="t('additionalModules.shareCurrent')"
      data-testid="additional-modules-share-floating"
      @click="openModal"
    >
      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342A3 3 0 108.684 10.658m0 2.684 6.632 3.316m-6.632-6 6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684Zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684Z" />
      </svg>
    </BaseButton>

    <Teleport to="body">
      <Transition name="share-modal">
        <div
          v-if="showModal"
          ref="dialogRef"
          tabindex="-1"
          :data-theme="isDark ? 'dark' : 'light'"
          class="fixed inset-0 z-[9990] flex items-end justify-center bg-black/40 backdrop-blur-sm sm:items-center"
          role="dialog"
          aria-modal="true"
          :aria-label="t('additionalModules.shareCurrent')"
          data-testid="additional-modules-share-dialog"
          @click.self="closeModal"
        >
          <div class="share-modal-card w-full rounded-t-3xl border border-border-default bg-surface p-6 shadow-overlay sm:mx-4 sm:max-w-md sm:rounded-2xl sm:p-8">
            <div class="mb-6 flex items-start justify-between gap-4">
              <div class="min-w-0">
                <h2 class="text-lg font-medium text-text-default">
                  {{ t('additionalModules.shareCurrent') }}
                </h2>
                <p class="mt-1 text-sm leading-6 text-text-muted">
                  {{ t('additionalModules.shareCurrentHelp') }}
                </p>
              </div>
              <BaseButton
                unstyled
                icon-only
                type="button"
                class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-surface-raised text-text-muted hover:text-text-default"
                :aria-label="t('additionalModules.close')"
                @click="closeModal"
              >
                <span aria-hidden="true" class="text-xl">×</span>
              </BaseButton>
            </div>

            <div class="flex min-w-0 items-center gap-3 rounded-xl border border-border-default bg-surface-raised p-3 sm:p-4">
              <div class="min-w-0 flex-1">
                <p class="text-xs font-medium uppercase tracking-wide text-text-subtle">
                  {{ t('additionalModules.linkLabel') }}
                </p>
                <p class="mt-1 truncate text-sm text-text-default" data-testid="additional-modules-share-url">
                  {{ currentUrl }}
                </p>
              </div>
              <BaseButton
                size="sm"
                type="button"
                data-testid="additional-modules-copy-link"
                @click="copyLink"
              >
                {{ t('additionalModules.copyLink') }}
              </BaseButton>
            </div>

            <p
              v-if="copyFeedback.label"
              class="mt-3 text-sm font-medium"
              :class="copyFeedback.tone === 'danger' ? 'text-danger-strong' : 'text-success-strong'"
              :role="copyFeedback.tone === 'danger' ? 'alert' : 'status'"
              data-testid="additional-modules-share-feedback"
            >
              {{ copyFeedback.label }}
            </p>

            <BaseButton
              v-if="canNativeShare"
              class="mt-5 w-full"
              type="button"
              data-testid="additional-modules-native-share"
              @click="nativeShare"
            >
              {{ t('additionalModules.shareViaApps') }}
            </BaseButton>
            <p v-else class="mt-4 text-center text-xs text-text-subtle">
              {{ t('additionalModules.copyHint') }}
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

.additional-modules-share-btn {
  right: max(1rem, env(safe-area-inset-right));
  bottom: calc(8.5rem + env(safe-area-inset-bottom));
}
</style>
