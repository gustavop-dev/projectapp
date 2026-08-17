### FLOW: `proposal-calculator-biometric-module`

- **Module:** proposal
- **Role:** guest (via shared UUID link)
- **Priority:** P2
- **Routes:** `/proposal/:uuid`
- **Description:** The investment calculator exposes `biometric_verification_module` as a provider-billed integration: ID document reading + OCR, facial recognition, liveness detection, antifraud + KYC, frictionless digital onboarding, and a verifications panel. Because the integration provider invoices the end client directly, the module follows the `is_invite=True, price_percent=0` pattern (same as `ai_module` and `integration_conversion_tracking`). Two sibling modules — `qr_generator_module` (25%) and `content_generator_module` (30%, with editorial calendar + scheduling) — are added to the catalog at the same time but are regular non-invite calculator modules; their structural behavior is already covered by `proposal-calculator-modules` and `proposal-calculator-new-modules`.
- **Steps:**
  1. Client opens the calculator modal on a proposal that includes `biometric_verification_module`.
  2. Module row renders with the bilingual title "🪪 Verificación y Validación Biométrica (Integración API)".
  3. Module shows "Agendar llamada" badge instead of a price (because `is_invite=True, price_percent=0`).
  4. Client clicks the module row → `invite_note` is revealed ("Te invitamos a una llamada... un proveedor especializado factura el servicio directamente al cliente final").
  5. Selecting the module does NOT alter the total investment (provider-billed; verified at the unit level by `computeWeeksAddition — does not count invite modules`).
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/proposal/proposal-calculator-biometric-module.spec.js`
