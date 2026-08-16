import { capitalizeFirst, conjunction, joinEs } from '~/utils/spanishList';

describe('conjunction', () => {
  // La regla no es cosmética acá: `language` se etiqueta "idioma", así que la
  // lista de campos sin guardar diría "cliente y idioma" sin ella.
  it('turns y into e before a word starting with i', () => {
    expect(conjunction('idioma')).toBe('e');
    expect(conjunction('impuesto')).toBe('e');
  });

  it('turns y into e before a silent h followed by i', () => {
    expect(conjunction('historia')).toBe('e');
  });

  it('keeps y before the hie and hia diphthongs', () => {
    expect(conjunction('hielo')).toBe('y');
    expect(conjunction('hiato')).toBe('y');
  });

  it('keeps y before any other word', () => {
    expect(conjunction('proyecto')).toBe('y');
    expect(conjunction('cliente')).toBe('y');
  });

  it('ignores case and accents when deciding', () => {
    expect(conjunction('Índice')).toBe('e');
    expect(conjunction('IDIOMA')).toBe('e');
  });

  it('falls back to y for empty input', () => {
    expect(conjunction('')).toBe('y');
    expect(conjunction(null)).toBe('y');
  });
});

describe('joinEs', () => {
  it('returns an empty string for no items', () => {
    expect(joinEs([])).toBe('');
    expect(joinEs(null)).toBe('');
  });

  it('returns the single item untouched', () => {
    expect(joinEs(['cliente'])).toBe('cliente');
  });

  it('joins two items with the conjunction', () => {
    expect(joinEs(['cliente', 'proyecto'])).toBe('cliente y proyecto');
  });

  it('separates the leading items with commas', () => {
    expect(joinEs(['título', 'cliente', 'proyecto'])).toBe('título, cliente y proyecto');
  });

  it('applies the e rule to the last item of the list', () => {
    expect(joinEs(['cliente', 'idioma'])).toBe('cliente e idioma');
    expect(joinEs(['título', 'cliente', 'idioma'])).toBe('título, cliente e idioma');
  });

  it('drops empty entries instead of printing stray separators', () => {
    expect(joinEs(['cliente', '', null, 'proyecto'])).toBe('cliente y proyecto');
  });
});

describe('capitalizeFirst', () => {
  it('raises only the first letter, leaving the rest alone', () => {
    expect(capitalizeFirst('cliente y proyecto')).toBe('Cliente y proyecto');
  });

  it('returns an empty string unchanged', () => {
    expect(capitalizeFirst('')).toBe('');
  });
});
