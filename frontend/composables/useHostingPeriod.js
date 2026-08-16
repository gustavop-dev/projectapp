import { computed, nextTick, ref, watch } from 'vue'
import { useAccountingStore } from '~/stores/accounting'
import { addMonths, nextPeriodEnd, todayISO } from '~/utils/periodDates'
import { CUSTOM_FREQUENCY, FREQUENCY_MONTHS } from '~/utils/recurring'

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
 * * duplicating — `period_anchor` on the draft, which states what the count
 *   starts from: the original's recorded window (fixed at its end plus a day),
 *   its hosting cycle (fixed too), or — when the original has neither, the
 *   normal case until the book is completed — the original's own DATE, which
 *   only implies a start once a cadence states how long that period lasted.
 *   That last anchor floats: picking another cadence moves the whole window,
 *   because the end it is counting from is precisely what was never recorded;
 * * creating — the day after the last window recorded for that client, or
 *   today when it is their first charge (resolved server-side, since the form
 *   has no list of the client's incomes to look it up in);
 * * editing — none: the record already opened its period, and a shortcut has
 *   no business moving a charge that is already on the book.
 *
 * Today is the last resort and nothing else: a window opened on today chains
 * with nothing, so it is reached only when the original carries no date at
 * all, and the form says as much when it happens.
 *
 * The dates are computed here rather than server-side, `add_months` clamp
 * included (see `~/utils/periodDates`), because the requirement is that they
 * move the instant a cadence is picked — a round trip per keystroke cannot
 * deliver that.
 */
export function useHostingPeriod(form, { isHosting, isEdit, isDuplicate, seed }) {
  const store = useAccountingStore()

  /** Start of the next period not yet recorded, when it is already fixed. */
  const anchorStart = ref('')
  /** What that start was read off, for the notice. '' outside a duplicate. */
  const anchorSource = ref('')
  /** The original's own date: the floating anchor's ground. */
  const anchorOriginDate = ref('')
  /** The original's recorded window, so the notice can name it. */
  const anchorOriginStart = ref('')
  const anchorOriginEnd = ref('')
  /** End of the last recorded period, for the hint. '' when there is none. */
  const previousPeriodEnd = ref('')
  /**
   * The last start this composable proposed. What tells apart a start the
   * anchor put there — which a new cadence may move — from one the operator
   * wrote, which it may not.
   */
  const proposedStart = ref('')

  // Hydration writes start, end and cadence as one batch out of a stored
  // record. Recomputing in the middle of that would overwrite the end that was
  // actually saved with the one the cadence implies — which is exactly the
  // disagreement a legacy row is allowed to carry.
  const hydrating = ref(false)

  function beginHydration() {
    hydrating.value = true
    // A fresh form has nothing proposed by us yet: whatever start it opens
    // with came from the record or the draft, so a cadence must not move it.
    proposedStart.value = ''
    nextTick(() => {
      hydrating.value = false
    })
  }

  /**
   * The start this window opens on under `cadence`. A recorded antecedent
   * fixes it and the cadence changes nothing; an original with only a date
   * implies its own length from the cadence, so the window opens where that
   * period would have closed. Today only when there is neither.
   */
  function anchorFor(cadence) {
    if (anchorStart.value) return anchorStart.value
    const months = FREQUENCY_MONTHS[cadence]
    if (anchorOriginDate.value && months) {
      return addMonths(anchorOriginDate.value, months)
    }
    return todayISO()
  }

  /** Propose a start, remembering it was us and not the operator. */
  function writeStart(value) {
    form.value.period_start = value
    proposedStart.value = value
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
      // A start the anchor proposed is still the anchor's to move: under a
      // floating anchor the whole window slides, since the length just chosen
      // is what decides where the original's period closed. One the operator
      // wrote stays put — the cadence recomputes the end around it.
      if (!form.value.period_start || form.value.period_start === proposedStart.value) {
        writeStart(anchorFor(cadence))
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
    const cadence = MONTHS_TO_CADENCE[option.months]
    return form.value.period_cadence === cadence
      && !!form.value.period_start
      && form.value.period_start === anchorFor(cadence)
  }

  function applyCycle(option) {
    const cadence = MONTHS_TO_CADENCE[option.months]
    if (!cadence) return
    writeStart(anchorFor(cadence))
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
  function clearAnchor() {
    anchorStart.value = ''
    anchorSource.value = ''
    anchorOriginDate.value = ''
    anchorOriginStart.value = ''
    anchorOriginEnd.value = ''
    previousPeriodEnd.value = ''
  }

  async function resolveAnchor() {
    if (!isHosting.value || isEdit.value) {
      clearAnchor()
      return
    }
    if (isDuplicate.value) {
      // Read off the draft, not off the form: the form only shows a start when
      // the backend had one to propose, and the case this exists for is the
      // one where it did not. `period_anchor` still says what to count from —
      // the original's date — so the window opens on the original rather than
      // on today. The form's own start is the fallback for a draft built
      // before this contract, and never re-resolved afterwards: the anchor is
      // where this duplicate STARTED, so moving the dates by hand must not
      // move what the shortcuts count from.
      const anchor = seed.value?.period_anchor || null
      clearAnchor()
      // '' and 'none' are different answers: the first is a draft built before
      // this contract, the second is one that looked and found nothing to
      // chain with. Only the second is worth telling the operator about.
      if (anchor) anchorSource.value = anchor.source || 'none'
      anchorStart.value = anchor?.start || form.value.period_start || ''
      anchorOriginDate.value = anchor?.origin_date || ''
      anchorOriginStart.value = anchor?.origin_start || ''
      anchorOriginEnd.value = anchor?.origin_end || ''
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
    anchorSource,
    anchorOriginDate,
    anchorOriginStart,
    anchorOriginEnd,
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
