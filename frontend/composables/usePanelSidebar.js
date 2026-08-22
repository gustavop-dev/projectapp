import { ref } from 'vue'
import { PANEL_BREAKPOINTS } from '~/config/responsive'

const STORAGE_KEY = 'panel_sidebar_collapsed'
const MOBILE_BREAKPOINT = PANEL_BREAKPOINTS.landscape
const EXPANDED_BREAKPOINT = PANEL_BREAKPOINTS.desktop

const isCollapsed = ref(false)
const isMobileOpen = ref(false)

function isClient() {
  return typeof window !== 'undefined'
}

/**
 * Collapsible sidebar + mobile drawer state for the internal admin panel (mirrors usePlatformSidebar API).
 */
export function usePanelSidebar() {
  function hydrate() {
    if (!isClient()) return
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'true') {
      isCollapsed.value = true
    } else if (stored === 'false') {
      isCollapsed.value = false
    } else {
      // Tablet landscape keeps the desktop navigation available but collapsed;
      // a laptop and larger starts expanded.
      isCollapsed.value = window.innerWidth < EXPANDED_BREAKPOINT
    }
  }

  function toggle() {
    isCollapsed.value = !isCollapsed.value
    if (isClient()) {
      localStorage.setItem(STORAGE_KEY, String(isCollapsed.value))
    }
  }

  function collapse() {
    isCollapsed.value = true
    if (isClient()) {
      localStorage.setItem(STORAGE_KEY, 'true')
    }
  }

  function expand() {
    isCollapsed.value = false
    if (isClient()) {
      localStorage.setItem(STORAGE_KEY, 'false')
    }
  }

  function openMobile() {
    isMobileOpen.value = true
  }

  function closeMobile() {
    isMobileOpen.value = false
  }

  function toggleMobile() {
    isMobileOpen.value = !isMobileOpen.value
  }

  function handleResize() {
    /* c8 ignore next */
    if (!isClient()) return
    if (window.innerWidth >= MOBILE_BREAKPOINT) {
      isMobileOpen.value = false
    }
  }

  function setupResizeListener() {
    if (!isClient()) return
    window.addEventListener('resize', handleResize)
  }

  function cleanupResizeListener() {
    if (!isClient()) return
    window.removeEventListener('resize', handleResize)
  }

  return {
    isCollapsed,
    isMobileOpen,
    hydrate,
    toggle,
    collapse,
    expand,
    openMobile,
    closeMobile,
    toggleMobile,
    setupResizeListener,
    cleanupResizeListener,
  }
}
