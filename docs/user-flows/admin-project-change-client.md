### FLOW: `admin-project-change-client`
- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/projects`
- **API:** `GET /api/projects/<id>/change-client/preview/?client_profile_id=`, `POST /api/projects/<id>/change-client/`, `DELETE /api/accounts/projects/<id>/?force=1` (guarded)
- **Description:** A project changes owner through ONE guided path — the form field stays immutable (`client_immutable`) and a ghost "Cambiar cliente…" entry opens the cascade. The preview names everything: movable records, incomes an active (non-cancelled) cuenta blocks (they detach and keep their client; anular y reemitir is the path for a wrong cuenta), draft cuentas that follow the project (fresh provisional snapshot) or their blocked income, ISSUED documents nothing touches, clientless rows left to the completion tools, and other documents that ride along. The mode — Mover | Desvincular — is chosen EVERY time (no preselection). The apply carries the preview's hosting/income ids as a staleness token (409 `records_not_found`/`records_changed` reload the preview) and runs in one transaction with an audit row per touched record. Hard-deleting a project now refuses with 409 `project_has_records` while anything is linked.
- **Steps:** edit project → Cambiar cliente… → pick destination → read the impact → choose the mode → confirm → row and accounting lists refresh.
- **Branches:** same client / unknown client / archived project answer 400 with their codes; missing mode keeps confirm disabled; 409 reloads the preview and drops the chosen mode.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-project-change-client.spec.js`

### Section 28 Coverage Index

| Flow ID | Module | Role | Priority | Status | Spec |
|---------|--------|------|----------|--------|------|
| `admin-accounting-project-bulk-assign` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-accounting-project-bulk-assign.spec.js` |
| `admin-accounting-project-coherence` | admin | admin | P1 | ✅ Covered | `e2e/admin/admin-accounting-project-coherence.spec.js` |
| `admin-project-inline-assign-offer` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-project-inline-assign-offer.spec.js` |
| `admin-project-change-client` | admin | admin | P2 | ✅ Covered | `e2e/admin/admin-project-change-client.spec.js` |
