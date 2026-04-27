<template>
  <div id="platform-login" class="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
    <BackgroundGradientAnimation
      gradient-background-start="rgb(0, 41, 33)"
      gradient-background-end="rgb(0, 25, 20)"
      first-color="0, 120, 100"
      second-color="0, 80, 90"
      third-color="30, 80, 60"
      fourth-color="0, 60, 80"
      fifth-color="20, 100, 70"
      pointer-color="0, 100, 80"
      size="100%"
      blending-value="hard-light"
      :interactive="true"
      container-class-name="!w-full !h-full !absolute !inset-0"
    />

    <div class="grain-overlay"></div>

    <div class="relative z-10 w-full max-w-md">
      <div class="mb-10 text-center" data-enter>
        <h1 class="font-bold text-2xl tracking-tight text-white">
          Project<span class="text-white/60">App.</span>
        </h1>
        <p class="mt-2 text-sm font-medium uppercase tracking-[0.25em] text-white/50">Portal</p>
      </div>

      <div class="rounded-3xl border border-white/[0.1] bg-white/95 p-8 shadow-2xl backdrop-blur-2xl" data-enter>
        <h2 class="text-xl font-medium text-text-default">Inicia sesión</h2>
        <p class="mt-2 text-sm leading-6 text-green-light">
          Ingresa con tu email y contraseña para acceder al portal.
        </p>

        <div v-if="errorMessage" class="mt-6 rounded-2xl border border-red-500/20 bg-red-50 px-4 py-3 text-sm text-red-600">
          {{ errorMessage }}
        </div>

        <form class="mt-8 space-y-5" @submit.prevent="handleSubmit">
          <div>
            <label for="platform-email" class="mb-2 block text-sm font-medium text-esmerald/70">Email</label>
            <input
              id="platform-email"
              v-model="form.email"
              type="email"
              autocomplete="email"
              class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition placeholder:text-green-light/60 focus:border-border-default focus:ring-1 focus:ring-esmerald/10"
              placeholder="cliente@empresa.com"
            >
          </div>

          <div>
            <label for="platform-password" class="mb-2 block text-sm font-medium text-esmerald/70">Contraseña</label>
            <input
              id="platform-password"
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              class="w-full rounded-xl border border-border-default bg-surface-muted/40 px-4 py-3 text-sm text-text-default outline-none transition placeholder:text-green-light/60 focus:border-border-default focus:ring-1 focus:ring-esmerald/10"
              placeholder="••••••••"
            >
          </div>

          <!-- reCAPTCHA v2 -->
          <div v-if="recaptchaSiteKey" class="flex justify-center">
            <div ref="recaptchaContainer"></div>
          </div>

          <button
            type="submit"
            class="w-full rounded-full bg-primary px-4 py-3 text-sm font-semibold text-white transition hover:bg-esmerald/90 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!canSubmit || authStore.isLoading"
          >
            {{ authStore.isLoading ? 'Ingresando...' : 'Iniciar sesión' }}
          </button>
        </form>
      </div>

      <p class="mt-8 text-center text-sm leading-6 text-white/40" data-enter>
        Si es tu primer acceso, después de validar tus credenciales temporales te guiaremos para configurar tu contraseña definitiva.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import BackgroundGradientAnimation from '~/components/ui/BackgroundGradientAnimation.vue'

definePageMeta({
  layout: false,
  middleware: ['platform-auth'],
})

useHead({
  title: 'Acceso a plataforma — ProjectApp',
})

const config = useRuntimeConfig()
const recaptchaSiteKey = config.public.recaptchaSiteKey
const recaptchaContainer = ref(null)
const recaptchaToken = ref('')
let recaptchaWidgetId = null

function loadRecaptchaScript() {
  return new Promise((resolve) => {
    if (window.grecaptcha?.render) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = 'https://www.google.com/recaptcha/api.js?onload=onRecaptchaLoaded&render=explicit'
    script.async = true
    script.defer = true
    window.onRecaptchaLoaded = () => resolve()
    document.head.appendChild(script)
  })
}

function renderRecaptcha() {
  if (!recaptchaContainer.value || !window.grecaptcha?.render) return
  if (recaptchaWidgetId !== null) return

  recaptchaWidgetId = window.grecaptcha.render(recaptchaContainer.value, {
    sitekey: recaptchaSiteKey,
    theme: 'light',
    callback: (token) => { recaptchaToken.value = token },
    'expired-callback': () => { recaptchaToken.value = '' },
  })
}

onMounted(async () => {
  localStorage.setItem('platform_theme', 'light')
  if (recaptchaSiteKey) {
    await loadRecaptchaScript()
    renderRecaptcha()
  }
})

usePageEntrance('#platform-login')

const route = useRoute()
const authStore = usePlatformAuthStore()
const form = reactive({
  email: '',
  password: '',
})
const localError = ref('')

authStore.hydrate()

const errorMessage = computed(() => localError.value || authStore.error)
const canSubmit = computed(() => {
  const hasCredentials = Boolean(form.email.trim()) && Boolean(form.password)
  if (recaptchaSiteKey) return hasCredentials && Boolean(recaptchaToken.value)
  return hasCredentials
})

async function handleSubmit() {
  localError.value = ''

  const email = form.email.trim()
  if (!email.includes('@')) {
    localError.value = 'Ingresa un email válido.'
    return
  }

  if (recaptchaSiteKey && !recaptchaToken.value) {
    localError.value = 'Completa el captcha para continuar.'
    return
  }

  const payload = { ...form }
  if (recaptchaToken.value) {
    payload.recaptcha_token = recaptchaToken.value
  }

  const result = await authStore.login(payload)
  if (!result.success) {
    localError.value = result.message
    if (recaptchaSiteKey && window.grecaptcha && recaptchaWidgetId !== null) {
      window.grecaptcha.reset(recaptchaWidgetId)
      recaptchaToken.value = ''
    }
    return
  }

  const localePath = useLocalePath()

  if (result.requiresVerification) {
    await navigateTo(localePath('/platform/verify'))
    return
  }

  if (authStore.needsProfileCompletion) {
    await navigateTo(localePath('/platform/complete-profile'))
    return
  }

  const redirectTarget = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
    ? route.query.redirect
    : localePath('/platform/dashboard')

  await navigateTo(redirectTarget)
}
</script>

<style scoped>
.grain-overlay {
  position: absolute;
  inset: -50%;
  width: 200%;
  height: 200%;
  z-index: 1;
  pointer-events: none;
  opacity: 0.3;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  animation: grainDrift 8s linear infinite;
}

@keyframes grainDrift {
  0% { transform: translate(0, 0); }
  25% { transform: translate(-5%, 5%); }
  50% { transform: translate(5%, -3%); }
  75% { transform: translate(-3%, -5%); }
  100% { transform: translate(0, 0); }
}
</style>
