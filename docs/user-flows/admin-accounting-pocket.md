### FLOW: `admin-accounting-pocket`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel/accounting/pocket`
- **Description:** ProjectApp pocket ledger with balance card and running-balance column (default view newest-first; the balance is computed chronologically). The pocket is the money entry point (Jul 2026): creating a movement also creates its linked income (IN → liquid/pocket) or expense (OUT). A new movement opens on Egreso, the common case, with every direction-dependent field already in its egreso variant; editing keeps the direction the record has. For IN the "Contabilidad" segmented is company-only; for OUT it is relabeled "Atribuir a" (Empresa/Gustavo/Carlos) because pocket money is company money: every OUT mirrors a company-ledger expense that counts against liquid utility — Empresa splits 50/50, a partner option registers a draw fully assigned to that partner (category personal). Linked movements open the edit modal with the direction locked and the attribution prefilled (derived from the split); edits mirror into the linked record and deleting either side cascades to the other (the delete confirm warns about the cascade). Unlinked historical movements keep plain CRUD and never gain a mirror.
- **Coverage:** ⚠️ Partial — modal ledger selector and locked-direction edit are covered; the create-POST payload (ledger included) and the cascade delete confirm are asserted at unit level only.
- **E2E Spec:** `e2e/admin/admin-accounting-pocket-recurring.spec.js`
