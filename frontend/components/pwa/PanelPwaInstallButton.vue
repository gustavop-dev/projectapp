<script setup>
import { useI18n } from '#imports'
import { usePanelPwa } from '~/composables/usePanelPwa'

defineProps({ collapsed: { type: Boolean, default: false } })
const emit = defineEmits(['install'])
const { t } = useI18n()
const { canOffer, isPrompting, install } = usePanelPwa()

function handleInstall() {
  emit('install')
  install()
}
</script>

<template>
  <BaseButton
    v-if="canOffer"
    variant="secondary"
    size="sm"
    class="mb-2 w-full"
    :icon-only="collapsed"
    :aria-label="t('pwa.install')"
    :loading="isPrompting"
    data-testid="panel-pwa-install"
    @click="handleInstall"
  >
    <BaseActionIcon action="download" />
    <span v-if="!collapsed">{{ t('pwa.install') }}</span>
  </BaseButton>
</template>
