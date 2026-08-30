import {
  manualFolderFilters,
  navigationEntityFilters,
} from '../../utils/documentNavigationFilters';

describe('document navigation filters', () => {
  it('selects a project while clearing the client axis', () => {
    expect(navigationEntityFilters('project', 8)).toEqual({
      folder: 'root',
      project: 8,
      client: null,
    });
  });

  it('selects a client while clearing the project axis', () => {
    expect(navigationEntityFilters('client', 36)).toEqual({
      folder: 'root',
      project: null,
      client: 36,
    });
  });

  it('preserves the archived root when an entity axis is cleared', () => {
    expect(navigationEntityFilters('project', 'all', 'archived')).toEqual({
      folder: 'root',
      project: null,
      client: null,
    });
  });

  it('clears both entity axes when a manual folder is selected', () => {
    expect(manualFolderFilters(7)).toEqual({
      folder: 7,
      project: null,
      client: null,
    });
  });
});
