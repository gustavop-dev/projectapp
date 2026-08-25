import { onBeforeUnmount, onMounted, ref } from 'vue'
import { PANEL_BREAKPOINTS } from '~/config/responsive'

export function panelProfileForWidth(width) {
  if (width >= PANEL_BREAKPOINTS.wide) return 'wide'
  if (width >= PANEL_BREAKPOINTS.desktop) return 'desktop'
  if (width >= PANEL_BREAKPOINTS.landscape) return 'landscape'
  if (width >= PANEL_BREAKPOINTS.portrait) return 'portrait'
  return 'compact'
}

export function usePanelViewportProfile() {
  // Desktop-first matches the existing SSR contract of useIsMobile.
  const profile = ref('desktop')
  const update = () => { profile.value = panelProfileForWidth(window.innerWidth) }

  onMounted(() => {
    update()
    window.addEventListener('resize', update)
  })
  onBeforeUnmount(() => window.removeEventListener('resize', update))

  return { profile }
}
