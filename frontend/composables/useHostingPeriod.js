import { computed, nextTick, ref, watch } from 'vue'
import { useAccountingStore } from '~/stores/accounting'
import { nextPeriodEnd, todayISO } from '~/utils/periodDates'
import { CUSTOM_FREQUENCY } from '~/utils/recurring'

/**
 * The covered-period block of a hosting income: start, end and cadence kept
 * consistent with each other.
 *
 * One idea holds the whole thing together — the ANCHOR, the start of the first
 * period not yet on the book. Picking a cadence with no start proposes it, and
 * every shortcut opens its window there, so clicking `+1 año` and then
 * `+1 mes` re-lengthens the same period instead of walking two periods into
 * the future. Where the anchor comes from depends on how the form was opened:
 *
 * * duplicating — the start the draft arrived with, which the backend already
 *   computed as the original's end plus a day;
 * * creating — the day after the last window recorded for that client, or
 *   today when it is their first charge (resolved server-side, since the form
 *   has no list of the client's incomes to look it up in);
 * * editing — none: the record already opened its period, and a shortcut has
 *   no business moving a charge that is already on the book.
 *
 * The dates are computed here rather than server-side, `add_months` clamp
 * included (see `~/utils/periodDates`), because the requirement is that they
 * move the instant a cadence is picked — a round trip per keystroke cannot
 * deliver that.
 */
export function useHostingPeriod(form, { isHosting, isEdit, isDuplicate, seed }) {
  const store = useAccountingStore()

  /** Start of the next period not yet recorded. '' while unknown. */
  const anchorStart = ref('')
  /** End of the last recorded period, for the hint. '' when there is none. */
  const previousPeriodEnd = ref('')

  // Hydration writes start, end and cadence as one batch out of a stored
  // record. Recomputing in the middle of that would overwrite the end that was
  // actually saved with the one the cadence implies — which is exactly the
  // disagreement a legacy row is allowed to carry.
  const hydrating = ref(false)

  function beginHydration() {
    hydrating.value = true
    nextTick(() => {
      hydrating.value = false
    })
  }

  function proposedEnd() {
    return nextPeriodEnd(form.value.period_start, form.value.period_cadence)
  }

  /** Write the end the current cadence implies, when it implies one. */
  function applyProposedEnd() {
    const end = proposedEnd()
    if (end) form.value.period_end = end
  }

  watch(
    () => form.value.period_cadence,
    (cadence) => {
      if (!isHosting.value || hydrating.value) return
      // `custom` is the escape hatch: both dates are written by hand and
      // nothing is proposed over them.
      if (!cadence || cadence === CUSTOM_FREQUENCY) return
      if (!form.value.period_start) {
        form.value.period_start = anchorStart.value || todayISO()
      }
      applyProposedEnd()
    },
  )

  watch(
    () => form.value.period_start,
    () => {
      if (!isHosting.value || hydrating.value) return
      applyProposedEnd()
    },
  )

  /**
   * The end was typed by hand. A cadence that no longer describes the window
   * would be the form stating two things that contradict each other, so the
   * selector steps back to `custom` and stops proposing.
   */
  function onPeriodEndEdited(value) {
    if (!isHosting.value || !value) return
    const cadence = form.value.period_cadence
    if (!cadence || cadence === CUSTOM_FREQUENCY) return
    if (value === proposedEnd()) return
    form.value.period_cadence = CUSTOM_FREQUENCY
  }

  // Mirrors CYCLE_OPTION_MONTHS on the backend. Bimestral and the longer
  // cadences stay selector-only: four buttons is the point of a shortcut.
  const CYCLE_MONTHS = [1, 3, 6, 12]
  const MONTHS_TO_CADENCE = { 1: 'monthly', 3: 'quarterly', 6: 'semiannual', 12: 'annual' }

  /**
   * Shortcuts to the next period. A hosting form offers them whenever it is
   * opening a period — creating or duplicating — and never while editing one
   * already recorded. Outside hosting they remain what they were: the dates
   * the duplicate draft computed for a single-date income.
   */
  const cycleOptions = computed(() => {
    if (isHosting.value) {
      return isEdit.value ? [] : CYCLE_MONTHS.map((months) => ({ months }))
    }
    return isDuplicate.value ? seed.value?.cycle_options ?? [] : []
  })

  function isCycleActive(option) {
    if (!isHosting.value) return false
    // Both halves, so a window the operator has since moved does not keep
    // claiming to be the one this button opens.
    return form.value.period_cadence === MONTHS_TO_CADENCE[option.months]
      && !!form.value.period_start
      && form.value.period_start === (anchorStart.value || todayISO())
  }

  function applyCycle(option) {
    const cadence = MONTHS_TO_CADENCE[option.months]
    if (!cadence) return
    form.value.period_start = anchorStart.value || todayISO()
    form.value.period_cadence = cadence
    // The watchers cover every path except the one where neither value
    // actually changed (clicking the active shortcut twice).
    applyProposedEnd()
  }

  const periodEndError = computed(() => {
    if (!isHosting.value) return ''
    const { period_start: start, period_end: end } = form.value
    if (!start || !end) return ''
    // Same rule and same wording as the write serializer, so the form and the
    // server never disagree about what is wrong.
    return end <= start ? 'La fecha de fin debe ser posterior a la de inicio.' : ''
  })

  /**
   * Resolve the anchor for the way this form was opened. Duplicating already
   * carries it; creating has to ask. Editing keeps none on purpose.
   */
  async function resolveAnchor() {
    if (!isHosting.value || isEdit.value) {
      anchorStart.value = ''
      previousPeriodEnd.value = ''
      return
    }
    if (isDuplicate.value) {
      // The draft already opened on the period after the original — including
      // the legacy path where that start was derived from a bare date. Read it
      // off the form, which is where the prefill landed, and never re-resolve
      // it: the anchor is where this duplicate STARTED, so moving the dates
      // afterwards must not move what the shortcuts count from.
      anchorStart.value = form.value.period_start || ''
      previousPeriodEnd.value = ''
      return
    }
    const requestedFor = form.value.client
    const result = await store.fetchIncomePeriodSuggestion({
      client: form.value.client,
      project: form.value.project,
    })
    // The operator may have moved on to another client while this was in
    // flight; answering for the previous one would fill in a stranger's dates.
    if (form.value.client !== requestedFor) return
    if (!result.success) {
      anchorStart.value = todayISO()
      previousPeriodEnd.value = ''
      return
    }
    anchorStart.value = result.data?.suggested_start || todayISO()
    previousPeriodEnd.value = result.data?.previous_period_end || ''
  }

  return {
    anchorStart,
    previousPeriodEnd,
    beginHydration,
    cycleOptions,
    isCycleActive,
    applyCycle,
    onPeriodEndEdited,
    periodEndError,
    resolveAnchor,
  }
}
