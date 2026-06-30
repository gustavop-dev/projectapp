<template>
  <div class="flex min-h-screen items-center justify-center bg-surface px-4 text-sm text-text-subtle">
    {{ message }}
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'

// No platform-auth middleware: this page establishes the session itself.
definePageMeta({ layout: false })

useHead({ title: 'Iniciando sesión — ProjectApp' })

const route = useRoute()
const localePath = useLocalePath()
const authStore = usePlatformAuthStore()
const message = ref('Iniciando sesión...')

onMounted(async () => {
  localStorage.setItem('platform_theme', 'light')

  const access = typeof route.query.access === 'string' ? route.query.access : ''
  const refresh = typeof route.query.refresh === 'string' ? route.query.refresh : ''

  if (!access || !refresh) {
    await navigateTo(localePath('/platform/login'))
    return
  }

  authStore.applyAuthenticatedSession({ access, refresh }, null)
  const result = await authStore.fetchMe()

  if (!result.success) {
    message.value = 'No pudimos iniciar la sesión.'
    await navigateTo(localePath('/platform/login'))
    return
  }

  const redirect = route.query.redirect
  const target = typeof redirect === 'string' && redirect.startsWith('/platform/')
    ? redirect
    : '/platform/dashboard'

  await navigateTo(localePath(target))
})
</script>
