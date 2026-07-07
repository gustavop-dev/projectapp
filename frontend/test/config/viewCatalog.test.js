import {
  countCatalogViews,
  getViewCopyReference,
  groupSectionViews,
  isOpenableViewUrl,
  proposalViewReferenceGuide,
  viewCatalogSections,
} from '../../config/viewCatalog';

import { viewAudienceOptions, viewTypeOptions } from '../../constants/viewMapFilterOptions';

const VALID_AUDIENCES = viewAudienceOptions.map((o) => o.value);
const VALID_VIEW_TYPES = viewTypeOptions.map((o) => o.value);

describe('viewCatalogSections', () => {
  it('includes the admin proposal detail/edit view with its recommended reference', () => {
    const panelViews = viewCatalogSections.find((section) => section.id === 'admin-panel').views;
    const proposalDetailView = panelViews.find((view) => view.url === '/panel/proposals/:id/edit');

    expect(proposalDetailView).toMatchObject({
      label: 'Editar / detalle de propuesta',
      file: 'frontend/pages/panel/proposals/[id]/edit.vue',
      reference: 'vista de edicion/detalle de propuesta del panel',
    });
  });

  it('counts every view in the catalog', () => {
    const manualCount = viewCatalogSections.reduce((count, section) => count + section.views.length, 0);

    expect(countCatalogViews()).toBe(manualCount);
    expect(countCatalogViews()).toBeGreaterThan(0);
  });

  it('every view has a valid audience field', () => {
    for (const section of viewCatalogSections) {
      for (const view of section.views) {
        expect(VALID_AUDIENCES).toContain(view.audience);
      }
    }
  });

  it('every view has a valid viewType field', () => {
    for (const section of viewCatalogSections) {
      for (const view of section.views) {
        expect(VALID_VIEW_TYPES).toContain(view.viewType);
      }
    }
  });

  it('every view has a non-empty curated group (sub-module)', () => {
    for (const section of viewCatalogSections) {
      for (const view of section.views) {
        expect(typeof view.group).toBe('string');
        expect(view.group.trim().length).toBeGreaterThan(0);
      }
    }
  });
});

describe('groupSectionViews', () => {
  it('groups views by their group field preserving catalog order', () => {
    const section = {
      views: [
        { label: 'A', group: 'Uno' },
        { label: 'B', group: 'Dos' },
        { label: 'C', group: 'Uno' },
      ],
    };

    const groups = groupSectionViews(section);

    expect(groups.map((g) => g.group)).toEqual(['Uno', 'Dos']);
    expect(groups[0].views.map((v) => v.label)).toEqual(['A', 'C']);
    expect(groups[1].views.map((v) => v.label)).toEqual(['B']);
  });

  it('falls back to General when a view has no group', () => {
    const groups = groupSectionViews({ views: [{ label: 'X' }] });

    expect(groups).toEqual([{ group: 'General', views: [{ label: 'X' }] }]);
  });
});

describe('isOpenableViewUrl', () => {
  it('accepts static URLs and rejects parameterized ones', () => {
    expect(isOpenableViewUrl('/panel/blog')).toBe(true);
    expect(isOpenableViewUrl('/')).toBe(true);
    expect(isOpenableViewUrl('/blog/:slug')).toBe(false);
    expect(isOpenableViewUrl('/platform/projects/:id/board')).toBe(false);
  });
});

describe('getViewCopyReference', () => {
  it('formats as [Section] Label — URL', () => {
    const view = { label: 'Dashboard del panel', url: '/panel' };

    const result = getViewCopyReference('Panel administrativo', view);

    expect(result).toBe('[Panel administrativo] Dashboard del panel \u2014 /panel');
  });
});

describe('proposalViewReferenceGuide', () => {
  it('distinguishes panel proposal views from public proposal views', () => {
    expect(proposalViewReferenceGuide).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          recommendedName: 'vista de edicion/detalle de propuesta del panel',
          url: '/panel/proposals/:id/edit',
        }),
        expect.objectContaining({
          recommendedName: 'vista publica de propuesta',
          url: '/proposal/:uuid',
        }),
      ]),
    );
  });
});
