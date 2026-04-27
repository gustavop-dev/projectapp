import { hexToRgb, luminance, toRgbString } from '../../utils/colorUtils';

describe('hexToRgb', () => {
  it('parses a 7-char hex with leading #', () => {
    expect(hexToRgb('#FFFFFF')).toEqual({ r: 255, g: 255, b: 255 });
    expect(hexToRgb('#000000')).toEqual({ r: 0, g: 0, b: 0 });
  });

  it('parses a hex without leading #', () => {
    expect(hexToRgb('047857')).toEqual({ r: 4, g: 120, b: 87 });
  });

  it('handles lowercase and uppercase', () => {
    expect(hexToRgb('#abcdef')).toEqual({ r: 171, g: 205, b: 239 });
    expect(hexToRgb('#ABCDEF')).toEqual({ r: 171, g: 205, b: 239 });
  });
});

describe('luminance', () => {
  it('returns 0 for black and 255 for white', () => {
    expect(luminance('#000000')).toBe(0);
    expect(Math.round(luminance('#FFFFFF'))).toBe(255);
  });

  it('crosses the 186 light/dark threshold predictably', () => {
    expect(luminance('#FFFFFF') > 186).toBe(true);
    expect(luminance('#000000') < 186).toBe(true);
    expect(luminance('#047857') < 186).toBe(true);
  });
});

describe('toRgbString', () => {
  it('formats hex as space-free comma-separated RGB', () => {
    expect(toRgbString('#FFFFFF')).toBe('255, 255, 255');
    expect(toRgbString('#047857')).toBe('4, 120, 87');
  });
});
