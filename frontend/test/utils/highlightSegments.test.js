import { highlightSegments } from '../../utils/highlightSegments';

describe('highlightSegments', () => {
  it('returns a single non-hit segment when the query is empty', () => {
    expect(highlightSegments('Kore - Inicio', '')).toEqual([
      { text: 'Kore - Inicio', hit: false },
    ]);
  });

  it('marks case-insensitive occurrences', () => {
    const segments = highlightSegments('Kore y kore', 'kore');
    expect(segments).toEqual([
      { text: 'Kore', hit: true },
      { text: ' y ', hit: false },
      { text: 'kore', hit: true },
    ]);
  });

  it('escapes regex special characters in the query', () => {
    const segments = highlightSegments('Pago (40%) inicial', '(40%)');
    expect(segments).toEqual([
      { text: 'Pago ', hit: false },
      { text: '(40%)', hit: true },
      { text: ' inicial', hit: false },
    ]);
  });

  it('handles non-string input and no matches', () => {
    expect(highlightSegments(1400000, '99')).toEqual([
      { text: '1400000', hit: false },
    ]);
    expect(highlightSegments('', 'x')).toEqual([{ text: '', hit: false }]);
  });
});
