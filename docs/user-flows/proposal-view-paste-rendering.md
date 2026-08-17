### FLOW: `proposal-view-paste-rendering`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** Client views proposal sections that use paste mode (`_editMode: 'paste'`). Paste-mode sections render as `RawContentSection` with markdown rendering in a styled card, while form-mode sections render their structured Vue components. Mixed form/paste proposals show each section in its correct mode.
- **Steps:**
  1. Client opens a proposal containing sections with `_editMode: 'paste'`.
  2. Paste-mode sections render `RawContentSection` with section title, index number, and a rounded card with markdown content.
  3. Markdown features (headings, bold, lists, blockquotes) render correctly via `marked` + `DOMPurify`.
  4. Form-mode sections in the same proposal render their structured components (no `RawContentSection`).
- **Branches:**
  - [Branch A — All form] Proposal with all form-mode sections renders zero `RawContentSection` components.
  - [Branch B — Mixed] Proposal with some paste and some form sections renders each correctly.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-view-paste-rendering.spec.js`
