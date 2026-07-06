/**
 * resolvePanelBreadcrumb derives labels/sections from panelNav with Spanish
 * display overrides. The five title-pinned routes asserted by
 * e2e/admin/admin-layout-title-mapping.spec.js must never change here.
 */
import { getPanelNavSections } from '~/config/panelNav';
import { resolvePanelBreadcrumb } from '~/utils/panelBreadcrumbs';

const lp = (p) => p;
const sections = getPanelNavSections(lp);
const resolve = (path) => resolvePanelBreadcrumb(path, sections);

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
    expect(resolve('/es-co/panel/proposals')).toEqual({ label: 'Propuestas', section: 'Sales' });
    expect(resolve('/en-us/panel/linkedin')).toEqual({ label: 'LinkedIn', section: 'ProjectApp content' });
  });

  it('gives previously-missing nav routes a breadcrumb automatically', () => {
    expect(resolve('/panel/linkedin')).toEqual({ label: 'LinkedIn', section: 'ProjectApp content' });
    expect(resolve('/panel/mcps')).toEqual({ label: 'MCPs', section: 'Integrations' });
    expect(resolve('/panel/accounting/cards')).toEqual({ label: 'Tarjetas', section: 'Accounting' });
  });

  it('resolves dynamic edit routes with corrected section labels', () => {
    expect(resolve('/panel/blog/55/edit')).toEqual({ label: 'Edit. post', section: 'ProjectApp content' });
    expect(resolve('/panel/portfolio/9/edit')).toEqual({ label: 'Edit. portfolio', section: 'ProjectApp content' });
    expect(resolve('/panel/documents/3/edit')).toEqual({ label: 'Edit. documento', section: 'Documents' });
    expect(resolve('/panel/diagnostics/7/edit')).toEqual({ label: 'Edit. diagnóstico', section: 'Sales' });
  });

  it('covers create/stub sub-routes through direct overrides with the parent section', () => {
    expect(resolve('/panel/blog/create')).toEqual({ label: 'Nuevo post', section: 'ProjectApp content' });
    expect(resolve('/panel/documents/create')).toEqual({ label: 'Nuevo doc.', section: 'Documents' });
    expect(resolve('/panel/diagnostics/defaults')).toEqual({ label: 'Diag. defaults', section: 'Sales' });
  });

  it('keeps accounting overview exact-match semantics', () => {
    expect(resolve('/panel/accounting')).toEqual({ label: 'Resumen', section: 'Accounting' });
    expect(resolve('/panel/accounting/incomes')).toEqual({ label: 'Ingresos', section: 'Accounting' });
  });

  it('returns null for unknown panel paths', () => {
    expect(resolve('/panel/unknown-route')).toBeNull();
    expect(resolve('/platform/projects')).toBeNull();
  });
});
