# Panel Diagnostics Module Audit — 2026-07-06

Full audit of the `/panel/diagnostics` module (Web App Diagnostic) covering views, components, business logic, backend, and panel error handling. Diagnostics is the younger twin of the Proposals module and has fallen behind it on error standards, notifications, design-system compliance, and operational features.

Phase 1 (quick wins) is implemented in the branch that introduces this document. Phases 2-4 are the approved roadmap.

## Module map

**Frontend** (Nuxt 3 + Vue 3, Pinia Options API, semantic Tailwind tokens):

| Piece | Path | Size |
|---|---|---|
| List page | `frontend/pages/panel/diagnostics/index.vue` | 511 lines |
| Create page | `frontend/pages/panel/diagnostics/create.vue` | 124 lines |
| Editor (multi-tab) | `frontend/pages/panel/diagnostics/[id]/edit.vue` | 1,178 lines |
| Defaults stub | `frontend/pages/panel/diagnostics/defaults.vue` | redirect to `/panel/defaults?mode=diagnostic` |
| Components | `frontend/components/WebAppDiagnostic/**` | 34 files, 5,565 lines |
| Store | `frontend/stores/diagnostics.js` + `diagnostics_constants.js` | 566 + 58 lines |
| Logic | `frontend/utils/diagnosticNextAction.js`, `composables/useDiagnosticFilters.js`, `useDiagnosticPrompt.js`, `useDiagnosticDarkMode.js` | — |

Giant components: `admin/DiagnosticAnalytics.vue` (963), `DiagnosticDocumentsTab.vue` (569), `DiagnosticEmailsTab.vue` (506).

**Backend** (Django 5 + DRF, function-based views):

| Piece | Path | Size |
|---|---|---|
| Views | `backend/content/views/diagnostic.py` | 1,617 lines, 33 endpoints + 9 helpers |
| Services | `content/services/diagnostic_service.py` (344), `diagnostic_email_service.py`, `diagnostic_pdf_service.py`, `diagnostic_documents_service.py` | — |
| Models | `web_app_diagnostic.py`, `diagnostic_section.py`, `diagnostic_view_event.py`, `diagnostic_change_log.py`, `diagnostic_default_config.py`, `diagnostic_attachment.py` | — |
| Serializers | `content/serializers/diagnostic.py` | 348 lines (no CreateSerializer) |

## Findings — backend

### High
- **BA1 — Error standard ignored.** `error_response` from `content/api_errors.py` (`{error, code, hint}`) was used **0 times** in diagnostic.py (vs 19 in proposal.py). Five error shapes coexisted across ~43 error responses: `{'error':'english_code'}`, `{'error':'Spanish phrase'}`, `{'error':code,'message':full}` (transitions), `{'detail':...}` (defaults), and raw `serializer.errors`. The frontend could not branch on `code`. **→ Fixed in Phase 1.**
- **BA2 — `diagnostic_analytics` does not scale** (L375-586): the global comparison loads ALL diagnostics and iterates them in Python per request (L520-552); N+1 for section titles (L429-438); aggregation duplicated in the CSV export (L625). ~200 lines of business logic living in the view. → Phase 2.
- **BA3 — Public endpoints without throttle / status gate**: `retrieve_public_diagnostic` and `by-slug` returned metadata (title, client_name, investment_amount) for DRAFT diagnostics; `download_public_diagnostic_pdf` (expensive PDF generation) and `respond_public_diagnostic` (mutates state) were AllowAny without throttle. **→ Fixed in Phase 1.**
- **BA4 — No pre-send scorecard/readiness.** No equivalent of `proposal_scorecard` (`views/proposal.py:1996`); `send_initial`/`send_final` do not verify client_email or content before transitioning + sending. → Phase 2.

### Medium
- **BM1 — Business logic in views**: `_compute_diagnostic_engagement_score` (L312: magic weights, `'cost'` hardcoded, flat +15 for closed states), analytics aggregation, CSV, `_parse_diagnostic_email` (122 lines), `_generate_and_save_confidentiality_pdf`, attachment validation. → Phase 2.
- **BM2 — `send_final` without phase guard**: both sends target SENT; the timestamp is decided only by `initial_sent_at is None` — a send_final on a DRAFT seals initial_sent_at and sends the final email. → Phase 2.
- **BM3 — Dead states/config**: `Status.VIEWED` unreachable, `Status.EXPIRED` never assigned; `DiagnosticDefaultConfig.expiration_days/reminder_days/urgency_reminder_days` are echo-only — no expiration/reminder task (proposals has them: `tasks.py:248,200`). → Phase 2 (implement the cycle or remove dead code).
- **BM4 — Manual parsing without serializers**: `create_diagnostic`, `bulk_update_diagnostic_sections` (silently drops invalid entries), `create_diagnostic_activity`, `track_diagnostic_section_view`, `send_diagnostic_attachments`, defaults PUT. → Phase 2.
- **BM5 — Missing DB indexes**: `WebAppDiagnostic` (status, client, updated_at), `DiagnosticChangeLog(diagnostic, created_at)`, `DiagnosticAttachment(diagnostic, document_type, is_generated)`. → Phase 2.
- **BM6 — Tracking integrity**: `time_spent_seconds` without upper bound, IP taken from X-Forwarded-For unvalidated → engagement score can be inflated. → Phase 2.

### Low
Score thresholds not configurable; ConfidentialityParams PATCH behaves as full-replace; re-fetch after create; device breakdown recomputed in Python per request; HTTP test gaps (`retrieve_diagnostic`, `reset_diagnostic_section`, `update_confidentiality_params`, `list_diagnostic_attachments`); change log records no-ops.

## Findings — frontend

### Critical
- **FC1 — Silent delete in the list**: `index.vue` called `store.remove` without handling the result; success and error had no feedback; a failed fetchAll did not notify either. **→ Fixed in Phase 1.**
- **FC2 — Store without `normalizeApiError`**: `stores/diagnostics.js` returned raw codes (`fetch_failed`) and did not propagate per-field `errors` (proposals.js uses it in ~14 places). The `result.errors.slug` branch in `edit.vue` was dead code. **→ Fixed in Phase 1.**

### High
- **FA1 — `DiagnosticAnalytics.vue` (963) monolithic**: 63 hardcoded color classes; repeated magic thresholds (70/40 engagement ×3, 80/50 coverage — also duplicated in edit.vue); business logic in the component (suggestions, SECTION_INSIGHTS, timeline maps). → Phase 3.
- **FA2 — ~250 lines of JSON logic inline in `edit.vue`** (buildDiagnosticExport, jsonSummary, parseImportJson, handleApplyImportJson, sectionHasContent) — proposals extracted this into `utils/proposalJsonMigration.js`. → Phase 3.
- **FA3 — Parity gaps vs Proposals**: no KPI dashboard (neither `/panel/` root nor list), no bulk actions, no pre-send checklist in the editor, no expiration in the UI, no multi-send. → Phases 2-3.
- **FA4 — Duplication with BusinessProposal**: DiagnosticEmailsTab ≈ ProposalEmailsTab, DiagnosticActionsModal ≈ ProposalActionsModal, sectionEditorUtils ×2, diagnosticNextAction ≈ proposalNextAction (near-literal copy). → Phase 4.

### Medium
- **FM1 — Legacy notifications**: `edit.vue` used `usePanelToast` + `<PanelToast />` (deprecated no-op alias pair). **→ Fixed in Phase 1.**
- **FM2 — Hardcoded tokens**: DiagnosticAnalytics (63), DiagnosticEmailsTab (26), DiagnosticDocumentsTab (22), DiagnosticFilterPanel (5), `diagnostics_constants.STATUS_META` (light-only, no dark:), `diagnosticNextAction.colorClass` (raw bg-blue-600). **→ Constants fixed in Phase 1**; component sweep → Phase 3.
- **FM3 — `create.vue` bypassed the design system**: raw select/input/button instead of BaseSelect/BaseInput/BaseButton. **→ Fixed in Phase 1.**
- **FM4 — DiagnosticActionsModal re-derives transitions** instead of reusing getDiagnosticNextAction. → Phase 3.
- **FM5 — List a11y**: sortable th without role/tabindex/aria-sort; 3-dots button without aria-label; modals without role="dialog"/aria-modal/focus-trap. → Phase 3.

### Low
No error state in the list (failed fetch == empty) **→ Fixed in Phase 1**; CSV with hardcoded absolute path; shared global isUpdating; nextAction missing terminal states; 100% client-side filtering; missing tests (sort/pagination/delete-feedback, color thresholds).

## Roadmap

- **Phase 1 — Quick wins: errors + feedback + design system (DONE in this branch).** BA1, BA3, FC1, FC2, FM1, FM3, constants part of FM2, list error state.
- **Phase 2 — Backend business logic.** Extract engagement score + analytics into `diagnostic_analytics_service.py` with named constants, fix N+1 and bounded/cached comparison (BA2, BM1); **diagnostic scorecard** pre-send with gate on sends + blocking checklist in the editor (BA4); phase guard on send_final and decide VIEWED/EXPIRED cycle (BM2, BM3); input serializers (BM4); DB indexes via new migration (BM5); cap time_spent_seconds (BM6).
- **Phase 3 — Frontend UI/UX.** Split DiagnosticAnalytics + centralize thresholds + full token pass (FA1, FM2); extract JSON logic to `utils/diagnosticJson.js` (FA2); KPI dashboard, bulk actions, expiration UI (FA3); a11y (FM5); ActionsModal reuses getDiagnosticNextAction (FM4); CSV via request_http.
- **Phase 4 — Deduplication with Proposals.** Shared EmailComposerTab/ActionsModal/sectionEditorUtils/getNextAction bases (FA4); common backend scoring base (proposals heat_score vs diagnostics engagement score).
