/**
 * resolvePanelBreadcrumb derives labels/sections from panelNav with Spanish
 * display overrides. The five title-pinned routes asserted by
 * e2e/admin/admin-layout-title-mapping.spec.js must never change here.
 *
 * Section expectations are read from panelNav itself (not hardcoded), so
 * renaming a sidebar section does not break this suite — the contract under
 * test is the ROUTING (which nav section a route resolves to), not the
 * section label text.
 */
import { getPanelNavSections } from '~/config/panelNav';
import { resolvePanelBreadcrumb } from '~/utils/panelBreadcrumbs';

const lp = (p) => p;
const sections = getPanelNavSections(lp);
const resolve = (path) => resolvePanelBreadcrumb(path, sections);

/** Label of the nav section containing an item with this exact href. */
function sectionOf(href) {
  const section = sections.find((s) => (s.items || []).some((i) => i.href === href));
  if (!section) throw new Error(`No nav section contains href ${href}`);
  return section.label;
}

describe('resolvePanelBreadcrumb', () => {
  describe('labels pinned by the E2E title-mapping contract', () => {
    it.each([
      ['/panel', 'Dashboard'],
      ['/panel/proposals', 'Propuestas'],
      ['/panel/proposals/create', 'Nueva prop.'],
      ['/panel/proposals/123/edit', 'Edit. propuesta'],
      ['/panel/blog/calendar', 'Calendario'],
    ])('%s → %s', (path, label) => {
      expect(resolve(path)?.label).toBe(label);
    });
  });

  it('strips the locale prefix before matching', () => {
    expect(resolve('/es-co/panel/proposals')).toEqual({
      label: 'Propuestas',
      section: sectionOf('/panel/proposals'),
    });
    expect(resolve('/en-us/panel/linkedin')).toEqual({
      label: 'LinkedIn',
      section: sectionOf('/panel/linkedin'),
    });
  });

  it('gives previously-missing nav routes a breadcrumb automatically', () => {
    expect(resolve('/panel/linkedin')).toEqual({ label: 'LinkedIn', section: sectionOf('/panel/linkedin') });
    expect(resolve('/panel/mcps')).toEqual({ label: 'MCPs', section: sectionOf('/panel/mcps') });
    expect(resolve('/panel/accounting/cards')).toEqual({
      label: 'Tarjetas',
      section: sectionOf('/panel/accounting/cards'),
    });
  });

  it('resolves dynamic edit routes with the section of their nav ancestor', () => {
    expect(resolve('/panel/blog/55/edit')).toEqual({ label: 'Edit. post', section: sectionOf('/panel/blog') });
    expect(resolve('/panel/portfolio/9/edit')).toEqual({ label: 'Edit. portfolio', section: sectionOf('/panel/portfolio') });
    expect(resolve('/panel/documents/3/edit')).toEqual({ label: 'Edit. documento', section: sectionOf('/panel/documents') });
    expect(resolve('/panel/diagnostics/7/edit')).toEqual({ label: 'Edit. diagnóstico', section: sectionOf('/panel/diagnostics') });
  });

  it('covers create/stub sub-routes through direct overrides with the parent section', () => {
    expect(resolve('/panel/blog/create')).toEqual({ label: 'Nuevo post', section: sectionOf('/panel/blog') });
    expect(resolve('/panel/documents/create')).toEqual({ label: 'Nuevo doc.', section: sectionOf('/panel/documents') });
    expect(resolve('/panel/diagnostics/defaults')).toEqual({ label: 'Diag. defaults', section: sectionOf('/panel/diagnostics') });
  });

  it('keeps accounting overview exact-match semantics', () => {
    expect(resolve('/panel/accounting')).toEqual({ label: 'Resumen', section: sectionOf('/panel/accounting') });
    expect(resolve('/panel/accounting/incomes')).toEqual({ label: 'Ingresos', section: sectionOf('/panel/accounting/incomes') });
  });

  it('returns null for unknown panel paths', () => {
    expect(resolve('/panel/unknown-route')).toBeNull();
    expect(resolve('/platform/projects')).toBeNull();
  });
});
