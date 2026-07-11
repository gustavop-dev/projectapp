# Documents Module — Dual PDF Template (Friendly / Professional) Design

- **Date:** 2026-07-10
- **Status:** Approved by owner (design review in session)
- **Scope:** Documents module (`/panel/documents`, `/platform/documents`), backend PDF pipeline

## 1. Problem

The on-screen markdown preview and the downloaded PDF of a document use two unrelated
rendering pipelines with different looks:

- **Preview ("friendly")** — `useMarkdownPreview.js` (custom regex parser) + scoped CSS in
  `DocumentMarkdownBody.vue`: emerald `#047857` headings with bottom borders, warm gray body
  text with 1.7 line-height, zebra tables, soft green blockquotes, GitHub-style callouts.
- **Downloaded PDF ("professional")** — `DocumentPdfService` + `pdf_utils.py` (ReportLab
  canvas): dark esmerald `#002921` brand palette, lemon accents, header bar, section banners.

The owner wants **both presentations available** — previewable via a switch and downloadable
as two options — because different clients respond better to one or the other. Additionally,
the PDF layout engine has fidelity defects: paragraphs do not fill the available width,
spurious line breaks appear, boxes can overlap, tables use fixed equal columns, long code
lines overflow, and nested lists flatten to one level.

## 2. Decisions (owner-approved)

| Decision | Choice |
|---|---|
| Engine for the friendly PDF | Second **ReportLab theme** in the existing pipeline (no new dependencies; WeasyPrint and browser-print rejected) |
| Where dual download applies | **Panel** chooses per download; **platform (clients) and email** use the document's persisted default style |
| Persistence | New `template_style` field on `Document` (`professional` \| `friendly`, default `professional`) |
| Markdown images `![alt](url)` | **Out of scope** — later phase (preview does not support them either) |

## 3. Architecture

### 3.1 Data model

- `Document.template_style`: `CharField` with choices `professional` (default) / `friendly`;
  new migration (never modify old migrations). Existing documents keep today's look.
- Exposed in the document detail/create/update serializers alongside the existing
  `include_portada/subportada/contraportada` flags, with choice validation.

### 3.2 Backend — endpoint & routing

- `GET /api/documents/<id>/pdf/?template=friendly|professional` on
  `download_document_pdf` (`backend/content/views/document.py`), mirroring the proposals
  precedent `?doc=technical` (`views/proposal.py`).
  - No param or invalid value → fall back to `document.template_style`.
- Platform (client) PDF endpoint takes **no** param and always renders
  `document.template_style`. The standalone email flow (`POST /api/emails/send/`,
  `views/standalone_email.py`) attaches document PDFs via `DocumentPdfService.generate(doc)`
  and therefore picks up the persisted style with no extra wiring.
- Download filename stays `<title>.pdf` for both styles (no suffix), matching current
  behavior in panel and platform.

### 3.3 Backend — theme object (no pipeline fork)

- New `PdfTheme` (dataclass) bundling: heading/body/accent colors, blockquote and callout
  palettes, table header/stripe colors, font sizes, leading (line-height), heading underline
  rules, header-bar styling.
- Drawing functions in `pdf_utils.py` accept an optional `theme` parameter whose default
  reproduces current constants — proposals, contracts, collection accounts, diagnostics and
  onboarding PDFs keep the professional palette and styling unchanged unless a theme is
  passed. (Their text layout does improve via the shared fidelity fixes of §3.4 — see §7.)
- `DocumentPdfService.generate(document, template_style)` selects the theme.
- **Friendly theme spec** (source of truth: `DocumentMarkdownBody.vue` scoped CSS):
  h1/h2 emerald `#047857` with thin `#d1d5db` bottom border, h3 `#059669`, body `#374151`
  with generous leading, blockquote `#f0fdf4` bg + `#10b981` left border, zebra tables
  (`#f9fafb` stripes), preview-matched callout palette, links `#059669`.
- Covers (portada/subportada/contraportada), clickable TOC, watermark, footer page numbers
  and the emoji pipeline (NotoEmoji per-run) work identically under both themes.

### 3.4 Backend — markdown fidelity fixes (both themes)

1. **Measured wrapping**: replace every char-count estimate
   (`max_width / (font_size * 0.48)`) with real `stringWidth`-based wrapping; styled runs
   (bold/italic/code/emoji) measured with their actual font via `_mixed_string_width`.
   Paragraphs fill the full available width with no spurious breaks.
2. **Single height source**: callout/code/blockquote boxes reserve exactly the height that
   the shared wrapping routine will draw; clean pagination when a box does not fit (no
   footer collisions, no overlap with the next block).
3. **Tables**: content-proportional column widths (min/max caps) instead of equal fixed
   columns; row heights derived from actually wrapped lines.
4. **Code blocks**: wrap long lines at measured width instead of overflowing the right margin.
5. **Nested lists**: extend `markdown_parser.py` beyond the current single `children` level
   to real multi-level nesting; per-level indent and marker at draw time.
6. Everything the preview renders stays supported in both PDFs: headings, bold/italic/strike,
   inline code, links, ordered/unordered lists, tables, fenced code, blockquotes, GitHub
   callouts, horizontal rules, `[TOC]`, emoji shortcodes.

### 3.5 Frontend

- **Preview switch**: `BaseSegmented` (same control as the list/gallery toggle) with
  Amigable/Profesional in `create.vue`, `[id]/edit.vue` and the full-screen
  `MarkdownPreviewModal`. New `theme` prop on `DocumentMarkdownBody.vue`
  (default `friendly` = current CSS); a `markdown-preview--professional` scoped block
  approximates the professional PDF palette (dark esmerald headings, bone backgrounds,
  Ubuntu type) on screen. Switch initializes from `template_style` and is persisted on save
  in the editor (create payload + update payload).
- **Dual download**: `BaseDropdown` split-button — "Descargar PDF · Amigable" /
  "Descargar PDF · Profesional" — in the editor header and `DocumentActionsSheet`.
  Store action becomes `downloadPdf(id, title, template)` appending `?template=`.
  Targeted cleanup: migrate that action from raw `axios` to the shared
  `request_http.js` client.
- **Platform page**: client download button unchanged; backend serves the persisted style.
- Card thumbnails (`variant="mini"`) keep the current friendly look.

## 4. Data flow

Operator edits → toggles style in preview switch → saves (persists `template_style`) →
downloads either style on demand via `?template=` → clients on `/platform` and email
attachments always receive the document's persisted default.

## 5. Error handling

- Invalid/absent `?template` → document default; legacy documents → `professional`.
- Serializer rejects unknown `template_style` values on create/update.
- PDF generation failure keeps existing panel notification handling
  (`usePanelNotify` + `error_response`).

## 6. Testing

- **Backend (pytest, batches ≤20, never full suite):** `?template=` branching incl.
  invalid values; friendly-theme `generate()` smoke on a kitchen-sink markdown document
  (asserts `%PDF` bytes, no crash); measured-wrapping units (lines ≤ available width, no
  premature breaks); table column-width distribution; nested-list parsing; box height ==
  drawn height regressions; emoji rendering under the friendly theme; regression slices of
  proposal/contract PDF tests (shared `pdf_utils` changes).
- **Frontend unit:** `DocumentMarkdownBody` theme prop classes; store `downloadPdf`
  template param + URL; segmented switch persistence in editor payloads.
- **E2E:** preview switch toggles theme class; download menu exposes both options.
  Run the `e2e-user-flows-check` skill as the final step (CLAUDE.md requirement — this
  changes a frontend user flow).

## 7. Risks

- Fixing wrapping in shared `pdf_utils.py` changes text layout in **all** PDF services
  (proposals, contracts, collection accounts…). It is a strict improvement, but their
  existing test slices must pass before merge.
- The on-screen "professional" preview is a CSS approximation of the ReportLab output —
  faithful in palette/typography, not pixel-identical pagination. The PDF remains the
  source of truth for print layout.

## 8. Out of scope

- Markdown image support (preview + PDF) — future phase.
- Per-download style selection for platform clients.
- Redesign of cover pages; syntax highlighting in code blocks.
