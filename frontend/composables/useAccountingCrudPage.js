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

  watch(filteredRecords, () => resetPage(), { deep: false });

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
    isModalOpen.value = true;
  }

  function openEditModal(record) {
    if (beforeEdit && beforeEdit(record) === false) return;
    editingRecord.value = record;
    isModalOpen.value = true;
  }

  function closeModal() {
    isModalOpen.value = false;
    editingRecord.value = null;
  }

  function saveErrorTitle(editing) {
    return typeof labels.saveErrorTitle === 'function'
      ? labels.saveErrorTitle(Boolean(editing))
      : labels.saveErrorTitle;
  }

  /**
   * Shared mutation flow: run the store call, then notify + row-flash +
   * onAfterMutation on success, or an error toast with the backend message.
   * Also the escape hatch for page-specific actions (liquidate, write-off)
   * so they don't re-implement this dance.
   */
  async function runMutation(action, { successTitle, errorTitle, flashId } = {}) {
    const result = await action();
    if (result.success) {
      notify.success({ title: successTitle });
      markMutated(flashId ?? result.data?.id);
      if (onAfterMutation) await onAfterMutation();
    } else {
      notify.error({ title: errorTitle, detail: result.message || '' });
    }
    return result;
  }

  async function handleSubmit(payload) {
    const editing = editingRecord.value;
    const result = await runMutation(
      () => (editing
        ? store.updateRecord(entity, editing.id, payload)
        : store.createRecord(entity, payload)),
      {
        successTitle: editing ? labels.updated : labels.created,
        errorTitle: saveErrorTitle(editing),
        flashId: editing?.id,
      },
    );
    if (result.success) closeModal();
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
    openCreateModal,
    openEditModal,
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
    // pagination
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
