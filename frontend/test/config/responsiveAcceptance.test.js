import { PANEL_VIEWPORTS } from '../../config/responsive';
import {
  RESPONSIVE_MODULE_NAMES,
  modulesForChangedFiles,
  responsiveOwnerForView,
} from '../../config/responsiveAcceptance';

describe('responsive acceptance registry', () => {
  it('keeps the five canonical viewport widths', () => {
    expect(Object.values(PANEL_VIEWPORTS).map(({ width }) => width)).toEqual([
      412,
      835,
      1195,
      1440,
      2560,
    ]);
  });

  it('runs only the owning module for a scoped page', () => {
    expect(modulesForChangedFiles(['frontend/pages/panel/mcps/index.vue'])).toEqual(['mcp']);
  });

  it('runs every module for a shared primitive', () => {
    expect(modulesForChangedFiles(['frontend/components/base/BaseModal.vue'])).toEqual(
      RESPONSIVE_MODULE_NAMES,
    );
  });

  it('runs every module for an unregistered UI directory', () => {
    expect(modulesForChangedFiles(['frontend/components/new-area/Widget.vue'])).toEqual(
      RESPONSIVE_MODULE_NAMES,
    );
  });

  it('assigns document editors to canvas', () => {
    expect(responsiveOwnerForView('admin-panel', {
      file: 'frontend/pages/panel/documents/[id]/edit.vue',
      url: '/panel/documents/:id/edit',
      audience: 'admin',
    })).toBe('canvas');
  });
});
