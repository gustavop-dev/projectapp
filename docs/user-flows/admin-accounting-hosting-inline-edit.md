### FLOW: `admin-accounting-hosting-inline-edit`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P3
- **Routes:** `/panel/accounting/hostings`
- **Description:** Inline edits without opening the modal: double-click on cliente, dominio or valor/mes swaps the cell for an input (`AccountingInlineCell`; money cells use BaseCurrencyInput), Enter/blur PATCHes only when the value changed, Esc cancels; a failed PATCH leaves the row untouched so the cell falls back. The estado column is `AccountingStatusSelect` (badge-styled select, snap-back + spinner) PATCHing `is_active` directly.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-blog-publish-mode.spec.js` (mode reveal + overdue banner + hydration + publish-now payload; added 2026-07-22)
