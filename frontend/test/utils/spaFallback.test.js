import { assertValidSpaFallbackHtml } from '../../utils/spaFallback';

describe('assertValidSpaFallbackHtml', () => {
  it('accepts a Nuxt mount document', () => {
    const result = assertValidSpaFallbackHtml(
      '<!DOCTYPE html><html><body><div id="__nuxt"></div></body></html>',
    );

    expect(result).toBeUndefined();
  });

  it('rejects an empty document', () => {
    expect(() => assertValidSpaFallbackHtml('  ')).toThrow('fallback HTML is empty');
  });

  it('rejects a meta refresh document', () => {
    expect(() => {
      assertValidSpaFallbackHtml(
        '<html><head><meta HTTP-EQUIV="Refresh" content="0; url=/en-us/200.html"></head></html>',
      );
    }).toThrow('fallback HTML contains a meta refresh redirect');
  });

  it('rejects a document without the Nuxt mount', () => {
    expect(() => assertValidSpaFallbackHtml('<html><body>Unavailable</body></html>'))
      .toThrow('fallback HTML does not contain the #__nuxt mount');
  });
});
