#!/usr/bin/env node
/**
 * Design-token guard: scans frontend Vue/JS for hardcoded color literals that
 * should now use semantic tokens (bg-surface, text-text-default, etc.).
 *
 * Why: with the design-system migration, new code must prefer tokens so dark
 * mode and tenant theming "just work" without component-level changes.
 *
 * Behavior:
 *   - Scans pages/, components/, layouts/ (excluding allowlist).
 *   - Reports forbidden literals grouped by file with line numbers.
 *   - Exits with code 0 if no offenses or under the threshold.
 *   - Exits 1 only when --strict is passed (intended for CI on touched files).
 *
 * Usage:
 *   node frontend/scripts/check-design-tokens.mjs              # warn-only, full repo
 *   node frontend/scripts/check-design-tokens.mjs --scope=panel  # admin panel scope only
 *   node frontend/scripts/check-design-tokens.mjs --strict     # exit 1 on any offense
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
  { pattern: /\btext-gray-[5-9]00\b/, suggest: 'text-text-default / text-text-muted / text-text-subtle' },
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

function extractDefinedColors() {
  const configPath = path.join(FRONTEND_ROOT, 'tailwind.config.js');
  const tokens = new Set();
  if (!fs.existsSync(configPath)) return tokens;
  const src = fs.readFileSync(configPath, 'utf8');

  // Find the `colors: { ... }` block inside theme.extend. We grab from the
  // first `colors:` after `extend:` to its matching closing brace, then pull
  // quoted keys out of that slice. This is a simple parser — it assumes the
  // config doesn't have nested objects inside `colors` (the current shape).
  const extendIdx = src.indexOf('extend:');
  if (extendIdx < 0) return tokens;
  const colorsIdx = src.indexOf('colors:', extendIdx);
  if (colorsIdx < 0) return tokens;
  const braceStart = src.indexOf('{', colorsIdx);
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
  ]),
  border: new Set([
    'solid', 'dashed', 'dotted', 'double', 'hidden', 'collapse', 'separate',
    'opacity',
  ]),
  ring: new Set(['inset', 'offset', 'opacity', 'solid', 'dashed', 'dotted', 'double']),
  divide: new Set(['solid', 'dashed', 'dotted', 'double', 'none', 'opacity', 'reverse']),
  outline: new Set(['solid', 'dashed', 'dotted', 'double', 'offset']),
  shadow: new Set(['inner']),
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

// Reads CLI flags.
const args = process.argv.slice(2);
const strict = args.includes('--strict');
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
    rel.startsWith('components/BusinessProposal/admin/'),
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

const offenses = [];
const invalidTokenOffenses = [];
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
  }
}

const totalOffenses = offenses.length + invalidTokenOffenses.length;
if (totalOffenses === 0) {
  console.log(`✓ design-tokens: no forbidden literals or invalid tokens found (scope=${scope})`);
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

const forbiddenSummary = `${offenses.length} forbidden literal${offenses.length === 1 ? '' : 's'} across ${Object.keys(grouped).length} file${Object.keys(grouped).length === 1 ? '' : 's'}`;
const invalidSummary = `${invalidTokenOffenses.length} invalid token reference${invalidTokenOffenses.length === 1 ? '' : 's'} across ${Object.keys(groupedInvalid).length} file${Object.keys(groupedInvalid).length === 1 ? '' : 's'}`;
const summary = `design-tokens: ${forbiddenSummary}, ${invalidSummary} (scope=${scope})`;

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
  console.log('\nSee frontend/components/base/README.md for the token table.');
}

process.exit(strict ? 1 : 0);
