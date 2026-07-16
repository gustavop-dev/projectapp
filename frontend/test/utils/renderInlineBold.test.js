import { renderInlineBold } from '../../utils/renderInlineBold';

describe('renderInlineBold', () => {
  it('converts **bold** spans to <strong> tags', () => {
    expect(renderInlineBold('supere los **1.500 USD** netos'))
      .toBe('supere los <strong>1.500 USD</strong> netos');
  });

  it('converts multiple bold spans in one string', () => {
    expect(renderInlineBold('**Importante:** cubre **8 KPIs**'))
      .toBe('<strong>Importante:</strong> cubre <strong>8 KPIs</strong>');
  });

  it('escapes HTML before substituting, so injected tags never survive', () => {
    expect(renderInlineBold('<script>alert(1)</script> & **<b>x</b>**'))
      .toBe('&lt;script&gt;alert(1)&lt;/script&gt; &amp; <strong>&lt;b&gt;x&lt;/b&gt;</strong>');
  });

  it('leaves unclosed or empty markers literal', () => {
    expect(renderInlineBold('un ** suelto')).toBe('un ** suelto');
    expect(renderInlineBold('vacío ****')).toBe('vacío ****');
  });

  it('handles null and undefined as empty strings', () => {
    expect(renderInlineBold(null)).toBe('');
    expect(renderInlineBold(undefined)).toBe('');
  });
});
