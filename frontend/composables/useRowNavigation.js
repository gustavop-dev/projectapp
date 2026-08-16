import { rowActivationIntent } from '~/utils/rowNavigation';

/**
 * The convenience half of a row link.
 *
 * The mandatory half lives in the template: the title cell renders a real
 * <BaseRowLink :to="href">. `openRow` makes the REST of the row react to the
 * same address with the same rules the browser applies to that anchor, and
 * stays out of the way everywhere the browser already does the right thing.
 *
 * `to` must be a fully resolved path. The caller runs it through
 * `useLocalePath()` ONCE and hands the SAME string to the anchor and to this
 * function, so the row and its link can never drift apart — i18n runs with
 * strategy 'prefix', so an unprefixed path is a broken address.
 */
export function useRowNavigation() {
  const router = useRouter();

  function hasTextSelection() {
    if (typeof window === 'undefined' || !window.getSelection) return false;
    const selection = window.getSelection();
    return !!selection && !selection.isCollapsed && selection.toString().trim().length > 0;
  }

  /**
   * @param {string} to Resolved, locale-prefixed path. Falsy means the row has
   *   no detail to open — nothing happens.
   * @param {MouseEvent} [event] Absent for a programmatic call.
   */
  function openRow(to, event) {
    if (!to) return;
    const intent = rowActivationIntent(event, { hasTextSelection });
    if (intent === 'ignore') return;
    if (intent === 'new-tab') {
      // Same-origin panel URLs. The plain two-argument form is what reliably
      // yields a TAB rather than a popup window.
      window.open(to, '_blank');
      return;
    }
    router.push(to);
  }

  return { openRow };
}
