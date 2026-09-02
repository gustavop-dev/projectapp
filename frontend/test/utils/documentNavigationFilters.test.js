import {
  contextualFolderFilters,
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

  it('keeps a selected project inside one of its folders', () => {
    expect(contextualFolderFilters({
      folderId: 17,
      folder: { id: 17, project: 8, client: 36 },
      mode: 'project',
      selection: 8,
    })).toEqual({
      folder: 17,
      project: 8,
      client: null,
    });
  });

  it('keeps a selected client inside one of its folders', () => {
    expect(contextualFolderFilters({
      folderId: 17,
      folder: { id: 17, project: 8, client: 36 },
      mode: 'client',
      selection: 36,
    })).toEqual({
      folder: 17,
      project: null,
      client: 36,
    });
  });

  it('keeps a selected entity when returning to its navigation root', () => {
    expect(contextualFolderFilters({
      folderId: 'root',
      mode: 'project',
      selection: 8,
    })).toEqual({
      folder: 'root',
      project: 8,
      client: null,
    });
  });

  it('clears entity axes for an unrelated folder', () => {
    expect(contextualFolderFilters({
      folderId: 17,
      folder: { id: 17, project: 9, client: 40 },
      mode: 'project',
      selection: 8,
    })).toEqual({
      folder: 17,
      project: null,
      client: null,
    });
  });
});
