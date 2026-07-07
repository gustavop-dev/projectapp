/**
 * Shared helpers for the proposal JSON stats panels (JsonStatsPanel).
 *
 * Used by both the proposal edit page (technical JSON sub-tab) and
 * ProposalJsonTab (export JSON view) so the stats math stays in one place.
 */
import { computed } from 'vue';

export const JSON_TEXTAREA_ROWS = 18;

function countPresentKeys(source, expectedKeys) {
  if (!source || typeof source !== 'object' || Array.isArray(source)) return 0;
  return expectedKeys.filter((key) => key in source).length;
}

function calculateProgress(completed, total) {
  if (!total) return 0;
  return Math.round((completed / total) * 100);
}

function formatJsonSize(raw) {
  const normalized = typeof raw === 'string' ? raw : JSON.stringify(raw || {}, null, 2);
  const bytes = new Blob([normalized]).size;
  if (bytes < 1024) return `${bytes} B`;
  const kilobytes = bytes / 1024;
  return `${kilobytes >= 10 ? kilobytes.toFixed(0) : kilobytes.toFixed(1)} KB`;
}

function formatDateTime(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

export function makeJsonStats({ sourceRef, rawStringRef, expectedKeys, updatedAtRef }) {
  return computed(() => {
    const source = sourceRef.value;
    const sectionCount = countPresentKeys(source, expectedKeys);
    const rawString = rawStringRef?.value || (source ? JSON.stringify(source, null, 2) : '');
    return {
      sectionCount,
      progress: calculateProgress(sectionCount, expectedKeys.length),
      size: formatJsonSize(rawString),
      updatedAt: formatDateTime(updatedAtRef?.value),
    };
  });
}
