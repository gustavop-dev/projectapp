<template>
  <div :class="{ dark: isDark }" id="platform-login" class="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
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

    <button
      type="button"
      class="fixed right-4 top-4 z-20 flex h-9 w-9 items-center justify-center rounded-full border border-white/10 text-white/60 transition hover:text-white"
      aria-label="Cambiar tema"
      @click="toggle"
    >
      <svg v-if="isDark" class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
      <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
    </button>

    <div class="relative z-10 w-full max-w-md">
      <div class="mb-10 text-center" data-enter>
        <h1 class="font-bold text-2xl tracking-tight text-white">
          Project<span class="text-white/60">App.</span>
        </h1>
        <p class="mt-2 text-sm font-medium uppercase tracking-[0.25em] text-white/50">Portal</p>
      </div>

      <div class="rounded-3xl border border-white/[0.1] bg-white/95 p-8 shadow-2xl backdrop-blur-2xl dark:border-white/[0.06] dark:bg-white/[0.08] dark:shadow-black/30" data-enter>
        <h2 class="text-xl font-medium text-esmerald dark:text-white">Inicia sesión</h2>
        <p class="mt-2 text-sm leading-6 text-green-light">
          Ingresa con tu email y contraseña para acceder al portal.
        </p>

        <div v-if="errorMessage" class="mt-6 rounded-2xl border border-red-500/20 bg-red-50 px-4 py-3 text-sm text-red-600 dark:bg-red-500/10 dark:text-red-200">
          {{ errorMessage }}
        </div>

        <form class="mt-8 space-y-5" @submit.prevent="handleSubmit">
          <div>
            <label for="platform-email" class="mb-2 block text-sm font-medium text-esmerald/70 dark:text-white/70">Email</label>
            <input
              id="platform-email"
              v-model="form.email"
              type="email"
              autocomplete="email"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/60 focus:border-esmerald/30 focus:ring-1 focus:ring-esmerald/10 dark:border-white/[0.08] dark:bg-white/[0.06] dark:text-white dark:placeholder:text-white/30 dark:focus:border-white/20 dark:focus:ring-white/10"
              placeholder="cliente@empresa.com"
            >
          </div>

          <div>
            <label for="platform-password" class="mb-2 block text-sm font-medium text-esmerald/70 dark:text-white/70">Contraseña</label>
            <input
              id="platform-password"
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/60 focus:border-esmerald/30 focus:ring-1 focus:ring-esmerald/10 dark:border-white/[0.08] dark:bg-white/[0.06] dark:text-white dark:placeholder:text-white/30 dark:focus:border-white/20 dark:focus:ring-white/10"
              placeholder="••••••••"
            >
          </div>

          <button
            type="submit"
            class="w-full rounded-full bg-esmerald px-4 py-3 text-sm font-semibold text-white transition hover:bg-esmerald/90 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-lemon dark:text-esmerald-dark dark:hover:bg-lemon/90"
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
import { usePlatformTheme } from '~/composables/usePlatformTheme'
import BackgroundGradientAnimation from '~/components/ui/BackgroundGradientAnimation.vue'

definePageMeta({
  layout: false,
  middleware: ['platform-auth'],
})

useHead({
  title: 'Acceso a plataforma — ProjectApp',
})

const { isDark, toggle, hydrate: hydrateTheme } = usePlatformTheme()
onMounted(() => hydrateTheme())

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
const canSubmit = computed(() => Boolean(form.email.trim()) && Boolean(form.password))

async function handleSubmit() {
  localError.value = ''

  const email = form.email.trim()
  if (!email.includes('@')) {
    localError.value = 'Ingresa un email válido.'
    return
  }

  const result = await authStore.login(form)
  if (!result.success) {
    localError.value = result.message
    return
  }

  if (result.requiresVerification) {
    await navigateTo('/platform/verify')
    return
  }

  if (authStore.needsProfileCompletion) {
    await navigateTo('/platform/complete-profile')
    return
  }

  const redirectTarget = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/platform')
    ? route.query.redirect
    : '/platform/dashboard'

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
