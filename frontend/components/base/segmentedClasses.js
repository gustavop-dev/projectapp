/**
 * Presentation shared by BaseSegmented (single choice) and BaseSegmentedMulti
 * (checkable, for filter dimensions).
 *
 * The two components differ in their accessibility contract, not in how they
 * look: one is a tablist of mutually exclusive tabs, the other a group of
 * toggle buttons. Keeping the classes here is what stops the filter panel and
 * the form modals from drifting apart visually while they stay apart
 * semantically.
 */

export const SEGMENTED_WRAPPER =
  'inline-flex max-w-full flex-wrap items-stretch gap-1 rounded-xl bg-surface-raised p-1'

export const SEGMENTED_SIZE = {
  sm: 'px-2.5 py-1 text-xs',
  md: 'px-3 py-2 text-sm',
}

export const SEGMENTED_ITEM_BASE =
  'inline-flex min-h-8 flex-1 items-center justify-center self-stretch whitespace-nowrap rounded-lg outline-none transition-all focus:ring-2 focus:ring-focus-ring/40'

export const SEGMENTED_ITEM_ON = 'bg-surface shadow-sm font-medium text-text-default'

export const SEGMENTED_ITEM_OFF = 'text-text-muted hover:text-text-default'

export const SEGMENTED_ITEM_DISABLED = 'opacity-60 cursor-not-allowed'

/**
 * `[{ value, label, testId?, disabled? }]` or bare strings/numbers, normalized
 * to the object form both components render.
 */
export function normalizeSegmentedOptions(options) {
  return (options || []).map((opt) =>
    typeof opt === 'object' && opt !== null
      ? {
          value: opt.value,
          label: opt.label ?? String(opt.value),
          testId: opt.testId,
          // Per-option lock, on top of the control-wide `disabled`: a filter can
          // have one choice that does not apply yet while the rest stay live.
          disabled: opt.disabled === true,
          disabledReason: opt.disabledReason || '',
        }
      : { value: opt, label: String(opt), disabled: false, disabledReason: '' },
  )
}
