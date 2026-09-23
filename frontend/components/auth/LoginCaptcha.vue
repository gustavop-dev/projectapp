<template>
  <div class="space-y-2" data-testid="login-captcha">
    <div ref="container" class="flex justify-center"></div>
    <p v-if="message" class="text-sm text-text-muted" role="status" aria-live="polite">{{ message }}</p>
    <BaseButton v-if="state === 'error' || state === 'expired' || retryAvailable" variant="secondary" size="sm" @click="retry">
      {{ t('captcha.retry') }}
    </BaseButton>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { loadRecaptcha } from '~/utils/recaptcha'

const props = defineProps({
  siteKey: { type: String, default: '' },
  resetKey: { type: Number, default: 0 },
  retryAvailable: { type: Boolean, default: false },
})
const emit = defineEmits(['update:token'])
const { t } = useI18n()
const container = ref(null)
const state = ref('loading')
let widget = null
let active = true
let loading = false
const message = computed(() => state.value === 'verified' ? '' : t(`captcha.${state.value}`))

function invalidate(nextState) {
  if (!active) return
  emit('update:token', '')
  state.value = nextState
}

async function retry() {
  if (loading) return
  loading = true
  invalidate('loading')
  try {
    if (!props.siteKey) throw new Error('captcha_key_missing')
    const api = await loadRecaptcha()
    if (!active) return
    state.value = 'required'
    if (widget !== null) {
      api.reset(widget)
    } else {
      widget = api.render(container.value, {
        sitekey: props.siteKey,
        size: 'compact',
        theme: 'light',
        callback: (token) => {
          if (!active) return
          emit('update:token', token)
          state.value = token ? 'verified' : 'required'
        },
        'expired-callback': () => invalidate('expired'),
        'error-callback': () => invalidate('error'),
      })
    }
  } catch {
    invalidate('error')
  } finally {
    loading = false
  }
}

watch(() => props.resetKey, retry)
onMounted(retry)
onBeforeUnmount(() => {
  active = false
  emit('update:token', '')
  if (widget !== null) window.grecaptcha?.reset(widget)
})
</script>
