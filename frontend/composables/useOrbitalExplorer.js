import { computed, onBeforeUnmount, onMounted, ref, unref } from 'vue'

const MIN_ZOOM = 0.82
const MAX_ZOOM = 1.07
const ZOOM_STEP = 0.04
const AUTO_ROTATION_DEGREES_PER_SECOND = 2.4

const ORBIT_RADII = Object.freeze({
  compact: { x: 35.5, y: 39 },
  portrait: { x: 39, y: 38 },
  landscape: { x: 35, y: 38 },
  desktop: { x: 36, y: 39 },
  wide: { x: 38, y: 40 },
})

export function clampExplorerZoom(value) {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Number(value.toFixed(2))))
}

export function orbitalPosition(index, total, angle, profile = 'desktop', zoom = 1) {
  const radii = ORBIT_RADII[profile] || ORBIT_RADII.desktop
  const step = total > 0 ? 360 / total : 0
  const degrees = angle + (step * index) - 90
  const radians = degrees * (Math.PI / 180)
  const depth = (Math.sin(radians) + 1) / 2

  return {
    x: 50 + (Math.cos(radians) * radii.x * zoom),
    y: 50 + (Math.sin(radians) * radii.y * zoom),
    scale: 0.92 + (depth * 0.12),
    zIndex: Math.round(10 + (depth * 10)),
  }
}

export function useOrbitalExplorer({ isExternallyPaused = false } = {}) {
  const angle = ref(0)
  const zoom = ref(1)
  const isManuallyPaused = ref(false)
  const isHovering = ref(false)
  const hasFocusWithin = ref(false)
  const isDragging = ref(false)
  const prefersReducedMotion = ref(false)
  const isPageVisible = ref(true)
  const hasDragged = ref(false)

  const isAutoRotating = computed(() => (
    !isManuallyPaused.value
    && !isHovering.value
    && !hasFocusWithin.value
    && !isDragging.value
    && !prefersReducedMotion.value
    && isPageVisible.value
    && !unref(isExternallyPaused)
  ))

  let frameId = null
  let previousTimestamp = null
  let mediaQuery = null
  let pointerStartX = 0
  let previousPointerX = 0

  function animate(timestamp) {
    if (previousTimestamp === null) previousTimestamp = timestamp
    const elapsedSeconds = Math.min((timestamp - previousTimestamp) / 1000, 0.1)
    previousTimestamp = timestamp
    if (isAutoRotating.value) {
      angle.value = (angle.value + (AUTO_ROTATION_DEGREES_PER_SECOND * elapsedSeconds)) % 360
    }
    frameId = window.requestAnimationFrame(animate)
  }

  function updateReducedMotion(event) {
    prefersReducedMotion.value = event.matches
  }

  function updateVisibility() {
    isPageVisible.value = document.visibilityState !== 'hidden'
    previousTimestamp = null
  }

  function rotateBy(degrees) {
    angle.value = (angle.value + degrees + 360) % 360
  }

  function zoomIn() {
    zoom.value = clampExplorerZoom(zoom.value + ZOOM_STEP)
  }

  function zoomOut() {
    zoom.value = clampExplorerZoom(zoom.value - ZOOM_STEP)
  }

  function resetOrbit() {
    angle.value = 0
    zoom.value = 1
  }

  function togglePause() {
    isManuallyPaused.value = !isManuallyPaused.value
  }

  function startDrag(event) {
    if (event.pointerType === 'mouse' && event.button !== 0) return
    pointerStartX = event.clientX
    previousPointerX = event.clientX
    hasDragged.value = false
    isDragging.value = true
    event.currentTarget?.setPointerCapture?.(event.pointerId)
  }

  function moveDrag(event) {
    if (!isDragging.value) return
    const delta = event.clientX - previousPointerX
    if (Math.abs(event.clientX - pointerStartX) > 4) hasDragged.value = true
    rotateBy(delta * 0.35)
    previousPointerX = event.clientX
  }

  function endDrag(event) {
    if (!isDragging.value) return
    isDragging.value = false
    event.currentTarget?.releasePointerCapture?.(event.pointerId)
  }

  function consumeDrag() {
    if (!hasDragged.value) return false
    hasDragged.value = false
    return true
  }

  function setHovering(value) {
    isHovering.value = value
  }

  function setFocusWithin(value) {
    hasFocusWithin.value = value
  }

  onMounted(() => {
    mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    updateReducedMotion(mediaQuery)
    mediaQuery.addEventListener?.('change', updateReducedMotion)
    document.addEventListener('visibilitychange', updateVisibility)
    frameId = window.requestAnimationFrame(animate)
  })

  onBeforeUnmount(() => {
    if (frameId !== null) window.cancelAnimationFrame(frameId)
    mediaQuery?.removeEventListener?.('change', updateReducedMotion)
    document.removeEventListener('visibilitychange', updateVisibility)
  })

  return {
    angle,
    zoom,
    isManuallyPaused,
    isAutoRotating,
    isDragging,
    prefersReducedMotion,
    rotateBy,
    zoomIn,
    zoomOut,
    resetOrbit,
    togglePause,
    startDrag,
    moveDrag,
    endDrag,
    consumeDrag,
    setHovering,
    setFocusWithin,
  }
}
