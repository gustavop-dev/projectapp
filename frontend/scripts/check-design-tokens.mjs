#!/usr/bin/env node
/**
 * Design-token guard: scans frontend Vue/JS for hardcoded color literals that
 * should now use semantic tokens (bg-surface, text-text-default, etc.).
 *
 * Why: with the design-system migration, new code must prefer tokens so dark
 * mode and tenant theming "just work" without component-level changes.
 *
 * Four checks run together:
 *   1. FORBIDDEN — legacy literals (`bg-white`, `bg-esmerald-dark`, etc.).
 *   2. INVALID_TOKEN_REFERENCES — `bg-X` where X isn't in tailwind.config.js
 *      or the Tailwind defaults (catches typos like `bg-primary-soft0`).
 *   4. RAW_BUTTON_STYLING — native <button> hand-writing its own chrome
 *      (bg-*, rounded-*, px-*, red/rose text) instead of <BaseButton
 *      variant="...">. Warn-only repo-wide (the migration is incremental);
 *      --strict makes it a hard gate on touched files. Tabs, segmented
 *      controls and selectable list rows opt out with a
 *      `design-tokens: allow-raw-button` comment.
 *   3. UNSTYLED_FORM_CONTROLS — native <input>/<select>/<textarea> in panel
 *      templates without a semantic background token. Bare inputs render
 *      white in dark mode. Panel-only; skips elements with `:class=` since
 *      dynamic bindings can't be statically traced.
 *   5. MANUAL_MODIFIER_NAVIGATION — reading ctrlKey/metaKey next to a
 *      window.open/router.push: an <a href> rewritten in JavaScript, which can
 *      only ever answer one of the browser's gestures. Gates always; the only
 *      exempt file is the shared primitive that owns the decision.
 *   6. ROW_LINK_MISSING — a `v-for` row with `@click` and no link inside, so
 *      the destination has no address the browser can use. Warn-only until
 *      --strict-rows, because a row whose detail is a modal needs an address
 *      invented before a link can exist. Opt out with
 *      `design-tokens: allow-clickable-row` for rows that only expand in place.
 *
 * Behavior:
 *   - Scans pages/, components/, layouts/ (excluding allowlist).
 *   - Reports offenses grouped by file with line numbers.
 *   - Exits with code 0 if no offenses or under the threshold.
 *   - Exits 1 only when --strict is passed (intended for CI on touched files).
 *
 * Usage:
 *   node frontend/scripts/check-design-tokens.mjs              # warn-only, full repo
 *   node frontend/scripts/check-design-tokens.mjs --scope=panel  # admin panel scope only
 *   node frontend/scripts/check-design-tokens.mjs --strict     # exit 1 on any offense
 *   node frontend/scripts/check-design-tokens.mjs --strict --strict-buttons  # also gate raw buttons
 *   node frontend/scripts/check-design-tokens.mjs --files a.vue b.vue  # only these files
 *   node frontend/scripts/check-design-tokens.mjs --quiet      # only print summary count
 *
 * Scopes:
 *   full   (default) — every file under pages/, components/, layouts/
 *   panel            — admin panel only (pages/panel/, components/panel/, components/BusinessProposal/admin/)
 *   public           — public site (proposal/, blog/, portfolio/, landings, diagnostic/) which has its own design system
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const FRONTEND_ROOT = path.resolve(path.dirname(__filename), '..');

// Patterns that should now be tokens. The replacement column is what to use
// instead — printed alongside each offense to make the fix obvious.
const FORBIDDEN = [
  { pattern: /\bbg-white\b(?!\/[0-9])/, suggest: 'bg-surface (or bg-surface-raised / bg-surface-muted)' },
  { pattern: /\bbg-esmerald(?:-dark|-light)?\b(?!\/[0-9])/, suggest: 'bg-primary / bg-primary-strong / bg-primary-soft' },
  { pattern: /\btext-esmerald(?:-dark|-light)?\b(?!\/[0-9])/, suggest: 'text-text-default / text-text-brand / text-primary' },
  { pattern: /\bborder-esmerald(?:-dark|-light)?\b(?!\/[0-9])/, suggest: 'border-border-default / border-input-border' },
  { pattern: /\bbg-lemon\b(?!\/[0-9])/, suggest: 'bg-accent / bg-accent-soft' },
  { pattern: /\btext-lemon\b(?!\/[0-9])/, suggest: 'text-accent (or use a contextual token)' },
  { pattern: /\bdark:bg-gray-[5-9]00\b/, suggest: 'remove dark: variant — bg-surface auto-flips' },
  { pattern: /\bdark:bg-esmerald(?:-dark|-light)?\b/, suggest: 'remove dark: variant — bg-surface auto-flips' },
  // Mid-scale grays are never right with the token system: as a surface they
  // break one of the two modes (tokens auto-flip), as an "always-dark" chrome
  // the brand-dark token is the convention. Matches the dark:-prefixed form
  // too (the \b boundary sits after the colon).
  { pattern: /\bbg-gray-[3-9]00(?:\/\d+)?\b/, suggest: 'bg-surface / bg-surface-raised (or bg-primary-strong for always-dark chrome)' },
  { pattern: /\bhover:bg-gray-[1-9]00(?:\/\d+)?\b/, suggest: 'hover:bg-surface-raised (on bg-surface) / hover:bg-border-muted (on bg-surface-raised)' },
  { pattern: /\btext-gray-200\b/, suggest: 'text-text-default / text-text-muted' },
  { pattern: /\bborder-gray-[3-9]00(?:\/\d+)?\b/, suggest: 'border-border-default / border-input-border' },
  { pattern: /\bdivide-gray-\d+00?\b/, suggest: 'divide-border-muted' },
  { pattern: /\b(?:dark:)?placeholder-gray-\d00\b/, suggest: 'placeholder:text-input-placeholder' },
  { pattern: /\btext-gray-[3-9]00\b/, suggest: 'text-text-default / text-text-muted / text-text-subtle' },
  { pattern: /\bdark:text-gray-[1-3]00\b/, suggest: 'remove dark: variant — text-text-* auto-flips' },
  { pattern: /\bborder-gray-[12]00\b/, suggest: 'border-border-default / border-border-muted / border-input-border' },
  { pattern: /\bdark:border-gray-[5-9]00\b/, suggest: 'remove dark: variant — border-border-* auto-flips' },
  { pattern: /\bbg-emerald-(?:50|100|600|700)\b/, suggest: 'bg-primary / bg-primary-soft / bg-success-soft' },
  { pattern: /\btext-emerald-(?:600|700)\b(?!\s+dark:text-emerald-)/, suggest: 'text-text-brand (already handles dark)' },
  { pattern: /\bring-emerald-500\b/, suggest: 'ring-focus-ring/30' },
  // Mixed semantic+literal anti-pattern: semantic token already handles dark mode,
  // the dark: literal override is redundant and will diverge from the token as it evolves.
  { pattern: /\btext-text-brand\b[^"'\n]*\bdark:text-emerald-[234]\d{2}\b/, suggest: 'remove dark:text-emerald-* — text-text-brand already flips to emerald-300 in dark' },
  { pattern: /\bbg-primary-soft\b(?!\/)[^"'\n]*\bdark:bg-emerald-900\/\d+/, suggest: 'remove dark:bg-emerald-900/* — bg-primary-soft has a dark override via CSS variable' },
  { pattern: /\bhover:bg-primary-soft\b(?!\/)[^"'\n]*\bdark:hover:bg-emerald-900\/\d+/, suggest: 'remove dark:hover:bg-emerald-900/* — hover:bg-primary-soft works in dark via CSS variable' },
];

// Forbidden patterns that are tolerated only in specific files. Keeps the
// rule strict everywhere except documented exceptions (e.g. `bg-gray-50` is
// the panel page-wash, paired with `dark:bg-primary-strong` in the layout).
const FORBIDDEN_CONDITIONAL = [
  {
    pattern: /\bbg-gray-50\b(?!\/[0-9])/,
    suggest: 'bg-surface-muted (page wash, auto-flips to primary-strong in dark)',
    allowedIn: new Set(['layouts/admin.vue']),
  },
  {
    pattern: /\bbg-gray-100\b(?!\/[0-9])/,
    suggest: 'bg-surface-raised (raised surface, auto-flips in dark)',
    allowedIn: new Set([]),
  },
];

// Tokens whose dark-mode value is intrinsically rgba() with a baked alpha
// (see frontend/assets/styles/theme.css around lines 144-209). Using them
// with a `/N` opacity modifier composes on top of an already-translucent
// intent and produces an unpredictable color in dark mode. Use the bare
// class. The triplet *-rgb fallback is white channels, so /N "works" but
// not as the author expects.
const ALPHA_BAKED_TOKENS = [
  'surface-raised',
  'border', 'border-muted',
  'primary-soft',
  'input-border', 'input-placeholder',
  'success-soft', 'warning-soft', 'danger-soft', 'info-soft',
];

const ALPHA_BAKED_PATTERN = new RegExp(
  String.raw`(?<![\w-])(?:bg|text|border|ring|fill|stroke|placeholder|caret|accent|from|to|via|divide|outline)-(${ALPHA_BAKED_TOKENS.join('|')})\/\d+\b`,
);

// ----------------------------------------------------------------------------
// Invalid-token detection: catches references to color tokens that don't exist
// in tailwind.config.js. This is what would have caught the `bg-primary-soft0`
// artefacts produced by a bad sed in the last migration.
//
// Strategy:
//   1. Parse `theme.extend.colors` keys out of tailwind.config.js (string keys
//      only — we don't try to evaluate the file).
//   2. Add the Tailwind default palette (white/black/transparent + scaled
//      colors like gray-50..950).
//   3. Scan files for `bg-X`, `text-X`, etc. Any X not in the Set is flagged.
// ----------------------------------------------------------------------------
const TAILWIND_KEYWORDS = new Set([
  'inherit',
  'current',
  'transparent',
  'white',
  'black',
]);

const TAILWIND_SCALED_FAMILIES = [
  'gray', 'red', 'blue', 'emerald', 'amber', 'yellow', 'green', 'orange',
  'rose', 'purple', 'pink', 'cyan', 'sky', 'indigo', 'violet', 'fuchsia',
  'lime', 'teal', 'slate', 'zinc', 'neutral', 'stone',
];

const TAILWIND_SCALE_STEPS = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950'];

// Utility classes that take a color token after the dash. `accent` and
// `placeholder` are unusual but Tailwind supports them (`accent-primary`,
// `placeholder-text-muted`, etc.).
const COLOR_UTILITIES = [
  'bg', 'text', 'border', 'ring', 'divide', 'from', 'to', 'via',
  'fill', 'stroke', 'outline', 'placeholder', 'caret', 'accent', 'shadow',
];

function extractDefinedThemeKeys(sectionName) {
  const configPath = path.join(FRONTEND_ROOT, 'tailwind.config.js');
  const tokens = new Set();
  if (!fs.existsSync(configPath)) return tokens;
  const src = fs.readFileSync(configPath, 'utf8');

  // Find the requested block inside theme.extend. We grab its matching closing
  // brace, then pull quoted keys out of that slice without evaluating config.
  const extendIdx = src.indexOf('extend:');
  if (extendIdx < 0) return tokens;
  const sectionIdx = src.indexOf(`${sectionName}:`, extendIdx);
  if (sectionIdx < 0) return tokens;
  const braceStart = src.indexOf('{', sectionIdx);
  if (braceStart < 0) return tokens;
  let depth = 0;
  let braceEnd = -1;
  for (let i = braceStart; i < src.length; i++) {
    const ch = src[i];
    if (ch === '{') depth++;
    else if (ch === '}') {
      depth--;
      if (depth === 0) {
        braceEnd = i;
        break;
      }
    }
  }
  if (braceEnd < 0) return tokens;
  const block = src.slice(braceStart + 1, braceEnd);

  // Match quoted keys like `'primary-soft':` or `"primary-soft":`. We
  // intentionally only match quoted keys to avoid picking up things like
  // `var(...)` literals or partial identifiers from the values.
  const keyRe = /['"]([a-z][a-z0-9-]*)['"]\s*:/gi;
  let m;
  while ((m = keyRe.exec(block)) !== null) {
    tokens.add(m[1]);
  }
  return tokens;
}

function extractDefinedColors() {
  return extractDefinedThemeKeys('colors');
}

function buildValidColorSet() {
  const set = new Set(TAILWIND_KEYWORDS);
  for (const fam of TAILWIND_SCALED_FAMILIES) {
    for (const step of TAILWIND_SCALE_STEPS) {
      set.add(`${fam}-${step}`);
    }
  }
  for (const tok of extractDefinedColors()) {
    set.add(tok);
  }
  return set;
}

const VALID_COLOR_TOKENS = buildValidColorSet();
const VALID_TEXT_SIZE_TOKENS = extractDefinedThemeKeys('fontSize');

// Per-utility blocklist: tokens that follow `bg-`/`text-`/etc. but are NOT
// color references (sizing, style, layout modifiers, SVG attribute names,
// etc.). These are silently ignored by the invalid-token check.
//
// We split this per-utility to avoid e.g. `stroke-width` being treated like
// `bg-width`. The 'common' bucket applies to every utility.
const NON_COLOR_BY_UTILITY = {
  common: new Set([
    'sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl', '7xl', '8xl', '9xl',
    'none', 'auto', 'inherit', 'current', 'transparent',
  ]),
  bg: new Set([
    'cover', 'contain', 'fixed', 'local', 'scroll', 'top', 'bottom', 'left',
    'right', 'center', 'origin', 'clip', 'blend', 'no-repeat', 'repeat',
    'repeat-x', 'repeat-y', 'repeat-round', 'repeat-space', 'gradient',
    'opacity',
  ]),
  text: new Set([
    'left', 'center', 'right', 'justify', 'start', 'end',
    'balance', 'pretty', 'wrap', 'nowrap', 'clip', 'ellipsis',
    'base', 'xs', 'opacity',
    // Shared panel typography scale from theme.extend.fontSize. These are
    // sizes, not color-token references.
    'panel-title', 'panel-heading', 'panel-body', 'panel-meta',
  ]),
  border: new Set([
    'solid', 'dashed', 'dotted', 'double', 'hidden', 'collapse', 'separate',
    'opacity',
  ]),
  ring: new Set(['inset', 'offset', 'opacity', 'solid', 'dashed', 'dotted', 'double']),
  divide: new Set(['solid', 'dashed', 'dotted', 'double', 'none', 'opacity', 'reverse']),
  outline: new Set(['solid', 'dashed', 'dotted', 'double', 'offset']),
  // card/raised/overlay are the elevation scale from theme.extend.boxShadow,
  // not colors (the color parser only reads theme.extend.colors).
  shadow: new Set(['inner', 'card', 'raised', 'overlay']),
  // SVG `stroke-linecap`, `stroke-linejoin`, `stroke-width`, `stroke-dasharray`
  // are SVG attribute names that look like Tailwind classes when scanned.
  stroke: new Set(['linecap', 'linejoin', 'width', 'dasharray', 'dashoffset', 'miterlimit', 'opacity']),
  fill: new Set(['opacity', 'rule']),
  placeholder: new Set(['opacity']),
  caret: new Set([]),
  accent: new Set([]),
  from: new Set([]),
  to: new Set([]),
  via: new Set([]),
};

// Border directional prefixes consume one segment after `border-` before the
// color token: `border-t-emerald-500`, `border-x-primary`, etc. Same idea for
// `divide-x/y` (but those don't take colors), `border-s/e`. We strip the
// direction prefix when present so the remaining token is just the color.
const BORDER_SIDES = new Set(['t', 'b', 'l', 'r', 'x', 'y', 's', 'e']);

// Match `bg-X`, `text-X`, etc. We capture the utility name and the tail
// (everything up to `/`, `[`, whitespace, or end-of-token). The negative
// lookahead `(?![:])` excludes inline CSS property names — `border-radius:`,
// `text-align:`, `border-bottom:` only appear in `style="..."` attributes
// or HTML email templates, never as a Tailwind class.
const TOKEN_USE_RE = new RegExp(
  `(?<![\\w-])(${COLOR_UTILITIES.join('|')})-([a-z][a-z0-9-]*)(?=$|[^a-z0-9-:])`,
  'gi',
);

// Skip lines that are clearly not class strings (imports, comments referencing
// var names, etc.). We keep this conservative — false negatives are fine,
// false positives in code comments are noise.
const SKIP_LINE_RE = /^\s*(?:\/\/|\*|import\s|from\s)/;

function findInvalidTokens(line) {
  const found = [];
  TOKEN_USE_RE.lastIndex = 0;
  let m;
  while ((m = TOKEN_USE_RE.exec(line)) !== null) {
    const utility = m[1].toLowerCase();
    let token = m[2];

    // Strip border directional prefix (`border-t-emerald-500` -> `emerald-500`).
    // If the tail is JUST the direction (`border-t`, `border-x`), it's a
    // borderless-side utility with no color, skip.
    if (utility === 'border') {
      const firstSeg = token.split('-')[0];
      if (BORDER_SIDES.has(firstSeg)) {
        if (token === firstSeg) continue; // border-t, border-x — no color
        token = token.slice(firstSeg.length + 1);
        // After stripping the side, if nothing remains, the original was
        // `border-t-[...]` with an arbitrary value (the regex stops at `[`).
        // Treat as not-a-color-token.
        if (!token) continue;
      }
    }
    // `divide-x` / `divide-y` are layout utilities, not colors. `divide-x-2`
    // sets width. Color form is `divide-{color}` directly.
    if (utility === 'divide') {
      const firstSeg = token.split('-')[0];
      if (firstSeg === 'x' || firstSeg === 'y') continue;
    }

    // Pure numeric (ring-1, divide-2, border-2) is sizing, not color.
    if (/^\d+$/.test(token)) continue;
    // `from-50%`, `to-100%` and similar gradient stop positions
    if (/^\d+%$/.test(token) || /^\d+\/\d+$/.test(token)) continue;

    // Per-utility non-color filter (uses only the first segment so things like
    // `stroke-linecap-square` would still match `linecap`).
    const firstSeg = token.split('-')[0];
    const utilityBlock = NON_COLOR_BY_UTILITY[utility];
    if (utilityBlock && (utilityBlock.has(firstSeg) || utilityBlock.has(token))) continue;
    if (NON_COLOR_BY_UTILITY.common.has(firstSeg) || NON_COLOR_BY_UTILITY.common.has(token)) continue;

    if (utility === 'text' && VALID_TEXT_SIZE_TOKENS.has(token)) continue;
    if (VALID_COLOR_TOKENS.has(token)) continue;
    found.push({ match: `${utility}-${m[2]}`, token });
  }
  return found;
}

// Files/dirs to skip entirely (decorative components, third-party shims, etc.).
const ALLOWLIST = new Set([
  'components/ui/AnimatedTestimonials.vue',
  'components/ui/BackgroundGradientAnimation.vue',
  'components/ui/animations',
  'components/ui/backgrounds',
  'components/base',
  'pages/panel/styleguide.vue',
]);

// ----------------------------------------------------------------------------
// Form-control background check (panel only): every native <input>, <select>,
// <textarea> in panel templates must declare a semantic background token.
// The other rules catch *forbidden* classes; this one catches their *absence*
// — a bare control inherits the user-agent default (white) which renders
// blinding-bright in dark mode.
// ----------------------------------------------------------------------------

// Native form types that legitimately have no background (checkbox/radio show
// only the indicator; file/submit/button/image/reset/range/color are buttons or
// have user-agent-provided visuals; hidden has no UI).
const FORM_CONTROL_TYPES_WITHOUT_BG = new Set([
  'checkbox', 'radio', 'file', 'submit', 'button', 'image', 'reset',
  'range', 'color', 'hidden',
]);

// Background tokens that satisfy the requirement. Includes dynamic-class
// matches: if the attribute string contains any of these substrings (whether
// in a static `class="..."`, a `:class="{ 'bg-X': cond }"`, or a `v-bind`),
// we accept it.
const ALLOWED_BG_PATTERNS = [
  /\bbg-input-bg\b/,
  /\bbg-input-text\b/,
  /\bbg-input-placeholder\b/,
  /\bbg-surface(?:-muted|-raised)?\b/,
  /\bbg-primary(?:-strong|-soft)?\b/,
  /\bbg-accent(?:-soft)?\b/,
  /\bbg-(?:success|warning|danger)-(?:soft|strong)\b/,
  /\bbg-on-(?:primary|danger)\b/,
  /\bbg-transparent\b/,
];

const FORM_CONTROL_TAG_RE = /<(input|select|textarea)\b([^>]*)>/gi;
// Extract `type="..."`/`type='...'` value from the attribute blob.
const TYPE_ATTR_RE = /\btype\s*=\s*['"]([^'"]+)['"]/i;

function findFormControlsMissingBg(content) {
  const found = [];
  const lineStarts = [0];
  for (let i = 0; i < content.length; i++) {
    if (content[i] === '\n') lineStarts.push(i + 1);
  }
  const offsetToLine = (offset) => {
    // Binary search lineStarts for the largest start <= offset.
    let lo = 0, hi = lineStarts.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >>> 1;
      if (lineStarts[mid] <= offset) lo = mid; else hi = mid - 1;
    }
    return lo + 1; // 1-indexed
  };

  // Skip <script> and <style> blocks — input/select/textarea inside them are
  // strings/comments, not real DOM.
  const skipRanges = [];
  const sectionRe = /<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi;
  let sm;
  while ((sm = sectionRe.exec(content)) !== null) {
    skipRanges.push([sm.index, sm.index + sm[0].length]);
  }
  const inSkip = (idx) => skipRanges.some(([s, e]) => idx >= s && idx < e);

  let m;
  FORM_CONTROL_TAG_RE.lastIndex = 0;
  while ((m = FORM_CONTROL_TAG_RE.exec(content)) !== null) {
    if (inSkip(m.index)) continue;
    const tag = m[1].toLowerCase();
    const attrs = m[2];

    // Native HTML elements only. Vue components are PascalCase (handled by the
    // tag regex which only matches lowercase), but be explicit.
    if (tag !== 'input' && tag !== 'select' && tag !== 'textarea') continue;

    // For <input>, skip control types that don't render a fillable surface.
    if (tag === 'input') {
      const typeMatch = attrs.match(TYPE_ATTR_RE);
      const inputType = typeMatch ? typeMatch[1].toLowerCase() : 'text';
      if (FORM_CONTROL_TYPES_WITHOUT_BG.has(inputType)) continue;
    }

    // Accept if any allowed bg token appears anywhere in the attribute blob
    // (works for static `class="..."` and for `:class="{ 'bg-X': cond }"`).
    if (ALLOWED_BG_PATTERNS.some((re) => re.test(attrs))) continue;

    // Vue dynamic class binding: the bg token may live in a function or
    // computed property that the static scanner can't follow. Skip rather
    // than false-positive.
    if (/(?::|v-bind:)class\s*=/.test(attrs)) continue;

    found.push({
      line: offsetToLine(m.index),
      tag,
      snippet: m[0].replace(/\s+/g, ' ').slice(0, 120),
    });
  }
  return found;
}

// Reads CLI flags.
const args = process.argv.slice(2);
const strict = args.includes('--strict');
const strictButtons = args.includes('--strict-buttons');
const strictRows = args.includes('--strict-rows');
const quiet = args.includes('--quiet');
const filesIdx = args.indexOf('--files');
const explicitFiles = filesIdx >= 0 ? args.slice(filesIdx + 1).filter((f) => !f.startsWith('--')) : null;
const scopeArg = args.find((a) => a.startsWith('--scope='));
const scope = scopeArg ? scopeArg.split('=')[1] : 'full';

const SCOPES = {
  full: () => true,
  panel: (rel) =>
    rel.startsWith('pages/panel/') ||
    rel.startsWith('components/panel/') ||
    rel.startsWith('components/Panel/') ||
    rel.startsWith('components/Tasks/') ||
    rel.startsWith('components/accounting/') ||
    rel.startsWith('components/clients/') ||
    rel.startsWith('components/proposals/') ||
    rel.startsWith('components/views/') ||
    rel.startsWith('components/BusinessProposal/admin/'),
  // Public business-proposal viewer only — carved out of `public` so it can
  // graduate to a hard CI gate independently of blog/portfolio/landings.
  'proposal-public': (rel) =>
    rel.startsWith('pages/proposal/') ||
    (rel.startsWith('components/BusinessProposal/') && !rel.startsWith('components/BusinessProposal/admin/')),
  public: (rel) =>
    rel.startsWith('pages/proposal/') ||
    rel.startsWith('pages/diagnostic/') ||
    rel.startsWith('pages/blog/') ||
    rel.startsWith('pages/portfolio') ||
    rel.startsWith('pages/landing') ||
    (rel.startsWith('components/BusinessProposal/') && !rel.startsWith('components/BusinessProposal/admin/')),
};
const inScope = SCOPES[scope] || SCOPES.full;

function isAllowed(relPath) {
  for (const entry of ALLOWLIST) {
    if (relPath === entry || relPath.startsWith(`${entry}/`)) return true;
  }
  return false;
}

function walk(dir, acc = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full, acc);
    } else if (/\.(vue|js|ts|jsx|tsx)$/.test(entry.name)) {
      acc.push(full);
    }
  }
  return acc;
}

function targetFiles() {
  if (explicitFiles && explicitFiles.length) {
    return explicitFiles
      .map((f) => path.resolve(f))
      .filter((f) => fs.existsSync(f));
  }
  const roots = ['pages', 'components', 'layouts'].map((r) => path.join(FRONTEND_ROOT, r));
  return roots.flatMap((r) => (fs.existsSync(r) ? walk(r) : []));
}

// Returns a Set of 1-indexed line numbers that fall inside a `<style>` block
// in a .vue file. Those lines contain CSS, not Tailwind classes, so they
// must be excluded from the invalid-token scan (CSS property names like
// `border-bottom`, `text-align`, `border-radius` collide with the regex).
function styleBlockLines(content) {
  const inside = new Set();
  const re = /<style\b[^>]*>([\s\S]*?)<\/style>/gi;
  let m;
  while ((m = re.exec(content)) !== null) {
    const startOffset = m.index + m[0].indexOf('>') + 1;
    const endOffset = m.index + m[0].length - '</style>'.length;
    const before = content.slice(0, startOffset);
    const startLine = before.split('\n').length; // 1-indexed
    const blockLines = content.slice(startOffset, endOffset).split('\n').length;
    for (let i = 0; i < blockLines; i++) inside.add(startLine + i);
  }
  return inside;
}

// Panel-scope predicate (used to gate the form-control rule, regardless of the
// current --scope flag — the rule is panel-only because public/platform pages
// are mid-migration and the rule would create false positives there).
const isPanelFile = SCOPES.panel;

// ----------------------------------------------------------------------------
// Raw-button detection: a native <button> that hand-writes its own chrome
// instead of using <BaseButton variant="...">.
//
// Why: the app accumulated 528 distinct class strings across 854 raw buttons,
// and 43 different visual treatments for "delete" alone. Every hand-styled
// button is a new dialect. BaseButton exposes one variant per kind of action
// (see components/base/README.md → Button variants).
//
// Not every <button> is an offense. Tabs, segmented controls and selectable
// list rows are legitimately native — they are not actions and map to no
// variant. Mark those with `design-tokens: allow-raw-button` in a comment on
// or just above the tag.
const ALLOW_RAW_BUTTON = 'design-tokens: allow-raw-button';

// Chrome = the things that make an element *look* like a button. A bare
// <button> with no styling is not what this rule is after.
const BUTTON_CHROME = [
  { pattern: /\bbg-(?!transparent\b)[a-z]/, suggest: 'variant="primary" / "secondary" / "danger" / "accent"' },
  { pattern: /\brounded-/, suggest: 'BaseButton owns the radius — pick a variant and a size' },
  { pattern: /\bpx-\d/, suggest: 'BaseButton owns the padding — use size="sm|md|lg"' },
  { pattern: /\btext-(?:red|rose)-\d/, suggest: 'variant="danger" (confirmed) / "danger-ghost" (inline)' },
  { pattern: /\btext-danger-strong\b/, suggest: 'variant="danger" (confirmed) / "danger-ghost" (inline)' },
];

// Returns the full text of the tag starting at `from`, quote-aware so a `>`
// inside a :class expression or an attribute value doesn't end it early.
function readTag(content, from) {
  let quote = null;
  for (let i = from; i < content.length; i++) {
    const ch = content[i];
    if (quote) {
      if (ch === quote) quote = null;
    } else if (ch === '"' || ch === "'") {
      quote = ch;
    } else if (ch === '>') {
      return content.slice(from, i + 1);
    }
  }
  return content.slice(from);
}

// Índice de offsets → línea, compartido por las reglas que trabajan sobre el
// contenido entero en vez de línea por línea.
function buildLineIndex(content) {
  const lineStarts = [];
  let acc = 0;
  for (const l of content.split('\n')) {
    lineStarts.push(acc);
    acc += l.length + 1;
  }
  const lineOf = (offset) => {
    let lo = 0;
    let hi = lineStarts.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (lineStarts[mid] <= offset) lo = mid;
      else hi = mid - 1;
    }
    return lo + 1; // 1-indexed
  };
  return { lineStarts, lineOf };
}

function findRawStyledButtons(content) {
  const found = [];
  const { lineStarts, lineOf } = buildLineIndex(content);

  const re = /<button\b/g;
  let m;
  while ((m = re.exec(content)) !== null) {
    const tag = readTag(content, m.index);
    const line = lineOf(m.index);
    // Opt-out on the tag itself or on the two lines above it.
    const contextStart = lineStarts[Math.max(0, line - 3)];
    if (content.slice(contextStart, m.index + tag.length).includes(ALLOW_RAW_BUTTON)) continue;
    for (const { pattern, suggest } of BUTTON_CHROME) {
      if (pattern.test(tag)) {
        found.push({ line, suggest });
        break;
      }
    }
  }
  return found;
}

// ----------------------------------------------------------------------------
// MANUAL_MODIFIER_NAVIGATION: a screen reading ctrlKey/metaKey to decide how to
// navigate is reimplementing an <a href> in JavaScript.
//
// Why: every listing that did this reimplemented a different fraction of it.
// Proposals and diagnostics branched to window.open on ctrl/cmd; documents had
// no branch at all, so ctrl+click opened in the same tab. None of them could
// serve middle click, "open in new tab" from the context menu, copying the
// address or the keyboard, because none of that is reachable without an href.
//
// The fix is never a better branch — it is a real link. The ONE place allowed
// to read modifiers is the shared primitive that decides what a row gesture
// means; naming it here is also how that exception stays documented.
const ALLOW_MANUAL_MODIFIER = 'design-tokens: allow-manual-modifier';
const MODIFIER_NAV_EXEMPT = new Set(['utils/rowNavigation.js']);
const MODIFIER_RE = /\b(?:ctrlKey|metaKey)\b/;
const NAVIGATION_RE = /(?:window\.open\(|router\.push\(|navigateTo\(|location\.href)/;
// Ancho de la ventana de coocurrencia. Una tecla modificadora sola no dice
// nada — `metaKey` es también un nombre de variable razonable; lo que delata al
// patrón es tenerla al lado de una navegación.
const MODIFIER_NAV_PROXIMITY = 8;

function findManualModifierNavigation(lines) {
  const found = [];
  for (let i = 0; i < lines.length; i++) {
    if (!MODIFIER_RE.test(lines[i])) continue;
    const from = Math.max(0, i - MODIFIER_NAV_PROXIMITY);
    const to = Math.min(lines.length, i + MODIFIER_NAV_PROXIMITY + 1);
    const window = lines.slice(from, to);
    if (!window.some((l) => NAVIGATION_RE.test(l))) continue;
    if (window.some((l) => l.includes(ALLOW_MANUAL_MODIFIER))) continue;
    found.push({ line: i + 1 });
  }
  return found;
}

// ----------------------------------------------------------------------------
// ROW_LINK_MISSING: a repeated row that navigates on click but holds no link.
//
// Why: a <tr>/<div> with @click is the convenience half of a link. Without an
// <a href> inside, the row cannot be opened in another tab, cannot have its
// address copied, does not preview in the status bar and is unreachable by
// keyboard. See components/base/README.md → Navigable rows.
//
// The rule does NOT look at handler names: after the fix a row still reads
// @click="navigateToProposal(...)", only guarded. A rule whose green state is
// "everybody added the opt-out marker" teaches nothing — this one goes green
// because a real link appeared.
//
// Deliberately narrow: only a tag carrying BOTH v-for and @click. Rows that
// merely expand in place (the clients accordion, the accounting history tables)
// are legitimate and mark themselves with the opt-out when they trip it.
const ALLOW_CLICKABLE_ROW = 'design-tokens: allow-clickable-row';
const ROW_TAG_RE = /<(tr|li|article|div)\b/g;
const ROW_LINK_RE = /<(?:a\s|a>|NuxtLink\b|BaseRowLink\b|nuxt-link\b)/;
// Un rol interactivo propio significa que la fila no es un destino sino un
// control: una opción de autocompletado, una pestaña, un ítem de menú.
const ROW_NON_DESTINATION_RE = /role="(?:option|tab|menuitem|menuitemradio|checkbox|radio)"/;

// Devuelve el bloque completo del elemento abierto en `from`, contando anidados
// del mismo tag. Si no cierra (markup raro), devuelve lo que quede.
function readElementBlock(content, from, tag) {
  const open = new RegExp(`<${tag}\\b`, 'g');
  const close = new RegExp(`</${tag}\\s*>`, 'g');
  open.lastIndex = from + 1;
  close.lastIndex = from + 1;
  let depth = 1;
  let cursor = from + 1;
  while (depth > 0) {
    open.lastIndex = cursor;
    close.lastIndex = cursor;
    const nextOpen = open.exec(content);
    const nextClose = close.exec(content);
    if (!nextClose) return content.slice(from);
    if (nextOpen && nextOpen.index < nextClose.index) {
      depth += 1;
      cursor = nextOpen.index + 1;
    } else {
      depth -= 1;
      cursor = nextClose.index + 1;
      if (depth === 0) return content.slice(from, nextClose.index + nextClose[0].length);
    }
  }
  return content.slice(from);
}

function findRowsWithoutLink(content, lineOf, lineStarts) {
  const found = [];
  ROW_TAG_RE.lastIndex = 0;
  let m;
  while ((m = ROW_TAG_RE.exec(content)) !== null) {
    const tag = readTag(content, m.index);
    if (!/\bv-for\b/.test(tag)) continue;
    if (!/@click(?![.\w-]*\bself\b)/.test(tag) || /@click\.self/.test(tag)) continue;
    if (ROW_NON_DESTINATION_RE.test(tag)) continue;
    const line = lineOf(m.index);
    const contextStart = lineStarts[Math.max(0, line - 3)];
    if (content.slice(contextStart, m.index + tag.length).includes(ALLOW_CLICKABLE_ROW)) continue;
    const block = readElementBlock(content, m.index, m[1]);
    if (ROW_LINK_RE.test(block)) continue;
    found.push({ line, tag: m[1] });
  }
  return found;
}

const offenses = [];
const invalidTokenOffenses = [];
const formControlOffenses = [];
const rawButtonOffenses = [];
const modifierNavOffenses = [];
const rowLinkOffenses = [];
for (const file of targetFiles()) {
  const rel = path.relative(FRONTEND_ROOT, file);
  if (isAllowed(rel)) continue;
  if (!inScope(rel)) continue;
  const content = fs.readFileSync(file, 'utf8');
  const lines = content.split('\n');
  const styleLines = file.endsWith('.vue') ? styleBlockLines(content) : new Set();
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNo = i + 1;
    if (!SKIP_LINE_RE.test(line) && !styleLines.has(lineNo)) {
      for (const bad of findInvalidTokens(line)) {
        invalidTokenOffenses.push({ file: rel, line: lineNo, match: bad.match, token: bad.token });
      }
    }
    for (const { pattern, suggest } of FORBIDDEN) {
      const m = line.match(pattern);
      if (m) {
        offenses.push({ file: rel, line: lineNo, match: m[0], suggest });
        break; // one offense per line is enough
      }
    }
    for (const { pattern, suggest, allowedIn } of FORBIDDEN_CONDITIONAL) {
      if (allowedIn.has(rel)) continue;
      const m = line.match(pattern);
      if (m) {
        offenses.push({ file: rel, line: lineNo, match: m[0], suggest });
        break;
      }
    }
    if (!styleLines.has(lineNo)) {
      const m = line.match(ALPHA_BAKED_PATTERN);
      if (m) {
        offenses.push({
          file: rel,
          line: lineNo,
          match: m[0],
          suggest: `drop the /N modifier — ${m[1]} is alpha-baked in dark (see theme.css)`,
        });
      }
    }
  }
  if (file.endsWith('.vue') && isPanelFile(rel)) {
    for (const fc of findFormControlsMissingBg(content)) {
      formControlOffenses.push({ file: rel, line: fc.line, tag: fc.tag, snippet: fc.snippet });
    }
  }
  if (file.endsWith('.vue')) {
    for (const rb of findRawStyledButtons(content)) {
      rawButtonOffenses.push({ file: rel, line: rb.line, suggest: rb.suggest });
    }
  }
  if (!MODIFIER_NAV_EXEMPT.has(rel)) {
    for (const mn of findManualModifierNavigation(lines)) {
      modifierNavOffenses.push({ file: rel, line: mn.line });
    }
  }
  if (file.endsWith('.vue')) {
    const { lineStarts, lineOf } = buildLineIndex(content);
    for (const rl of findRowsWithoutLink(content, lineOf, lineStarts)) {
      rowLinkOffenses.push({ file: rel, line: rl.line, tag: rl.tag });
    }
  }
}

// Raw buttons are reported but do not gate by default. 629 of them still live
// in files people edit daily, so gating on --strict would turn every unrelated
// one-line edit into a full button migration of that file — which is how a
// useful rule gets deleted. Pass --strict-buttons to gate on it (do that once
// the migration lands; the count is the progress bar until then).
// MANUAL_MODIFIER_NAVIGATION gates unconditionally: it landed green (the only
// two occurrences were removed by the change that introduced the rule), and the
// anti-pattern has a unique fingerprint, so there is no migration to wait out.
//
// ROW_LINK_MISSING waits behind --strict-rows for the same reason raw buttons
// wait behind --strict-buttons: rows whose detail has no address yet cannot be
// fixed by adding a link, only by inventing the address first.
const gatingOffenses = offenses.length + invalidTokenOffenses.length + formControlOffenses.length
  + modifierNavOffenses.length
  + (strictButtons ? rawButtonOffenses.length : 0)
  + (strictRows ? rowLinkOffenses.length : 0);
const totalOffenses = offenses.length + invalidTokenOffenses.length + formControlOffenses.length
  + rawButtonOffenses.length + modifierNavOffenses.length + rowLinkOffenses.length;
if (totalOffenses === 0) {
  console.log(`✓ design-tokens: no forbidden literals, invalid tokens, unstyled form controls, raw styled buttons, hand-rolled modifier navigation or clickable rows without a link found (scope=${scope})`);
  process.exit(0);
}

const grouped = offenses.reduce((acc, o) => {
  (acc[o.file] = acc[o.file] || []).push(o);
  return acc;
}, {});

const groupedInvalid = invalidTokenOffenses.reduce((acc, o) => {
  (acc[o.file] = acc[o.file] || []).push(o);
  return acc;
}, {});

const groupedFormControls = formControlOffenses.reduce((acc, o) => {
  (acc[o.file] = acc[o.file] || []).push(o);
  return acc;
}, {});

const groupedRawButtons = rawButtonOffenses.reduce((acc, o) => {
  (acc[o.file] = acc[o.file] || []).push(o);
  return acc;
}, {});

const groupedModifierNav = modifierNavOffenses.reduce((acc, o) => {
  (acc[o.file] = acc[o.file] || []).push(o);
  return acc;
}, {});

const groupedRowLinks = rowLinkOffenses.reduce((acc, o) => {
  (acc[o.file] = acc[o.file] || []).push(o);
  return acc;
}, {});

const forbiddenSummary = `${offenses.length} forbidden literal${offenses.length === 1 ? '' : 's'} across ${Object.keys(grouped).length} file${Object.keys(grouped).length === 1 ? '' : 's'}`;
const invalidSummary = `${invalidTokenOffenses.length} invalid token reference${invalidTokenOffenses.length === 1 ? '' : 's'} across ${Object.keys(groupedInvalid).length} file${Object.keys(groupedInvalid).length === 1 ? '' : 's'}`;
const formControlSummary = `${formControlOffenses.length} form control${formControlOffenses.length === 1 ? '' : 's'} without semantic bg across ${Object.keys(groupedFormControls).length} file${Object.keys(groupedFormControls).length === 1 ? '' : 's'}`;
const rawButtonSummary = `${rawButtonOffenses.length} raw styled button${rawButtonOffenses.length === 1 ? '' : 's'} across ${Object.keys(groupedRawButtons).length} file${Object.keys(groupedRawButtons).length === 1 ? '' : 's'}`;
const modifierNavSummary = `${modifierNavOffenses.length} hand-rolled modifier navigation${modifierNavOffenses.length === 1 ? '' : 's'} across ${Object.keys(groupedModifierNav).length} file${Object.keys(groupedModifierNav).length === 1 ? '' : 's'}`;
const rowLinkSummary = `${rowLinkOffenses.length} clickable row${rowLinkOffenses.length === 1 ? '' : 's'} without a link across ${Object.keys(groupedRowLinks).length} file${Object.keys(groupedRowLinks).length === 1 ? '' : 's'}`;
const summary = `design-tokens: ${forbiddenSummary}, ${invalidSummary}, ${formControlSummary}, ${rawButtonSummary}, ${modifierNavSummary}, ${rowLinkSummary} (scope=${scope})`;

if (quiet) {
  console.log(summary);
} else {
  console.log(`${summary}\n`);
  if (offenses.length) {
    console.log(`FORBIDDEN — legacy literals that must use semantic tokens:`);
    for (const [file, list] of Object.entries(grouped)) {
      console.log(`  ${file}`);
      for (const o of list) {
        console.log(`    L${o.line}  ${o.match}  →  ${o.suggest}`);
      }
    }
  }
  if (invalidTokenOffenses.length) {
    if (offenses.length) console.log('');
    console.log(`INVALID_TOKEN_REFERENCES — token does not exist in tailwind.config.js or Tailwind defaults:`);
    for (const [file, list] of Object.entries(groupedInvalid)) {
      console.log(`  ${file}`);
      for (const o of list) {
        console.log(`    L${o.line}  ${o.match}  (unknown token: ${o.token})`);
      }
    }
  }
  if (rawButtonOffenses.length) {
    if (offenses.length || invalidTokenOffenses.length) console.log('');
    console.log(`RAW_BUTTON_STYLING — native <button> hand-writing its own chrome instead of <BaseButton variant="...">:`);
    console.log(`  One variant per kind of action — see components/base/README.md → Button variants.`);
    console.log(`  Tabs, segmented controls and selectable list rows are not actions: mark those`);
    console.log(`  with a "design-tokens: allow-raw-button" comment on or above the tag.`);
    for (const [file, list] of Object.entries(groupedRawButtons)) {
      console.log(`  ${file}`);
      for (const o of list) {
        console.log(`    L${o.line}  →  ${o.suggest}`);
      }
    }
  }
  if (formControlOffenses.length) {
    if (offenses.length || invalidTokenOffenses.length) console.log('');
    console.log(`UNSTYLED_FORM_CONTROLS — native <input>/<select>/<textarea> in panel without a semantic background:`);
    console.log(`  Add bg-input-bg (preferred) or bg-surface / bg-transparent / use a Base* component.`);
    for (const [file, list] of Object.entries(groupedFormControls)) {
      console.log(`  ${file}`);
      for (const o of list) {
        console.log(`    L${o.line}  <${o.tag}>  ${o.snippet}`);
      }
    }
  }
  if (modifierNavOffenses.length) {
    console.log('');
    console.log(`MANUAL_MODIFIER_NAVIGATION — reading ctrlKey/metaKey to decide how to navigate:`);
    console.log(`  That is an <a href> written in JavaScript, and it can only ever answer one`);
    console.log(`  gesture. Give the row a real link (BaseRowLink) and let useRowNavigation`);
    console.log(`  handle the click — see components/base/README.md → Navigable rows.`);
    for (const [file, list] of Object.entries(groupedModifierNav)) {
      console.log(`  ${file}`);
      for (const o of list) {
        console.log(`    L${o.line}  →  BaseRowLink + useRowNavigation`);
      }
    }
  }
  if (rowLinkOffenses.length) {
    console.log('');
    console.log(`ROW_LINK_MISSING — a repeated row with @click and no link inside:`);
    console.log(`  Without an <a href> the row cannot be opened in another tab, copied, or`);
    console.log(`  reached by keyboard. Put a <BaseRowLink :to> on its title.`);
    console.log(`  A row that only expands in place is not a destination: mark it with a`);
    console.log(`  "design-tokens: allow-clickable-row" comment on or above the tag.`);
    for (const [file, list] of Object.entries(groupedRowLinks)) {
      console.log(`  ${file}`);
      for (const o of list) {
        console.log(`    L${o.line}  <${o.tag} v-for @click>  →  add a <BaseRowLink :to>`);
      }
    }
  }
  console.log('\nSee frontend/components/base/README.md for the token table.');
}

process.exit(strict && gatingOffenses > 0 ? 1 : 0);
