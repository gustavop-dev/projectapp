/**
 * Tests for the selectArrowStyle utility.
 *
 * Covers: export exists, contains expected CSS declarations.
 */
import { SELECT_ARROW_STYLE } from '../../utils/selectArrowStyle';

describe('SELECT_ARROW_STYLE', () => {
  it('exports a non-empty string', () => {
    expect(typeof SELECT_ARROW_STYLE).toBe('string');
    expect(SELECT_ARROW_STYLE.length).toBeGreaterThan(0);
  });

  it('contains background-image CSS declaration', () => {
    expect(SELECT_ARROW_STYLE).toContain('background-image:');
    expect(SELECT_ARROW_STYLE).toContain('background-position:');
    expect(SELECT_ARROW_STYLE).toContain('background-repeat:');
  });
});
