import { ref } from 'vue'
import { useLocalePath } from '#imports'
import { create_request } from '~/stores/services/request_http'
import { writePlatformSession } from '~/composables/usePlatformApi'

export function usePanelToPlatformBridge() {
  const localePath = useLocalePath()
  const isBridging = ref(false)

  async function goToPlatform(targetPath = '/platform/dashboard') {
    if (isBridging.value) return
    isBridging.value = true
    try {
      const { data } = await create_request('accounts/session-token-bridge/')
      writePlatformSession({
        accessToken: data.tokens.access,
        refreshToken: data.tokens.refresh,
        user: data.user,
      })
      window.location.href = localePath(targetPath)
    } catch {
      window.location.href = localePath('/platform/login')
    }
  }

  return { goToPlatform, isBridging }
}
