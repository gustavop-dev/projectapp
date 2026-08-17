### FLOW: `admin-proposal-functional-requirements-form`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit` (Sections tab → functional_requirements section)
- **Description:** Admin manages functional requirement groups (Views, Components, Features, Admin Module) and their items using the form interface. Each item has an editable "ID (enlace técnico)" field — the stable id (`item-<group>-<slug>`) used by the technical document's `linked_item_ids` for item↔requirement traceability. Missing ids are auto-assigned on save (client mirror + backend `ensure_functional_requirements_item_ids`). The section preview mirrors the public render, including the per-item "Ver requerimientos (N)" links built from the proposal's technical_document.
- **Steps:**
  1. Admin opens the functional_requirements section editor.
  2. Four default groups render: Views, Components, Features, Admin Module.
  3. Admin edits group fields: icon, title, description.
  4. Admin adds items to a group: icon, name, description, optional stable id (auto-generated on save when empty).
  5. Admin removes items from a group.
  6. Admin adds additional modules via "+ Agregar módulo adicional".
  7. Admin saves the section → content_json includes groups[] and additionalModules[] with per-group `_editMode` and per-item stable `id`.
  8. [Preview] Admin opens the section preview → items with linked technical requirements show the same "Ver requerimientos (N)" affordance the client sees.
- **Coverage:** ⚠️ Partial
- **E2E Spec:** `e2e/admin/admin-proposal-requirements.spec.js`
- **Unit Tests:** `test/components/SectionEditor.test.js`, `test/components/SectionPreviewModal.test.js`
- **Backend Tests:** `content/tests/views/test_section_update_views.py`
