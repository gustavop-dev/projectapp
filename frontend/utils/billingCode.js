/**
 * Client-side mirror of `accounts/services/billing_code.py`.
 *
 * Only the normalization lives here — validation stays on the backend, which is
 * the single source of truth and answers with the message the panel shows. This
 * exists so every surface sends the same shape (uppercase, trimmed, single
 * spaces) instead of each modal rolling its own.
 */
export const BILLING_CODE_MAX_LENGTH = 12;

/** Uppercase and trim, collapsing inner whitespace runs. */
export function normalizeBillingCode(value) {
  return String(value || '').trim().replace(/\s+/g, ' ').toUpperCase();
}

/** The 6 fields every client form posts, so no surface can drift from the rest. */
export function emptyClientForm() {
  return {
    name: '', email: '', phone: '', company: '', nit: '', billing_code: '',
  };
}

/** Trimmed payload for the create/update endpoints. */
export function clientFormPayload(form) {
  return {
    name: (form.name || '').trim(),
    email: (form.email || '').trim(),
    phone: (form.phone || '').trim(),
    company: (form.company || '').trim(),
    nit: (form.nit || '').trim(),
    billing_code: normalizeBillingCode(form.billing_code),
  };
}
