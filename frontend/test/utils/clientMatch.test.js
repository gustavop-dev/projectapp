import { nameParts, normalizeName, suggestClient } from '../../utils/clientMatch';

const CLIENTS = [
  { id: 1, name: 'Daniel Felipe Corredor', company: 'MIMITTOS' },
  { id: 2, name: 'Germán Franco', company: '' },
  { id: 3, name: 'Néstor y Milena', company: '' },
  { id: 4, name: 'Aarón Sepúlveda', company: 'Reno Partes' },
];

describe('normalizeName', () => {
  it('drops accents, case and punctuation', () => {
    expect(normalizeName('Germán Franco')).toBe('german franco');
    expect(normalizeName('G&M Consultores S.A.S.')).toBe('g&m consultores s a s');
  });

  it('survives empty input', () => {
    expect(normalizeName(null)).toBe('');
  });
});

describe('nameParts', () => {
  it('splits the "Persona - Marca" convention keeping the whole string', () => {
    expect(nameParts('German - Kore')).toEqual([
      'german kore', 'german', 'kore',
    ]);
  });

  it('handles two people on the left', () => {
    expect(nameParts('Jimmy & Daniel - Mimittos')).toContain('jimmy & daniel');
    expect(nameParts('Jimmy & Daniel - Mimittos')).toContain('mimittos');
  });
});

describe('suggestClient', () => {
  it('pairs the brand half with the client company, ignoring case', () => {
    expect(suggestClient('Jimmy & Daniel - Mimittos', CLIENTS).id).toBe(1);
  });

  it('pairs the person half with the client name, ignoring accents', () => {
    expect(suggestClient('German - Kore', CLIENTS).id).toBe(2);
    expect(suggestClient('Nestor - Xpandia', CLIENTS).id).toBe(3);
  });

  it('returns null when nothing resembles a registered client', () => {
    // Those clients simply do not exist yet — the operator creates them.
    // Paired with a hit so the null is a real verdict, not a dead function.
    expect(suggestClient('Katerin Ruiz - Senses Candles', CLIENTS)).toBeNull();
    expect(suggestClient('Wilson Garcia - G&M', CLIENTS)).toBeNull();
    expect(suggestClient('Aarón - Reno Partes', CLIENTS).id).toBe(4);
  });

  it('does not guess from very short fragments', () => {
    expect(suggestClient('A - B', CLIENTS)).toBeNull();
    // Four characters is the floor, so this one does resolve.
    expect(suggestClient('Kore - Reno', CLIENTS).id).toBe(4);
  });

  it('returns null without a name or without clients', () => {
    expect(suggestClient('', CLIENTS)).toBeNull();
    expect(suggestClient('German - Kore', [])).toBeNull();
    expect(suggestClient('German - Kore', CLIENTS).id).toBe(2);
  });
});
