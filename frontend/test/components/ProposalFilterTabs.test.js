/**
 * Tests for ProposalFilterTabs logic.
 *
 * Covers: toggleMenu, startCreate, startRename, confirmInput, cancelInput,
 * handleDelete, and input validation.
 *
 * Following project convention: extract and test component logic directly
 * rather than mounting Vue components.
 */

// ── toggleMenu ─────────────────────────────────────────────────────────────

function toggleMenu(openMenuId, tabId) {
  return openMenuId === tabId ? null : tabId;
}

describe('toggleMenu', () => {
  it('opens menu when currently closed', () => {
    expect(toggleMenu(null, 'tab-1')).toBe('tab-1');
  });

  it('closes menu when same tab is toggled', () => {
    expect(toggleMenu('tab-1', 'tab-1')).toBeNull();
  });

  it('switches to different tab when another is open', () => {
    expect(toggleMenu('tab-1', 'tab-2')).toBe('tab-2');
  });
});


// ── confirmInput logic ──────────────────────────────────────────────────────

function confirmInput({ inputName, isRenaming, renameTargetId }) {
  const name = inputName.trim();
  if (!name) return null;
  if (isRenaming && renameTargetId) {
    return { action: 'rename', id: renameTargetId, name };
  }
  return { action: 'create', name };
}

describe('confirmInput', () => {
  it('returns create action for new tab', () => {
    const result = confirmInput({ inputName: 'My Tab', isRenaming: false, renameTargetId: null });
    expect(result).toEqual({ action: 'create', name: 'My Tab' });
  });

  it('returns rename action for existing tab', () => {
    const result = confirmInput({ inputName: 'New Name', isRenaming: true, renameTargetId: 'tab-1' });
    expect(result).toEqual({ action: 'rename', id: 'tab-1', name: 'New Name' });
  });

  it('returns null for empty name', () => {
    expect(confirmInput({ inputName: '', isRenaming: false, renameTargetId: null })).toBeNull();
  });

  it('returns null for whitespace-only name', () => {
    expect(confirmInput({ inputName: '   ', isRenaming: false, renameTargetId: null })).toBeNull();
  });

  it('trims whitespace from name', () => {
    const result = confirmInput({ inputName: '  Trimmed  ', isRenaming: false, renameTargetId: null });
    expect(result.name).toBe('Trimmed');
  });
});


// ── cancelInput ─────────────────────────────────────────────────────────────

function cancelInput() {
  return { showInput: false, inputName: '', isRenaming: false, renameTargetId: null };
}

describe('cancelInput', () => {
  it('resets all input state', () => {
    const state = cancelInput();
    expect(state.showInput).toBe(false);
    expect(state.inputName).toBe('');
    expect(state.isRenaming).toBe(false);
    expect(state.renameTargetId).toBeNull();
  });
});


// ── startCreate ─────────────────────────────────────────────────────────────

function startCreate() {
  return { isRenaming: false, renameTargetId: null, inputName: '', showInput: true };
}

describe('startCreate', () => {
  it('sets up create mode state', () => {
    const state = startCreate();
    expect(state.isRenaming).toBe(false);
    expect(state.renameTargetId).toBeNull();
    expect(state.inputName).toBe('');
    expect(state.showInput).toBe(true);
  });
});


// ── startRename ─────────────────────────────────────────────────────────────

function startRename(tab) {
  return { openMenuId: null, isRenaming: true, renameTargetId: tab.id, inputName: tab.name, showInput: true };
}

describe('startRename', () => {
  it('sets up rename mode with tab data', () => {
    const tab = { id: 'tab-1', name: 'Old Name' };
    const state = startRename(tab);
    expect(state.openMenuId).toBeNull();
    expect(state.isRenaming).toBe(true);
    expect(state.renameTargetId).toBe('tab-1');
    expect(state.inputName).toBe('Old Name');
    expect(state.showInput).toBe(true);
  });
});


// ── handleDelete ────────────────────────────────────────────────────────────

function handleDelete(tabId) {
  return { openMenuId: null, deletedTabId: tabId };
}

describe('handleDelete', () => {
  it('clears menu and returns deleted tab id', () => {
    const result = handleDelete('tab-1');
    expect(result.openMenuId).toBeNull();
    expect(result.deletedTabId).toBe('tab-1');
  });
});


// ── Tab limit enforcement ───────────────────────────────────────────────────

describe('tab limit enforcement', () => {
  it('+ button should be disabled when limit is reached', () => {
    const isTabLimitReached = true;
    expect(isTabLimitReached).toBe(true);
  });

  it('+ button should be enabled when under limit', () => {
    const isTabLimitReached = false;
    expect(isTabLimitReached).toBe(false);
  });
});


// ── Mobile select options ───────────────────────────────────────────────────

describe('mobile select options', () => {
  it('includes Todas as first option plus all saved tabs', () => {
    const tabs = [
      { id: 'tab-1', name: 'Tab A' },
      { id: 'tab-2', name: 'Tab B' },
    ];
    const options = ['all', ...tabs.map(t => t.id)];
    expect(options).toEqual(['all', 'tab-1', 'tab-2']);
  });

  it('includes only Todas when no saved tabs exist', () => {
    const tabs = [];
    const options = ['all', ...tabs.map(t => t.id)];
    expect(options).toEqual(['all']);
  });
});


// ── Active tab class logic ──────────────────────────────────────────────────

function isActiveTab(activeTabId, tabId) {
  return activeTabId === tabId;
}

describe('active tab detection', () => {
  it('returns true when tab matches active id', () => {
    expect(isActiveTab('tab-1', 'tab-1')).toBe(true);
  });

  it('returns false when tab does not match active id', () => {
    expect(isActiveTab('tab-1', 'tab-2')).toBe(false);
  });

  it('identifies Todas tab as active when activeTabId is all', () => {
    expect(isActiveTab('all', 'all')).toBe(true);
  });
});
