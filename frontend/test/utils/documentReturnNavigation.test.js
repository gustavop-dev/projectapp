import {
  documentOriginWithFocus,
  documentReturnLabel,
  resolveDocumentReturn,
} from '../../utils/documentReturnNavigation';

function fakeRouter() {
  return {
    resolve(target) {
      if (typeof target === 'object') {
        const query = new URLSearchParams(target.query || {}).toString();
        return {
          path: target.path,
          query: target.query || {},
          fullPath: `${target.path}${query ? `?${query}` : ''}`,
        };
      }
      const url = new URL(target, 'https://projectapp.test');
      return {
        path: url.pathname,
        query: Object.fromEntries(url.searchParams.entries()),
        fullPath: `${url.pathname}${url.search}${url.hash}`,
      };
    },
  };
}

describe('resolveDocumentReturn', () => {
  it('accepts a localized Documents list origin', () => {
    const result = resolveDocumentReturn(
      '/es/panel/documents?folder=8&q=Acme&page=2',
      fakeRouter(),
      '/es/panel/documents',
    );

    expect(result).toEqual({
      target: '/es/panel/documents?folder=8&q=Acme&page=2',
      query: { folder: '8', q: 'Acme', page: '2' },
      hasOrigin: true,
    });
  });

  it('rejects an external origin', () => {
    const result = resolveDocumentReturn(
      'https://evil.example/panel/documents', fakeRouter(), '/es/panel/documents',
    );

    expect(result).toEqual({ target: '/es/panel/documents', query: {}, hasOrigin: false });
  });

  it('rejects a protocol-relative origin', () => {
    const result = resolveDocumentReturn(
      '//evil.example/panel/documents', fakeRouter(), '/es/panel/documents',
    );

    expect(result.hasOrigin).toBe(false);
  });

  it('rejects another internal module', () => {
    const result = resolveDocumentReturn(
      '/es/panel/clients?tab=projects', fakeRouter(), '/es/panel/documents',
    );

    expect(result.hasOrigin).toBe(false);
  });
});

describe('documentOriginWithFocus', () => {
  it('preserves the live list query', () => {
    const route = { path: '/es/panel/documents', query: { folder: '8', page: '3' } };

    expect(documentOriginWithFocus(route, fakeRouter(), 42))
      .toBe('/es/panel/documents?folder=8&page=3&focus=42');
  });

  it('replaces a stale focus id', () => {
    const route = { path: '/es/panel/documents', query: { focus: '3' } };

    expect(documentOriginWithFocus(route, fakeRouter(), 9))
      .toBe('/es/panel/documents?focus=9');
  });
});

describe('documentReturnLabel', () => {
  const folderById = (id) => (id === 8 ? { id, name: 'Contratos' } : null);

  it('names a folder origin', () => {
    expect(documentReturnLabel({
      hasOrigin: true, query: { folder: '8' }, folderById,
    })).toBe('Volver a «Contratos»');
  });

  it('names an archived folder origin', () => {
    expect(documentReturnLabel({
      hasOrigin: true, query: { folder: '8', scope: 'archived' }, folderById,
    })).toBe('Volver a «Contratos» (archivados)');
  });

  it('names a search origin', () => {
    expect(documentReturnLabel({
      hasOrigin: true, query: { q: 'Factura agosto' }, folderById,
    })).toBe('Volver a resultados de «Factura agosto»');
  });

  it('names the archive root', () => {
    expect(documentReturnLabel({
      hasOrigin: true, query: { folder: 'root', scope: 'archived' }, folderById,
    })).toBe('Volver a Archivados');
  });

  it('names a filtered root', () => {
    expect(documentReturnLabel({
      hasOrigin: true, query: { tags: '3,8' }, folderById,
    })).toBe('Volver a documentos filtrados');
  });

  it('uses the direct-entry fallback', () => {
    expect(documentReturnLabel({
      hasOrigin: false, query: {}, folderById,
    })).toBe('Volver a Documentos');
  });
});
