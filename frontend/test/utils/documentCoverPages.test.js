import { describeIncludedPages, includedPages } from '~/utils/documentCoverPages';

describe('documentCoverPages — qué páginas trae el PDF', () => {
  it('lists every page in the order the PDF renders them', () => {
    expect(includedPages({
      include_portada: true,
      include_subportada: true,
      include_contraportada: true,
    })).toEqual(['portada', 'subportada', 'contenido', 'contraportada']);
  });

  it('drops the page whose checkbox is off', () => {
    expect(includedPages({
      include_portada: true,
      include_subportada: false,
      include_contraportada: true,
    })).toEqual(['portada', 'contenido', 'contraportada']);
  });

  it('keeps the content when the three are unchecked — es lo que se descarga', () => {
    expect(includedPages({
      include_portada: false,
      include_subportada: false,
      include_contraportada: false,
    })).toEqual(['contenido']);
  });

  it('treats a missing flag as unchecked instead of assuming the default', () => {
    expect(includedPages({})).toEqual(['contenido']);
  });

  it('reads as one line under the checkboxes', () => {
    expect(describeIncludedPages({
      include_portada: true,
      include_subportada: false,
      include_contraportada: true,
    })).toBe('portada · contenido · contraportada');
  });
});
