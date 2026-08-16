/**
 * Tests for utils/folderRollup.js.
 *
 * El álgebra del subárbol en aislamiento, sin Pinia. Lo que se fija acá es la
 * separación de los dos ejes: por qué carpetas se puede bajar (`membershipScope`)
 * y qué documentos se suman al bajar (`countingScope`). Confundirlos es lo que
 * hace que un documento se cuente dos veces o ninguna.
 */

import { buildFolderRollup, directRollupRecord } from '../../utils/folderRollup';

/** Carpeta con los seis contadores absolutos, como los sirve el backend. */
function folder(id, parent, { docs = 0, subs = 0, archivedDocs = 0, archivedSubs = 0, archived = false } = {}) {
  return {
    id,
    parent,
    is_archived: archived,
    document_count: archived ? archivedDocs : docs,
    children_count: archived ? archivedSubs : subs,
    active_document_count: docs,
    active_children_count: subs,
    archived_document_count: archivedDocs,
    archived_children_count: archivedSubs,
  };
}

const ACTIVE = { countingScope: 'active', membershipScope: 'active' };

describe('buildFolderRollup', () => {
  it('adds up documents from every level, not just the direct children', () => {
    // La forma de «Familia» en producción: la raíz no tiene ni un documento
    // propio y guarda 12 repartidos dos niveles más abajo.
    const folders = [
      folder(1, null, { subs: 1 }),
      folder(2, 1, { docs: 1, subs: 2 }),
      folder(3, 2, { docs: 6 }),
      folder(4, 2, { docs: 5 }),
    ];

    const rollup = buildFolderRollup(folders, ACTIVE);

    expect(rollup.get(1).docs).toBe(12);
    expect(rollup.get(2).docs).toBe(12);
    expect(rollup.get(3).docs).toBe(6);
  });

  it('keeps what is its own apart from what it inherits', () => {
    const folders = [folder(1, null, { docs: 1, subs: 1 }), folder(2, 1, { docs: 11 })];

    expect(buildFolderRollup(folders, ACTIVE).get(1)).toEqual({
      docs: 12, subs: 1, ownDocs: 1, ownSubs: 1,
    });
  });

  it('counts every subfolder of the branch, at any depth', () => {
    const folders = [
      folder(1, null, { subs: 1 }),
      folder(2, 1, { subs: 2 }),
      folder(3, 2),
      folder(4, 2),
    ];

    expect(buildFolderRollup(folders, ACTIVE).get(1).subs).toBe(3);
  });

  it('does not bleed between sibling branches', () => {
    const folders = [
      folder(1, null, { subs: 1 }),
      folder(2, 1, { docs: 7 }),
      folder(8, null, { subs: 1 }),
      folder(9, 8, { docs: 3 }),
    ];

    const rollup = buildFolderRollup(folders, ACTIVE);

    expect(rollup.get(1).docs).toBe(7);
    expect(rollup.get(8).docs).toBe(3);
  });

  it('stops at an archived folder so a promoted branch is not counted twice', () => {
    // A(activa) → B(archivada) → C(activa). El panel PROMUEVE a C a fila de la
    // cima, porque su contenedor no está en el scope activo. Si el subárbol de
    // A bajara por B, los 5 documentos de C saldrían en las dos filas y la suma
    // pasaría del total de «Todos».
    const folders = [
      folder(1, null, { docs: 2 }),
      folder(2, 1, { archived: true }),
      folder(3, 2, { docs: 5 }),
    ];

    const rollup = buildFolderRollup(folders, ACTIVE);

    expect(rollup.get(1).docs).toBe(2);
    expect(rollup.get(3).docs).toBe(5);
    expect(rollup.has(2)).toBe(false);
  });

  it('walks through active folders to reach the archived content they hold', () => {
    // El caso simétrico, y el que un recorrido ingenuo por carpetas del scope
    // contado se comería: una carpeta ACTIVA puede guardar archivados, y sin
    // bajar por ella no quedan en ninguna fila del modo archivado.
    const folders = [
      folder(1, null, { subs: 1 }),
      folder(2, 1, { archivedDocs: 4, archived: true }),
    ];

    const rollup = buildFolderRollup(folders, {
      countingScope: 'archived', membershipScope: 'all',
    });

    expect(rollup.get(1).docs).toBe(4);
  });

  it('gives the same tree a different answer per scope', () => {
    const folders = [
      folder(1, null, { docs: 1, subs: 1 }),
      folder(2, 1, { docs: 3, archivedDocs: 4 }),
    ];

    expect(buildFolderRollup(folders, ACTIVE).get(1).docs).toBe(4);
    expect(buildFolderRollup(folders, {
      countingScope: 'archived', membershipScope: 'all',
    }).get(1).docs).toBe(4);
    expect(buildFolderRollup(folders, {
      countingScope: 'all', membershipScope: 'all',
    }).get(1).docs).toBe(8);
  });

  it('leaves the roots of a scope partitioning every document exactly once', () => {
    // La identidad del requisito: sumar las filas de la cima da el total.
    const folders = [
      folder(1, null, { docs: 1, subs: 1 }),
      folder(2, 1, { docs: 6 }),
      folder(8, null, { docs: 4 }),
    ];

    const rollup = buildFolderRollup(folders, ACTIVE);
    const roots = folders.filter((f) => f.parent == null);
    const total = roots.reduce((sum, f) => sum + rollup.get(f.id).docs, 0);

    expect(total).toBe(11);
  });

  it('finishes on a cyclic parent chain instead of hanging the panel', () => {
    // Imposible por la API (`validate_parent` lo rechaza), pero un dato torcido
    // no puede colgar el panel: la insignia sale corta, no infinita.
    const folders = [folder(1, 2, { docs: 2 }), folder(2, 1, { docs: 3 })];

    const rollup = buildFolderRollup(folders, ACTIVE);

    expect(rollup.get(1).docs).toBeGreaterThanOrEqual(2);
    expect(Number.isFinite(rollup.get(2).docs)).toBe(true);
  });

  it('treats a self-parented folder as a root instead of dropping it', () => {
    const rollup = buildFolderRollup([folder(1, 1, { docs: 3 })], ACTIVE);

    expect(rollup.get(1).docs).toBe(3);
  });

  it('rolls up a legacy payload that only carries the relative counters', () => {
    // Fixtures y respuestas cacheadas anteriores a los contadores absolutos.
    const folders = [
      { id: 1, parent: null, document_count: 1, children_count: 1, is_archived: false },
      { id: 2, parent: 1, document_count: 6, children_count: 0, is_archived: false },
    ];

    expect(buildFolderRollup(folders, ACTIVE).get(1).docs).toBe(7);
  });

  it('still answers for a folder whose parent is not in the list', () => {
    const rollup = buildFolderRollup([folder(5, 99, { docs: 3 })], ACTIVE);

    expect(rollup.get(5).docs).toBe(3);
  });

  it('returns an empty map for an empty or missing list', () => {
    expect(buildFolderRollup([], ACTIVE).size).toBe(0);
    expect(buildFolderRollup(undefined, ACTIVE).size).toBe(0);
  });
});

describe('directRollupRecord', () => {
  it('reports the folder alone, for rows outside the loaded tree', () => {
    expect(directRollupRecord(folder(1, null, { docs: 3, subs: 2 }))).toEqual({
      docs: 3, subs: 2, ownDocs: 3, ownSubs: 2,
    });
  });
});
