### FLOW: `layout-icon-interaction-feedback`

- **Module:** layout
- **Role:** guest / admin / platform-admin / platform-client
- **Priority:** P2
- **Routes:** Transversal; representative E2E route `/panel/views`
- **Description:** Activate an icon-only action, navigation control, opener, or toggle and receive an immediate balanced 360 ms press, rebound and expanding halo. Copy actions additionally confirm the real clipboard result beside the originating control without replacing its icon.
- **Steps:**
  1. The user reaches a surface with an enabled icon-only control.
  2. The user activates the control with pointer, touch, or keyboard.
  3. The control immediately compresses, rebounds and settles while its shared halo expands and fades.
  4. For copy, the browser resolves the clipboard write.
  5. The same control shows a nearby success label and the clipboard contains the requested reference.
- **Branches:**
  - [Branch A — Clipboard denied] The control shows a nearby error label and the owning surface keeps its normal error notification.
  - [Branch B — Reduced motion] The halo/color reaction remains visible without scale animation.
  - [Branch C — Coarse pointer] The interactive target is at least 44 × 44 px.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-view-map.spec.js`
