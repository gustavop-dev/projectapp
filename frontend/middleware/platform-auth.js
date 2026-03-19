import { usePlatformAuthStore } from '~/stores/platform-auth'

export default defineNuxtRouteMiddleware(async (to) => {
  // Strip optional i18n locale prefix (e.g. /en-us, /es-co) for path matching
  const rawPath = to.path.replace(/^\/[a-z]{2}(-[a-z]{2})?(?=\/)/, '')

  if (!rawPath.startsWith('/platform')) return

  const authStore = usePlatformAuthStore()
  authStore.hydrate()

  const isLoginPage = rawPath === '/platform/login'
  const isVerifyPage = rawPath === '/platform/verify'
  const isCompleteProfilePage = rawPath === '/platform/complete-profile'
  const redirectTarget = `/platform/login?redirect=${encodeURIComponent(to.fullPath)}`

  if (authStore.accessToken && !authStore.hasValidatedSession) {
    const result = await authStore.fetchMe()
    if (!result.success) {
      authStore.logout()
      if (!isLoginPage && !isVerifyPage) {
        return navigateTo(redirectTarget)
      }
    }
  }

  if (isLoginPage) {
    if (authStore.isAuthenticated && authStore.isOnboarded) {
      if (authStore.needsProfileCompletion) {
        return navigateTo('/platform/complete-profile')
      }
      return navigateTo('/platform/dashboard')
    }

    if (authStore.hasVerificationToken && !authStore.isOnboarded) {
      return navigateTo('/platform/verify')
    }

    return
  }

  if (isVerifyPage) {
    if (authStore.isAuthenticated && authStore.isOnboarded) {
      if (authStore.needsProfileCompletion) {
        return navigateTo('/platform/complete-profile')
      }
      return navigateTo('/platform/dashboard')
    }

    if (!authStore.hasVerificationToken && !authStore.isAuthenticated) {
      return navigateTo('/platform/login')
    }

    return
  }

  if (!authStore.accessToken) {
    return navigateTo(redirectTarget)
  }

  if (!authStore.isOnboarded) {
    return navigateTo('/platform/verify')
  }

  if (isCompleteProfilePage) {
    if (authStore.profileCompleted) {
      return navigateTo('/platform/dashboard')
    }
    return
  }

  if (authStore.needsProfileCompletion) {
    return navigateTo('/platform/complete-profile')
  }

  if (to.meta.platformRole === 'admin' && authStore.role !== 'admin') {
    return navigateTo('/platform/dashboard')
  }

  if (to.meta.platformRole === 'client' && authStore.role !== 'client') {
    return navigateTo('/platform/dashboard')
  }
})
