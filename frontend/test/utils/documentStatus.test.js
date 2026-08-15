/**
 * Tests for utils/documentStatus.js.
 *
 * `folderRowSummary` alimenta el inventario del tooltip de eliminar, así que
 * tiene que poder sumar los dos estados sin duplicar nada.
 */

import {
  archivedAgeLabel, folderRowSummary, scopedDocumentCount,
} from '../../utils/documentStatus';

const mixedFolder = {
  document_count: 2,
  children_count: 1,
  active_document_count: 2,
  active_children_count: 1,
  archived_document_count: 3,
  archived_children_count: 2,
};

describe('scopedDocumentCount', () => {
  it('counts the active documents by default', () => {
    expect(scopedDocumentCount(mixedFolder)).toBe(2);
  });

  it('counts the archived documents in the archived scope', () => {
    // Es el número de la fila del panel lateral: con el modo encendido tiene
    // que contar archivados, o el contador contradice al listado.
    expect(scopedDocumentCount(mixedFolder, 'archived')).toBe(3);
  });

  it('adds both states in the mixed scope', () => {
    expect(scopedDocumentCount(mixedFolder, 'all')).toBe(5);
  });

  it('ignores subfolders — the row counts documents', () => {
    expect(scopedDocumentCount({ ...mixedFolder, archived_children_count: 9 }, 'archived'))
      .toBe(3);
  });

  it('survives a missing folder', () => {
    expect(scopedDocumentCount(null, 'archived')).toBe(0);
  });

  it('falls back to the legacy counter on either side', () => {
    // Payloads viejos (respuestas cacheadas, fixtures) sólo traen el relativo,
    // que en una carpeta archivada YA es el conteo archivado.
    const legacyArchived = { document_count: 4, is_archived: true };
    expect(scopedDocumentCount(legacyArchived, 'archived')).toBe(4);
    expect(scopedDocumentCount(legacyArchived)).toBe(0);
    expect(scopedDocumentCount({ document_count: 4, is_archived: false })).toBe(4);
  });
});

describe('folderRowSummary', () => {
  it('counts the active content by default', () => {
    expect(folderRowSummary(mixedFolder)).toBe('2 documentos · 1 subcarpeta');
  });

  it('counts the archived content in the archived scope', () => {
    expect(folderRowSummary(mixedFolder, 'archived')).toBe('3 documentos · 2 subcarpetas');
  });

  it('adds both states in the mixed scope', () => {
    expect(folderRowSummary(mixedFolder, 'all')).toBe('5 documentos · 3 subcarpetas');
  });

  it('does not double count an archived folder', () => {
    // En una carpeta archivada `document_count` YA es el conteo archivado:
    // sumarlo con `archived_document_count` daría el doble.
    const archivedFolder = {
      is_archived: true,
      document_count: 4,
      children_count: 0,
      active_document_count: 0,
      active_children_count: 0,
      archived_document_count: 4,
      archived_children_count: 0,
    };

    expect(folderRowSummary(archivedFolder, 'all')).toBe('4 documentos');
  });

  it('falls back to the legacy counters when the absolute ones are missing', () => {
    expect(folderRowSummary({ document_count: 1, children_count: 0 })).toBe('1 documento');
  });

  it('reports an empty folder', () => {
    expect(folderRowSummary({}, 'all')).toBe('Vacía');
  });
});

describe('archivedAgeLabel', () => {
  it('returns nothing without a date', () => {
    expect(archivedAgeLabel(null)).toBe('');
    expect(archivedAgeLabel('not a date')).toBe('');
  });

  it('names today and yesterday', () => {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 86400000);

    expect(archivedAgeLabel(now.toISOString())).toBe('hoy');
    expect(archivedAgeLabel(yesterday.toISOString())).toBe('ayer');
  });

  it('counts days, then months, then years', () => {
    const daysAgo = (n) => new Date(Date.now() - n * 86400000).toISOString();

    expect(archivedAgeLabel(daysAgo(5))).toBe('hace 5 días');
    expect(archivedAgeLabel(daysAgo(60))).toBe('hace 2 meses');
    expect(archivedAgeLabel(daysAgo(400))).toBe('hace 1 año');
  });
});
