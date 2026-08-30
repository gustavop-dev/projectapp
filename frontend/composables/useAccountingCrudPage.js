import { getCurrentScope, onScopeDispose, ref, watch } from 'vue';

import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePagination } from '~/composables/usePagination';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useTableSort } from '~/composables/useTableSort';

const PAGE_SIZE = 15;
const HIGHLIGHT_MS = 2500;

/**
 * Shared page-controller for the accounting CRUD subviews (incomes,
 * expenses, hostings, pocket, recurring, ads). Encapsulates the block those
 * pages used to copy verbatim: create/edit modal state, submit + delete
 * flows (with panel notifications and the danger ConfirmModal), client-side
 * pagination over the filtered rows, and the saved-filter-tab handlers.
 *
 * Options:
 * - entity        store entity key ('incomes', 'expenses', ...).
 * - store         the accounting Pinia store.
 * - filteredRecords  computed list the table paginates over.
 * - labels        user-visible strings:
 *     { created, updated, deleted, saveErrorTitle, deleteErrorTitle,
 *       deleteTitle, deleteMessage(record) }
 *     `saveErrorTitle` may be a string or `(editing) => string` for pages
 *     whose create/update error titles differ.
 * - onAfterMutation()  optional async hook awaited after any successful
 *     mutation (e.g. refetch server meta). Pages whose rows carry
 *     server-computed state derived from OTHER rows must use it: mutating
 *     one row can go stale on its siblings.
 * - beforeEdit(record) / beforeDelete(record)  optional guards; returning
 *     false aborts opening the edit modal / the delete confirm.
 * - sortAccessors / sortDefaults  forwarded to useTableSort (per-column
 *     sort field overrides and first-click directions).
 * - saveTab / resetFilters / isFilterPanelOpen  from useAccountingFilters,
 *     used by handleCreateFilterTab / handleResetFilters.
 * - resetPageOn  `currentFilters` from useAccountingFilters. Narrowing the
 *     working set sends the reader back to page 1; mutating a row must not.
 *     Pages that omit it fall back to the old rows-based trigger.
 * - suppressFieldErrorNotification  leaves serializer field errors beside
 *     their controls when the caller renders `result.fieldErrors`; general
 *     failures still use the panel notification host.
 */
export function useAccountingCrudPage({
  entity,
  store,
  labels,
  filteredRecords,
  onAfterMutation = null,
  beforeEdit = null,
  beforeDelete = null,
  sortAccessors = {},
  sortDefaults = {},
  saveTab = null,
  resetFilters = null,
  isFilterPanelOpen = null,
  resetPageOn = null,
  suppressFieldErrorNotification = false,
}) {
  const notify = usePanelNotify();
  const { confirmState, requestConfirm, handleConfirmed, handleCancelled } =
    useConfirmModal();

  // -----------------------------------------------------------------
  // Column sorting + pagination over the rows
  // -----------------------------------------------------------------

  const { sortKey, sortDir, toggleSort, sortedRecords } = useTableSort(
    filteredRecords,
    { sortAccessors, sortDefaults },
  );

  const {
    currentPage,
    totalPages,
    totalItems,
    rangeFrom,
    rangeTo,
    paginatedItems: pagedRecords,
    goTo: goToPage,
    next: nextPage,
    prev: prevPage,
    reset: resetPage,
  } = usePagination(sortedRecords, { pageSize: PAGE_SIZE });

  // Back to page 1 when the FILTERS move, not when the data does. Watching the
  // rows meant every mutation reset the position — deleting a row from page 3
  // dropped the reader on page 1 — because a refetch reassigns the store array
  // whether or not the working set actually changed. Shrinking past the last
  // page is already handled: usePagination clamps currentPage to totalPages.
  if (resetPageOn) {
    watch(resetPageOn, () => resetPage(), { deep: true });
  } else {
    watch(filteredRecords, () => resetPage(), { deep: false });
  }

  // -----------------------------------------------------------------
  // Saved filter tab helpers
  // -----------------------------------------------------------------

  function handleCreateFilterTab(name) {
    if (saveTab) saveTab(name);
    if (isFilterPanelOpen) isFilterPanelOpen.value = true;
  }

  function handleResetFilters() {
    if (resetFilters) resetFilters();
    if (isFilterPanelOpen) isFilterPanelOpen.value = false;
  }

  // -----------------------------------------------------------------
  // Create / edit modal
  // -----------------------------------------------------------------

  const isModalOpen = ref(false);
  const editingRecord = ref(null);
  // Prefill for a form that still creates (duplicating a record), kept apart
  // from `editingRecord` precisely because that one decides POST vs PATCH.
  const seedRecord = ref(null);

  // Row-flash feedback: id of the last created/edited record, cleared after
  // a short delay. If sorting/filters hide the row the highlight is a no-op.
  const lastMutatedId = ref(null);
  let highlightTimer = null;

  function markMutated(id) {
    if (id === undefined || id === null) return;
    lastMutatedId.value = id;
    if (highlightTimer) clearTimeout(highlightTimer);
    highlightTimer = setTimeout(() => {
      lastMutatedId.value = null;
      highlightTimer = null;
    }, HIGHLIGHT_MS);
  }

  if (getCurrentScope()) {
    onScopeDispose(() => {
      if (highlightTimer) clearTimeout(highlightTimer);
    });
  }

  function openCreateModal() {
    editingRecord.value = null;
    seedRecord.value = null;
    isModalOpen.value = true;
  }

  function openEditModal(record) {
    if (beforeEdit && beforeEdit(record) === false) return;
    seedRecord.value = null;
    editingRecord.value = record;
    isModalOpen.value = true;
  }

  /**
   * Open the form prefilled with `seed` but still creating: `editingRecord`
   * stays null, so `handleSubmit` POSTs instead of PATCHing the record the
   * seed was copied from. This is what duplicating an income rides on.
   */
  function openSeededModal(seed) {
    editingRecord.value = null;
    seedRecord.value = seed;
    isModalOpen.value = true;
  }

  function closeModal() {
    isModalOpen.value = false;
    editingRecord.value = null;
    seedRecord.value = null;
  }

  function saveErrorTitle(editing) {
    return typeof labels.saveErrorTitle === 'function'
      ? labels.saveErrorTitle(Boolean(editing))
      : labels.saveErrorTitle;
  }

  /** Same string-or-function shape as `saveErrorTitle`, resolved lazily. */
  function resolveCopy(value, result) {
    return typeof value === 'function' ? value(result) : (value || '');
  }

  /**
   * Shared mutation flow: run the store call, then notify + row-flash +
   * onAfterMutation on success, or an error toast with the backend message.
   * Also the escape hatch for page-specific actions (liquidate, write-off)
   * so they don't re-implement this dance.
   *
   * `successTitle` and `successDetail` may be `(result) => string` when the
   * copy depends on what came back — a bulk action reporting how many rows
   * the server actually wrote, for instance.
   */
  async function runMutation(
    action,
    { successTitle, successDetail, errorTitle, flashId } = {},
  ) {
    const result = await action();
    if (result.success) {
      notify.success({
        title: resolveCopy(successTitle, result),
        detail: resolveCopy(successDetail, result),
      });
      markMutated(flashId ?? result.data?.id);
      if (onAfterMutation) await onAfterMutation();
    } else if (!(suppressFieldErrorNotification && result.fieldErrors)) {
      notify.error({ title: errorTitle, detail: result.message || '' });
    }
    return result;
  }

  /**
   * Title for a successful save. A seeded create is a duplicate, and saying
   * so is what tells it apart from a manual one in the notification history —
   * pages that define no `duplicated` copy keep the plain created wording.
   */
  function saveSuccessTitle(editing, seeded) {
    if (editing) return labels.updated;
    return (seeded && labels.duplicated) || labels.created;
  }

  async function handleSubmit(payload) {
    const editing = editingRecord.value;
    // Read before the mutation: closeModal() clears the seed on success.
    const seeded = !editing && !!seedRecord.value;
    const result = await runMutation(
      () => (editing
        ? store.updateRecord(entity, editing.id, payload)
        : store.createRecord(entity, payload)),
      {
        successTitle: saveSuccessTitle(editing, seeded),
        errorTitle: saveErrorTitle(editing),
        flashId: editing?.id,
      },
    );
    if (result.success) closeModal();
    // Pages that react to what came back (e.g. offering a follow-up on the
    // created row) need the result; existing callers ignore it.
    return result;
  }

  // -----------------------------------------------------------------
  // Delete
  // -----------------------------------------------------------------

  function confirmDeleteRecord(record) {
    if (beforeDelete && beforeDelete(record) === false) return;
    requestConfirm({
      title: labels.deleteTitle,
      message: labels.deleteMessage(record),
      variant: 'danger',
      confirmText: 'Eliminar',
      cancelText: 'Cancelar',
      onConfirm: () => runMutation(
        () => store.deleteRecord(entity, record.id),
        { successTitle: labels.deleted, errorTitle: labels.deleteErrorTitle },
      ),
    });
  }

  return {
    // modal
    isModalOpen,
    editingRecord,
    seedRecord,
    openCreateModal,
    openEditModal,
    openSeededModal,
    closeModal,
    handleSubmit,
    // row-flash feedback
    lastMutatedId,
    // delete confirm
    confirmDeleteRecord,
    confirmState,
    handleConfirmed,
    handleCancelled,
    // escape hatches for page-specific row actions, so they reuse this
    // controller's ConfirmModal and mutation flow (notify + flash + hook)
    requestConfirm,
    runMutation,
    // sorting
    sortKey,
    sortDir,
    toggleSort,
    // The sorted set behind the current page: a deep link needs it to work
    // out WHICH page holds the row it was sent to.
    sortedRecords,
    // pagination
    pageSize: PAGE_SIZE,
    currentPage,
    totalPages,
    totalItems,
    rangeFrom,
    rangeTo,
    pagedRecords,
    prevPage,
    nextPage,
    goToPage,
    // filter tab helpers
    handleCreateFilterTab,
    handleResetFilters,
  };
}
