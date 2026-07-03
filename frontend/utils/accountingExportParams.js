/**
 * Map the page's local filter state to the server-side query params of
 * the accounting list/export endpoints (mapping: localKey -> serverKey).
 * Empty values are skipped; arrays join with commas (multi choice → OR).
 */
export function buildExportParams(filters, mapping) {
  const params = {};
  for (const [localKey, serverKey] of Object.entries(mapping)) {
    const value = filters[localKey];
    if (value === '' || value === null || value === undefined) continue;
    if (Array.isArray(value)) {
      if (value.length) params[serverKey] = value.join(',');
      continue;
    }
    params[serverKey] = String(value);
  }
  return params;
}
