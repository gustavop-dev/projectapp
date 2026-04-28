import { computed, ref, watch } from 'vue';

export function usePagination(source, options = {}) {
  const pageSize = ref(options.pageSize ?? 10);
  const currentPage = ref(1);

  const items = computed(() => {
    const value = typeof source === 'function' ? source() : source.value;
    return Array.isArray(value) ? value : [];
  });

  const totalItems = computed(() => items.value.length);
  const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)));

  watch(totalPages, (next) => {
    if (currentPage.value > next) currentPage.value = next;
    if (currentPage.value < 1) currentPage.value = 1;
  });

  const paginatedItems = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value;
    return items.value.slice(start, start + pageSize.value);
  });

  const rangeFrom = computed(() => (totalItems.value === 0 ? 0 : (currentPage.value - 1) * pageSize.value + 1));
  const rangeTo = computed(() => Math.min(currentPage.value * pageSize.value, totalItems.value));

  function goTo(page) {
    currentPage.value = Math.min(Math.max(1, page), totalPages.value);
  }
  function next() { goTo(currentPage.value + 1); }
  function prev() { goTo(currentPage.value - 1); }
  function reset() { currentPage.value = 1; }

  return {
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    paginatedItems,
    rangeFrom,
    rangeTo,
    goTo,
    next,
    prev,
    reset,
  };
}
