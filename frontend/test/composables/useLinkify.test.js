/**
 * Tests for the useLinkify composable.
 *
 * Covers: full URL linkification, bare domain linkification,
 * already-linked content skipped, non-string input, display formatting,
 * useLinkify composable hook export.
 */
import { linkify, useLinkify } from '../../composables/useLinkify';


describe('linkify — full URLs', () => {
  it('converts a plain https URL to an anchor tag', () => {
    const result = linkify('Visit https://example.com for more info.');
    expect(result).toContain('<a href="https://example.com"');
    expect(result).toContain('target="_blank"');
    expect(result).toContain('rel="noopener noreferrer"');
    expect(result).toContain('class="linkify-link"');
  });

  it('strips www and trailing slash from display text for https URL', () => {
    const result = linkify('Go to https://www.projectapp.co/');
    expect(result).toContain('>projectapp.co<');
  });

  it('includes path in display text when URL has non-root path', () => {
    const result = linkify('See https://example.com/about');
    expect(result).toContain('>example.com/about<');
  });

  it('converts http URL as well as https', () => {
    const result = linkify('Old site: http://old.example.com');
    expect(result).toContain('href="http://old.example.com"');
  });

  it('converts multiple URLs in the same string', () => {
    const result = linkify('First: https://a.com and second: https://b.com');
    expect(result).toContain('href="https://a.com"');
    expect(result).toContain('href="https://b.com"');
  });

  it('handles URL with query params', () => {
    const result = linkify('https://example.com/search?q=test');
    expect(result).toContain('href="https://example.com/search?q=test"');
  });
});


describe('linkify — bare domains', () => {
  it('converts bare .com domain to anchor', () => {
    const result = linkify('Visit projectapp.com for details.');
    expect(result).toContain('href="https://projectapp.com"');
  });

  it('converts bare .co domain', () => {
    const result = linkify('Contact us at projectapp.co');
    expect(result).toContain('href="https://projectapp.co"');
  });

  it('strips www from display text of bare domain', () => {
    const result = linkify('See www.example.com today.');
    expect(result).toContain('>example.com<');
  });

  it('does not linkify a word without valid TLD', () => {
    const result = linkify('This is an example word.');
    expect(result).not.toContain('<a ');
  });

  it('does not double-linkify a URL already processed', () => {
    const result = linkify('https://example.com');
    const count = (result.match(/<a /g) || []).length;
    expect(count).toBe(1);
  });
});


describe('linkify — edge cases', () => {
  it('returns empty string for empty input', () => {
    expect(linkify('')).toBe('');
  });

  it('returns empty string for null input', () => {
    expect(linkify(null)).toBe('');
  });

  it('returns empty string for undefined input', () => {
    expect(linkify(undefined)).toBe('');
  });

  it('returns empty string for numeric input', () => {
    expect(linkify(123)).toBe('');
  });

  it('returns plain text unchanged when no URLs present', () => {
    const text = 'Hello, this has no links at all.';
    expect(linkify(text)).toBe(text);
  });

  it('does not linkify email addresses', () => {
    const result = linkify('Send to team@projectapp.co please.');
    expect(result).not.toContain('<a ');
  });
});


describe('useLinkify composable', () => {
  it('exposes linkify function', () => {
    const { linkify: fn } = useLinkify();
    expect(typeof fn).toBe('function');
  });

  it('linkify from useLinkify works correctly', () => {
    const { linkify: fn } = useLinkify();
    const result = fn('https://projectapp.co');
    expect(result).toContain('href="https://projectapp.co"');
  });
});
