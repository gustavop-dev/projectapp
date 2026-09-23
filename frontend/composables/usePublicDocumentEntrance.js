import { onMounted, onBeforeUnmount, onUpdated } from 'vue'

/** Animate sections once as they enter, without hiding prerendered content.
 * Register after updates too: the public catalog refreshes after hydration.
 * Only section wrappers opt in; fixed actions must stay outside them.
 */
export function usePublicDocumentEntrance(container) {
  const seen = new WeakSet()
  const pending = new Set()
  let observer

  function refresh() {
    if (!observer || !container.value) return
    for (const element of pending) {
      if (!container.value.contains(element)) {
        observer.unobserve(element)
        pending.delete(element)
      }
    }
    for (const element of container.value.querySelectorAll('[data-document-enter]')) {
      if (seen.has(element) || pending.has(element)) continue
      pending.add(element)
      observer.observe(element)
    }
  }

  onMounted(() => {
    if (typeof IntersectionObserver === 'undefined') return
    observer = new IntersectionObserver((entries) => {
      for (const { target, isIntersecting } of entries) {
        if (!isIntersecting || seen.has(target)) continue
        seen.add(target)
        if (!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
          target.classList.add('public-document-entered')
        }
        observer.unobserve(target)
        pending.delete(target)
      }
    }, { rootMargin: '0px 0px -24px 0px', threshold: 0 })
    refresh()
  })

  onUpdated(refresh)
  onBeforeUnmount(() => {
    observer?.disconnect()
    pending.clear()
  })
}
