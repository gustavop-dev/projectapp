### FLOW: `admin-proposal-functional-requirements-paste`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Sections tab → functional_requirements section)
- **Description:** Admin uses the per-group "Pegar contenido" mode to save raw text for individual requirement groups. Each group and additional module has its own paste toggle. When a group is in paste mode, the client-facing proposal renders that group as a `RawContentSection` with Markdown.
- **Steps:**
  1. Admin opens the functional_requirements section editor.
  2. Admin clicks "Pegar contenido" on a specific group (e.g., Views).
  3. A textarea (rows=10) appears within that group, pre-filled via `groupToReadableText()`.
  4. Admin types or pastes content.
  5. Admin saves the section → group's `_editMode: 'paste'` and `rawText` are stored in content_json.
  6. On next open, the group remembers paste mode.
- **Branches:**
  - [Branch A — Mixed modes] Some groups in form mode, others in paste mode → each saved independently.
  - [Branch B — Client view] Groups with `_editMode: 'paste'` render as `RawContentSection` in the client proposal.
- **Coverage:** ⚠️ Partial
- **E2E Spec:** `e2e/admin/admin-proposal-requirements.spec.js`
- **Unit Tests:** `test/components/SectionEditor.test.js`
- **Backend Tests:** `content/tests/views/test_section_update_views.py`
