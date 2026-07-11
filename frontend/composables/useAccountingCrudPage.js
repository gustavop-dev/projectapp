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
 * - onAfterMutation(record, payload, action)  optional async hook awaited
 *     after a successful create/update/delete (e.g. refetch server meta).
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

  async function handleSubmit(payload) {
    const editing = editingRecord.value;
    const result = editing
      ? await store.updateRecord(entity, editing.id, payload)
      : await store.createRecord(entity, payload);

    if (result.success) {
      notify.success({ title: editing ? labels.updated : labels.created });
      markMutated(result.data?.id ?? editing?.id);
      closeModal();
      if (onAfterMutation) {
        await onAfterMutation(editing, payload, editing ? 'update' : 'create');
      }
    } else {
      notify.error({ title: saveErrorTitle(editing), detail: result.message || '' });
    }
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
      onConfirm: async () => {
        const result = await store.deleteRecord(entity, record.id);
        if (result.success) {
          notify.success({ title: labels.deleted });
          if (onAfterMutation) await onAfterMutation(record, null, 'delete');
        } else {
          notify.error({ title: labels.deleteErrorTitle, detail: result.message || '' });
        }
      },
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
