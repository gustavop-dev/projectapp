/**
 * Tests for the HTML-escape behavior added to ``linkify`` to prevent XSS
 * in admin-authored proposal copy that is rendered with v-html.
 *
 * The whitelist preserves <b>, <strong>, <i>, <em>, <br> (admin copy
 * historically uses these for emphasis) but escapes everything else.
 */
import { linkify } from '../../composables/useLinkify';

describe('linkify — HTML escape (XSS hardening)', () => {
  it('escapes a <script> injection so it does not execute', () => {
    const result = linkify('Hello <script>alert(1)</script> world');
    expect(result).not.toContain('<script>');
    expect(result).toContain('&lt;script&gt;');
    expect(result).toContain('&lt;/script&gt;');
  });

  it('preserves whitelisted <b> and <strong> tags', () => {
    const result = linkify('Plain <b>bold</b> and <strong>stronger</strong>.');
    expect(result).toContain('<b>bold</b>');
    expect(result).toContain('<strong>stronger</strong>');
  });

  it('preserves whitelisted <i>, <em>, and <br> tags', () => {
    const result = linkify('Line 1<br>Line 2 with <i>italic</i> and <em>em</em>.');
    expect(result).toContain('<br>');
    expect(result).toContain('<i>italic</i>');
    expect(result).toContain('<em>em</em>');
  });

  it('escapes ampersands and quotes so attribute injection is blocked', () => {
    const result = linkify('A & B with " quote');
    expect(result).toContain('&amp;');
    expect(result).toContain('&quot;');
  });

  it('escapes <img> and other non-whitelisted tags', () => {
    const result = linkify('<img src=x onerror=alert(1)>');
    expect(result).not.toContain('<img');
    expect(result).toContain('&lt;img');
  });

  it('still linkifies URLs around escaped content', () => {
    const result = linkify('Visit https://projectapp.co for <b>more</b>.');
    expect(result).toContain('href="https://projectapp.co"');
    expect(result).toContain('<b>more</b>');
  });
});
