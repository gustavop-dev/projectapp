/**
 * Normalize a caught axios error into a consistent shape the panel UI can render.
 *
 * The backend is inconsistent about error payloads:
 *   - { error: "message", code?, hint? }   (proposal/content endpoints)
 *   - { detail: "message" }                (DRF default / permission errors)
 *   - { field: ["err1", "err2"], ... }     (serializer field errors)
 *   - { non_field_errors: [...] }          (serializer object-level errors)
 *   - a bare string
 *
 * @param {*} error - The value thrown by an awaited HTTP call (usually an axios error).
 * @param {string} [fallback] - Message to use when nothing usable is found.
 * @returns {{ message: string, code: string|null, hint: string|null, fieldErrors: Object|null, status: number|null }}
 */
export function normalizeApiError(error, fallback = 'Ocurrió un error. Inténtalo de nuevo.') {
  const data = error?.response?.data;
  const status = error?.response?.status ?? null;

  if (data == null) {
    return { message: fallback, code: null, hint: null, fieldErrors: null, status };
  }

  if (typeof data === 'string') {
    return { message: data || fallback, code: null, hint: null, fieldErrors: null, status };
  }

  const code = typeof data.code === 'string' ? data.code : null;
  const hint = typeof data.hint === 'string' ? data.hint : null;

  // Explicit human message keys, in priority order.
  const direct = firstString(data.error) || firstString(data.detail) || firstString(data.message);
  if (direct) {
    return { message: direct, code, hint, fieldErrors: collectFieldErrors(data), status };
  }

  // Serializer field errors: pick the first readable message, keep the map.
  const fieldErrors = collectFieldErrors(data);
  if (fieldErrors) {
    const firstKey = Object.keys(fieldErrors)[0];
    return { message: fieldErrors[firstKey], code, hint, fieldErrors, status };
  }

  return { message: fallback, code, hint, fieldErrors: null, status };
}

/** Return `value` as a trimmed string if it's a non-empty string, else null. */
function firstString(value) {
  return typeof value === 'string' && value.trim() ? value.trim() : null;
}

/**
 * Build a { field: "first message" } map from serializer-style field errors,
 * skipping the reserved meta keys. Returns null when there are none.
 */
function collectFieldErrors(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return null;
  const reserved = new Set(['error', 'detail', 'message', 'code', 'hint']);
  const result = {};
  for (const [key, value] of Object.entries(data)) {
    if (reserved.has(key)) continue;
    const msg = Array.isArray(value) ? firstString(value[0]) : firstString(value);
    if (msg) result[key] = msg;
  }
  return Object.keys(result).length ? result : null;
}
