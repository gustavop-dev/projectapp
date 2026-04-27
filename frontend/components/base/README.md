# Base Components & Design Tokens

A thin design-system layer for ProjectApp's frontend. Components in this folder
wrap native HTML elements with semantic theme tokens so dark mode resolves
automatically — no `dark:` variants needed in consumer markup.

## Tokens

Defined in `frontend/assets/styles/theme.css` and exposed as Tailwind colors
(`frontend/tailwind.config.js`). Values flip with the `.dark` class on `<html>`
(toggled by `useDiagnosticDarkMode`).

| Token (Tailwind class)            | Use for                                  |
| --------------------------------- | ---------------------------------------- |
| `bg-surface`                      | primary card / panel background          |
| `bg-surface-muted`                | soft container (page-level wash)         |
| `bg-surface-raised`               | inner panels, chips, segmented controls  |
| `border-border-default`           | default border color                     |
| `border-border-muted`             | subtle dividers                          |
| `text-text-default`               | body / heading text                      |
| `text-text-muted`                 | labels, secondary copy                   |
| `text-text-subtle`                | placeholders, very faint copy            |
| `text-text-brand`                 | brand-tinted legends/headings (flips light/dark) |
| `bg-primary` / `text-primary`     | brand primary (esmerald — constant)      |
| `bg-accent`                       | brand accent (lemon — constant)          |
| `bg-input-bg` / `text-input-text` | form control fill / text                 |
| `border-input-border`             | form control border                      |
| `placeholder-input-placeholder`   | form control placeholder color           |
| `ring-focus-ring`                 | focus ring                               |
| `text-on-primary`                 | foreground (text/icon) on `bg-primary`   |
| `text-on-danger`                  | foreground (text/icon) on `bg-danger-strong` |
| `bg-success-soft / text-success-strong`, `warning-*`, `danger-*` | status pairs |

The legacy hex tokens (`esmerald`, `lemon`, `bone`, `gray-*`, etc.) keep working
unchanged. New work should prefer semantic tokens.

### Opacity modifiers

Semantic tokens are wired through an RGB-triplet bridge
(`rgb(var(--color-X-rgb) / <alpha-value>)`), so Tailwind opacity modifiers
work on every semantic color. Examples:

```html
<div class="bg-primary/40 text-text-brand/60 ring-focus-ring/30" />
<button class="bg-accent/80 hover:bg-accent" />
<span class="border border-border-default/50" />
```

**Caveat — dark-mode tokens with intrinsic alpha.** `surface-raised`,
`border-default`, `border-muted`, `input-border`, and the status `*-soft`
variants are intrinsically `rgba(...)` in dark mode. Their triplet variables
fall back to the underlying solid hue, so an opacity modifier in dark mode
*replaces* the baked alpha rather than composing with it — the result is
unlikely to match design intent.

Recommendation: use opacity modifiers on the "solid" tokens (`primary*`,
`accent*`, `text-*`, `input-text`, `focus-ring`, status `*-strong`,
light-mode soft backgrounds). For the alpha-baked tokens listed above,
prefer the bare class without `/N`.

## Components

| Component       | Props                                                                                  |
| --------------- | -------------------------------------------------------------------------------------- |
| `BaseInput`     | `modelValue`, `type`, `size` (`sm`/`md`), `error`, `placeholder`, `disabled`           |
| `BaseSelect`    | `modelValue`, `options` (array or default slot), `size`, `error`, `placeholder`, `disabled` |
| `BaseTextarea`  | `modelValue`, `rows`, `size`, `error`, `placeholder`, `disabled`                       |
| `BaseButton`    | `variant` (`primary`/`secondary`/`ghost`/`danger`/`accent`), `size` (`sm`/`md`/`lg`), `loading`, `disabled`, `as` |
| `BaseBadge`     | `variant` (`neutral`/`success`/`warning`/`danger`/`accent`/`primary`), `size`          |
| `BaseCard`      | `padding` (`none`/`sm`/`md`/`lg`), `as`                                                |
| `BaseModal`     | `modelValue`, `size` (`sm`/`md`/`lg`/`xl`/`2xl`/`5xl`), `closeOnBackdrop`, `closeOnEsc`, `padding` |
| `BaseToggle`    | `modelValue`, `size` (`sm`/`md`), `disabled`, `ariaLabel`, `onClass` / `offClass` (override colors for status toggles, e.g. `on-class="bg-warning-strong"`) |
| `BaseCheckbox`  | `modelValue`, `value`, `disabled` — label via default slot                             |
| `BaseFormField` | `label`, `hint`, `error`, `required`, `for`, `size` — wrap any control in the default slot |
| `BaseSegmented` | `modelValue`, `options` (array of `{ value, label, testId? }` or strings), `size` (`sm`/`md`), `fullWidth` — segmented control / pill tabs |
| `BaseTabs`      | `modelValue`, `tabs` (array of `{ id, label, badge?, disabled? }`), `variant` (`underline`/`pill`), `fullWidth` — desktop tab bar with mobile `<select>` fallback |
| `BaseDropdown`  | `items` (array of `{ label, onClick?, to?, icon?, disabled?, danger?, divider? }`), `align` (`left`/`right`), `width` — Headless UI Menu wrapper. Trigger via `#trigger` slot |
| `BaseAlert`     | `variant` (`info`/`success`/`warning`/`danger`), `title`, `dismissible`. Icon via `#icon` slot, body via default slot |
| `BaseEmptyState` | `title`, `description`. Icon via `#icon`, custom body via default, CTA via `#actions` |
| `BaseTooltip`   | `position` (`top`/`bottom`/`left`/`right`), `backgroundColor`, `textColor`, `width`, `minWidth`. Trigger via `#trigger`, body via default slot. Click for touch, hover for desktop |

Components are auto-imported by Nuxt — use them directly in templates without
an explicit `import`.

## Border-radius scale

Stick to the same three values across the system:

- `rounded-md` — small (chips, compact inputs)
- `rounded-xl` — default (cards, inputs, buttons)
- `rounded-full` — pills, avatars, badges

## Migration example

Before:

```html
<input
  v-model="form.email"
  type="email"
  class="w-full px-4 py-2.5 border border-gray-200 dark:border-white/[0.08]
         dark:bg-esmerald-dark dark:text-white dark:placeholder:text-green-light/40
         rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500
         outline-none bg-white"
/>
```

After:

```html
<BaseInput v-model="form.email" type="email" />
```

Dark mode is handled by the `bg-input-bg` / `border-input-border` tokens that
the component uses internally.

## Platform tenant theming

When a tenant has a custom `theme_color`, `usePlatformCustomTheme.applyTheme()`
overrides `--color-primary`, `--color-primary-strong`, `--color-primary-soft`,
`--color-text-brand`, and `--color-focus-ring` on `documentElement`. Base
components automatically reflect the tenant's brand color without needing any
component-level changes. When the tenant clears the theme, the overrides are
removed and the defaults from `assets/styles/theme.css` take over again.

## UI components migrated to tokens

These live in `frontend/components/ui/` (separate from base) but already use semantic
tokens, so they pair cleanly with the base layer:

- `FilterToggleButton` — `open`, `count`. Active state uses `bg-primary text-white`,
  inactive uses `bg-surface text-text-muted border-border-default`.

(`ResponsiveTabs` and `Tooltip` were deprecated and removed — use `BaseTabs`
and `BaseTooltip` instead.)

## Lint guard

`scripts/check-design-tokens.mjs` scans for forbidden color literals
(`bg-white`, `bg-esmerald`, `dark:bg-gray-700`, `text-gray-700`,
`bg-emerald-600`, etc.) and prints what to use instead.

```bash
npm --prefix frontend run check:design-tokens          # full repo, warn-only
npm --prefix frontend run check:design-tokens:panel    # admin panel scope only
npm --prefix frontend run check:design-tokens:strict   # exit 1 on any offense (CI / pre-commit)
node frontend/scripts/check-design-tokens.mjs --files path/to/file.vue   # focused check on touched files
```

The script accepts `--scope=panel|public|full` and `--quiet` (summary only).
The base components (`components/base/`), the styleguide page, and decorative
UI components (`AnimatedTestimonials`, `BackgroundGradientAnimation`) are
allowlisted.

When you migrate a tab or component to tokens, run
`check:design-tokens --scope=panel --quiet` before and after to track progress.

### CI gating policy

The `design-tokens-guard` job in `.github/workflows/ci.yml` enforces three
distinct checks on every PR:

- **Per-PR (touched files): hard gate.** Files changed in the PR are run
  through `--strict --files <touched>`. Any new offense in a touched file
  fails the build. This keeps the migration incremental for legacy code that
  the PR does not touch.
- **Panel scope: hard gate.** `--scope=panel --strict` runs against the full
  panel surface on every PR (not just touched files). Now that panel sits at
  0 offenses, this prevents regressions introduced by new components added
  under `components/panel/` or imported indirectly into the panel without
  being modified by the PR.
- **Public scope: warn-only.** `--scope=public --quiet` runs with a trailing
  `|| true` so the delta is visible in CI logs and the PR comment without
  blocking the build. The public site is still mid-migration; this surfaces
  progress without forcing churn.

## Migration policy

- New views and components: use base components and semantic tokens.
- Legacy code: migrate when you are already touching the file. Coexistence is
  fine — old hex tokens stay valid.

### Legacy hex tokens (deprecated)

`esmerald`, `esmerald-dark`, `esmerald-light`, `lemon`, `bone`, `brown`,
`window-black`, `green-light` and bare `black`/`dark` are kept in
`tailwind.config.js` as raw hex for backwards compatibility. They are heavily
used (~3000 across the public site, ~360 in the panel) and many use opacity
modifiers like `bg-esmerald/40` which the current var-based semantic tokens
do not support cleanly.

**Do not introduce new uses.** The lint guard flags them. They will be
folded into the semantic system (`bg-esmerald` → `bg-primary`, etc.) once
the panel offense count drops low enough to coordinate the migration without
visual regressions on the public site.
- For pilots already migrated, see:
  - `components/panel/defaults/ProposalDefaultsPanel.vue` (general tab)
  - `pages/panel/proposals/[id]/edit.vue` (general tab + activity)
  - `components/BusinessProposal/admin/ContractParamsModal.vue`

## Visual regression

The styleguide page (`/panel/styleguide`) has full-page Playwright screenshot
coverage in light and dark mode. The spec lives at
`frontend/e2e/visual/styleguide.spec.js` and its baseline PNGs at
`frontend/e2e/visual/styleguide.spec.js-snapshots/`.

The intent is to catch unintended pixel changes when tokens, base components,
or shared layout chrome are touched — not to lock the design forever.

Run the visual specs:

```bash
npm --prefix frontend run e2e -- e2e/visual/styleguide.spec.js
```

Regenerate baselines (only after an *intentional* design change):

```bash
npm --prefix frontend run e2e -- e2e/visual/styleguide.spec.js --update-snapshots
```

When to regenerate:

- Yes: you changed tokens in `assets/styles/theme.css`, edited a base
  component on purpose, or added a new section to `pages/panel/styleguide.vue`.
- No: a test went red after an unrelated refactor or "harmless" tweak —
  inspect the diff (`e2e-results/` HTML report) and fix the regression
  instead of overwriting the baseline.

The first CI run on a fresh checkout has no baseline and will write the
PNGs on the spot. Commit the generated PNGs together with the change that
produced them so reviewers can eyeball the new look.
