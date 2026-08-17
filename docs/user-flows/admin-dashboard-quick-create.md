### FLOW: `admin-dashboard-quick-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/`
- **Description:** The dashboard header "+ Crear" dropdown offers quick navigation to create a proposal, document, task or expense.
- **Steps:**
  1. Admin opens `/panel/` and clicks "+ Crear".
  2. The dropdown lists Propuesta / Documento / Tarea / Gasto.
  3. Selecting an option navigates to the corresponding module route.
- **Coverage:** ✅ Covered (menu destinations + real navigation to expenses). Covering this flow surfaced and fixed a real bug: `BaseDropdown` rendered `to` items through `<component :is="'NuxtLink'">`, which cannot resolve Nuxt auto-imported components — the menu items were dead `<nuxtlink>` elements with no href (fixed with `resolveComponent`).
- **E2E Spec:** `e2e/admin/admin-dashboard.spec.js`
