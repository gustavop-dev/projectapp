/**
 * Tests for utils/archiveScope.js.
 *
 * `isRootInScope` es la regla que define «la cima del listado», y de ella
 * depende que archivar una carpeta la muestre como contenedor en vez de dejar
 * sus documentos como hermanos.
 */

import {
  DEFAULT_SCOPE, isRootInScope, matchesScope, normalizeScope,
} from '../../utils/archiveScope';

const active = { id: 1, is_archived: false };
const archived = { id: 2, is_archived: true };

describe('normalizeScope', () => {
  it('keeps the three known scopes', () => {
    expect(normalizeScope('all')).toBe('all');
    expect(normalizeScope('active')).toBe('active');
    expect(normalizeScope('archived')).toBe('archived');
  });

  it('falls back to the resting state for anything else', () => {
    expect(normalizeScope('banana')).toBe(DEFAULT_SCOPE);
    expect(normalizeScope(undefined)).toBe('active');
  });
});

describe('matchesScope', () => {
  it('accepts both states under all', () => {
    expect(matchesScope(active, 'all')).toBe(true);
    expect(matchesScope(archived, 'all')).toBe(true);
  });

  it('separates the two states otherwise', () => {
    expect(matchesScope(active, 'active')).toBe(true);
    expect(matchesScope(archived, 'active')).toBe(false);
    expect(matchesScope(archived, 'archived')).toBe(true);
    expect(matchesScope(active, 'archived')).toBe(false);
  });

  it('treats a missing entity as no match', () => {
    expect(matchesScope(null, 'all')).toBe(false);
  });
});

describe('isRootInScope', () => {
  const find = (id) => [active, archived].find((f) => f.id === id) || null;

  it('puts an item without a container at the top', () => {
    expect(isRootInScope(null, find, 'archived')).toBe(true);
  });

  it('puts an item whose container is unknown at the top', () => {
    // Red de seguridad: lo que no se puede ubicar aflora en vez de desaparecer.
    expect(isRootInScope(999, find, 'active')).toBe(true);
  });

  it('puts an item at the top when its container is out of scope', () => {
    // Un documento archivado en una carpeta ACTIVA: la carpeta no se lista en
    // el archivo, así que el documento tiene que verse en la cima.
    expect(isRootInScope(active.id, find, 'archived')).toBe(true);
  });

  it('keeps an item nested when its container is listed alongside it', () => {
    expect(isRootInScope(archived.id, find, 'archived')).toBe(false);
    expect(isRootInScope(active.id, find, 'active')).toBe(false);
  });

  it('nests under any container in the mixed scope', () => {
    expect(isRootInScope(archived.id, find, 'all')).toBe(false);
    expect(isRootInScope(active.id, find, 'all')).toBe(false);
  });
});
