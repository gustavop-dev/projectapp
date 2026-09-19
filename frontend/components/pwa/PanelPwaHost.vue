<script setup>
import { onMounted } from 'vue'
import { useI18n } from '#imports'
import { usePanelPwa } from '~/composables/usePanelPwa'

const { t } = useI18n()
const {
  canOffer, isPrompting, invitationVisible, instructionsOpen, installError,
  browserKind, install, dismissInvitation, showInvitationOnce,
} = usePanelPwa()

onMounted(showInvitationOnce)
</script>

<template>
  <div
    v-if="canOffer && invitationVisible"
    class="mb-5 flex flex-wrap items-center gap-3 rounded-xl border border-border-default bg-surface p-4"
    role="status"
    data-testid="panel-pwa-invitation"
  >
    <p class="min-w-0 flex-1 text-sm text-text-muted">{{ t('pwa.invitation') }}</p>
    <BaseButton size="sm" :loading="isPrompting" @click="install">{{ t('pwa.install') }}</BaseButton>
    <BaseActionButton action="close" :label="t('pwa.dismiss')" @click="dismissInvitation" />
  </div>

  <BaseModal v-model="instructionsOpen" kind="confirm" padding="md">
    <div class="mb-4 flex items-start justify-between gap-3">
      <h2 class="text-lg font-semibold text-text-default">{{ t('pwa.install') }}</h2>
      <BaseActionButton action="close" :label="t('pwa.close')" @click="instructionsOpen = false" />
    </div>
    <p v-if="installError" role="alert" class="mb-4 text-sm text-danger-strong">{{ t('pwa.error') }}</p>
    <p class="mb-4 text-sm text-text-muted">{{ t('pwa.help.' + browserKind) }}</p>
    <p class="text-sm text-text-muted">{{ t('pwa.requiresConnection') }}</p>
  </BaseModal>
</template>
