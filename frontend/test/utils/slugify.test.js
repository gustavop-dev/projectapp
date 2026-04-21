import { toSlug } from '../../utils/slugify';

describe('toSlug', () => {
  it('lowercases and removes diacritics from a Spanish name', () => {
    expect(toSlug('María López')).toBe('maria-lopez');
  });

  it('collapses multiple spaces and special characters to a single dash', () => {
    expect(toSlug('Empresa   S.A.S.')).toBe('empresa-s-a-s');
  });

  it('strips leading and trailing dashes', () => {
    expect(toSlug('  --Hello--  ')).toBe('hello');
  });

  it('returns the fallback when the input normalizes to empty', () => {
    expect(toSlug('', { fallback: 'propuesta' })).toBe('propuesta');
    expect(toSlug('!!!', { fallback: 'propuesta' })).toBe('propuesta');
  });

  it('returns empty string when input is empty and no fallback is given', () => {
    expect(toSlug('')).toBe('');
  });

  it('handles null and undefined gracefully', () => {
    expect(toSlug(null)).toBe('');
    expect(toSlug(undefined)).toBe('');
  });

  it('truncates to the specified maxLength', () => {
    const long = 'a'.repeat(200);
    expect(toSlug(long, { maxLength: 50 })).toHaveLength(50);
  });

  it('preserves numbers in the slug', () => {
    expect(toSlug('Cliente 2026')).toBe('cliente-2026');
  });
});
