import { onBeforeUnmount, onMounted, ref } from 'vue'

/**
 * Breakpoint móvil reactivo.
 *
 * Arranca en `false` (desktop-first) en SSR / primer render y se corrige en el
 * cliente al montar. Sirve para alternar entre tabla (desktop) y tarjetas
 * (móvil) con `v-if`/`v-else`, de modo que SOLO una de las dos exista en el DOM.
 *
 * Por qué v-if y no `hidden md:block` / `md:hidden`: con el toggle por CSS ambas
 * versiones quedan en el DOM (una con `display:none`), lo que duplica el texto y
 * rompe los `getByText(...)` en modo estricto de los E2E.
 */
export function useIsMobile(maxWidth = 767) {
  const isMobile = ref(false)
  let mql = null
  const update = () => { isMobile.value = !!mql && mql.matches }

  onMounted(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    mql = window.matchMedia(`(max-width: ${maxWidth}px)`)
    update()
    mql.addEventListener('change', update)
  })

  onBeforeUnmount(() => {
    if (mql) mql.removeEventListener('change', update)
  })

  return { isMobile }
}
