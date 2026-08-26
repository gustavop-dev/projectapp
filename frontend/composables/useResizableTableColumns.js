import {
  computed, nextTick, onBeforeUnmount, onMounted, ref, unref, watch,
} from 'vue'

function clamp(value, config) {
  const parsed = Number(value)
  const fallback = Number(config.default)
  if (!Number.isFinite(parsed)) return fallback
  return Math.min(Number(config.max), Math.max(Number(config.min), parsed))
}

function readStored(key) {
  if (!key || typeof window === 'undefined') return {}
  try {
    const parsed = JSON.parse(window.localStorage.getItem(key) || '{}')
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {}
  } catch (_error) {
    return {}
  }
}

function writeStored(key, value) {
  if (!key || typeof window === 'undefined') return
  try {
    if (Object.keys(value).length) window.localStorage.setItem(key, JSON.stringify(value))
    else window.localStorage.removeItem(key)
  } catch (_error) { /* Storage is an enhancement; layout still works without it. */ }
}

export function resolveResizableColumnWidths(
  columns,
  preferred = {},
  visibleKeys = null,
  available = 0,
) {
  const keySet = visibleKeys ? new Set(visibleKeys) : null
  const visible = columns.filter((column) => !keySet || keySet.has(column.key))
  const widths = Object.fromEntries(visible.map((column) => [
    column.key,
    column.columnWidth.default,
  ]))
  const donors = visible
    .filter((column) => column.columnWidth.shrinkPriority !== null
      && !column.columnWidth.fixed && !column.columnWidth.resizable)
    .sort((a, b) => a.columnWidth.shrinkPriority - b.columnWidth.shrinkPriority)
  const fillers = visible
    .filter((column) => column.columnWidth.fillPriority !== null
      && !column.columnWidth.fixed && !column.columnWidth.resizable)
    .sort((a, b) => a.columnWidth.fillPriority - b.columnWidth.fillPriority)

  function totalWidth() {
    return Object.values(widths).reduce((sum, width) => sum + width, 0)
  }

  function shrinkToFit(deficit) {
    let remaining = deficit
    for (const donor of donors) {
      if (remaining <= 0) break
      const room = widths[donor.key] - donor.columnWidth.min
      const taken = Math.min(room, remaining)
      widths[donor.key] -= taken
      remaining -= taken
    }
  }

  function fillSpace(surplus) {
    let remaining = surplus
    for (const filler of fillers) {
      if (remaining <= 0) break
      const room = filler.columnWidth.max - widths[filler.key]
      const given = Math.min(room, remaining)
      widths[filler.key] += given
      remaining -= given
    }
  }

  // First resolve the table at its default resizable widths. Preferences are
  // applied afterwards so an enlarged column takes space from donors in the
  // declared business order even when the viewport had spare room initially.
  if (available > 0) {
    const baselineTotal = totalWidth()
    if (baselineTotal > available) shrinkToFit(baselineTotal - available)
    else if (baselineTotal < available) fillSpace(available - baselineTotal)
  }

  for (const column of visible) {
    if (!column.columnWidth.resizable) continue
    widths[column.key] = clamp(preferred[column.key], column.columnWidth)
  }

  if (available > 0) {
    const preferredTotal = totalWidth()
    if (preferredTotal > available) shrinkToFit(preferredTotal - available)
    else if (preferredTotal < available) fillSpace(available - preferredTotal)
  }

  const total = totalWidth()
  return { widths, minWidth: Math.max(total, available || 0) }
}

/**
 * Shared width engine for real tables. Consumers declare every track with a
 * `columnWidth` policy. Resizable preferences stay exact; when space runs out,
 * donor columns shrink in `shrinkPriority` order until their floor, then the
 * table scrolls inside its own wrapper.
 */
export function useResizableTableColumns({
  columns,
  containerRef,
  storageKey = '',
  visibleKeys = null,
}) {
  const containerWidth = ref(0)
  const preferred = ref({})
  const draggingKey = ref(null)
  const dragStartX = ref(0)
  const dragStartWidth = ref(0)
  let observer = null

  const normalized = computed(() => unref(columns).map((column) => ({
    ...column,
    columnWidth: {
      min: Number(column.columnWidth.min),
      default: Number(column.columnWidth.default),
      max: Number(column.columnWidth.max),
      resizable: Boolean(column.columnWidth.resizable),
      fixed: Boolean(column.columnWidth.fixed),
      shrinkPriority: Number.isFinite(column.columnWidth.shrinkPriority)
        ? Number(column.columnWidth.shrinkPriority)
        : null,
      fillPriority: Number.isFinite(column.columnWidth.fillPriority)
        ? Number(column.columnWidth.fillPriority)
        : null,
    },
  })))

  watch(normalized, (nextColumns) => {
    const stored = readStored(storageKey)
    const next = {}
    for (const column of nextColumns) {
      if (!column.columnWidth.resizable) continue
      const current = preferred.value[column.key]
      next[column.key] = clamp(current ?? stored[column.key], column.columnWidth)
    }
    preferred.value = next
  }, { immediate: true, deep: true })

  const layout = computed(() => resolveResizableColumnWidths(
    normalized.value,
    preferred.value,
    visibleKeys ? unref(visibleKeys) : null,
    containerWidth.value,
  ))

  const tableStyle = computed(() => ({
    tableLayout: 'fixed',
    minWidth: `${Math.ceil(layout.value.minWidth)}px`,
  }))

  function preferredWidth(key) {
    const column = normalized.value.find((item) => item.key === key)
    return column?.columnWidth.resizable
      ? clamp(preferred.value[key], column.columnWidth)
      : layout.value.widths[key]
  }

  function columnStyle(key) {
    const width = layout.value.widths[key]
    return width ? { width: `${Math.round(width)}px` } : {}
  }

  function persist() {
    const custom = {}
    for (const column of normalized.value) {
      if (!column.columnWidth.resizable) continue
      const width = clamp(preferred.value[column.key], column.columnWidth)
      if (width !== column.columnWidth.default) custom[column.key] = width
    }
    writeStored(storageKey, custom)
  }

  function resizeTo(key, value, shouldPersist = true) {
    const column = normalized.value.find((item) => item.key === key)
    if (!column?.columnWidth.resizable) return
    preferred.value = { ...preferred.value, [key]: clamp(value, column.columnWidth) }
    if (shouldPersist) persist()
  }

  function reset(key) {
    const column = normalized.value.find((item) => item.key === key)
    if (!column?.columnWidth.resizable) return
    preferred.value = { ...preferred.value, [key]: column.columnWidth.default }
    persist()
  }

  function onPointerStart(key, event) {
    draggingKey.value = key
    dragStartX.value = event.clientX
    dragStartWidth.value = preferredWidth(key)
  }

  function onPointerMove(key, event) {
    if (draggingKey.value !== key) return
    resizeTo(key, dragStartWidth.value + event.clientX - dragStartX.value, false)
  }

  function onPointerEnd(key) {
    if (draggingKey.value !== key) return
    draggingKey.value = null
    persist()
  }

  function measureContainer() {
    containerWidth.value = containerRef.value?.clientWidth
      || containerRef.value?.getBoundingClientRect?.().width
      || 0
  }

  function observeContainer() {
    observer?.disconnect()
    measureContainer()
    if (!containerRef.value || typeof ResizeObserver === 'undefined') return
    observer = new ResizeObserver((entries) => {
      containerWidth.value = entries[0]?.contentRect?.width || 0
    })
    observer.observe(containerRef.value)
  }

  onMounted(async () => {
    await nextTick()
    observeContainer()
    window.addEventListener('resize', measureContainer)
  })
  onBeforeUnmount(() => {
    observer?.disconnect()
    window.removeEventListener('resize', measureContainer)
  })

  return {
    columnStyle,
    draggingKey,
    onPointerEnd,
    onPointerMove,
    onPointerStart,
    preferredWidth,
    reset,
    resizeTo,
    tableStyle,
  }
}
