/**
 * Tests for the useMessages and useGlobalMessages composables.
 *
 * Covers: useMessages with viewKeyOverride, route-based resolution,
 * useGlobalMessages with section lookup.
 */
let mockTm;
let mockRouteName;
let useMessages;
let useGlobalMessages;

beforeEach(() => {
  mockTm = jest.fn((key) => ({ title: `${key}-title` }));
  mockRouteName = 'index___en-us';
  global.useI18n = () => ({ tm: mockTm });
  global.useRoute = () => ({ name: mockRouteName, params: {}, query: {}, path: '/', fullPath: '/' });

  jest.resetModules();
  const mod = require('../../composables/useMessages');
  useMessages = mod.useMessages;
  useGlobalMessages = mod.useGlobalMessages;
});

describe('useMessages', () => {
  describe('with viewKeyOverride', () => {
    it('returns messages for the override key', () => {
      mockTm.mockReturnValue({ hero: 'Welcome' });

      const { messages } = useMessages('aboutUs');

      expect(messages.value).toEqual({ hero: 'Welcome' });
      expect(mockTm).toHaveBeenCalledWith('aboutUs');
    });

    it('returns empty object when tm returns falsy', () => {
      mockTm.mockReturnValue(null);

      const { messages } = useMessages('missing');

      expect(messages.value).toEqual({});
    });
  });

  describe('with route-based resolution', () => {
    it('maps index route to landingSoftware', () => {
      mockRouteName = 'index___en-us';
      const { messages } = useMessages();

      messages.value;
      expect(mockTm).toHaveBeenCalledWith('landingSoftware');
    });

    it('maps landing-web-design route to home', () => {
      mockRouteName = 'landing-web-design___es-co';
      const { messages } = useMessages();

      messages.value;
      expect(mockTm).toHaveBeenCalledWith('home');
    });

    it('maps about-us route to aboutUs', () => {
      mockRouteName = 'about-us___en-us';
      const { messages } = useMessages();

      messages.value;
      expect(mockTm).toHaveBeenCalledWith('aboutUs');
    });

    it('maps contact route to contact', () => {
      mockRouteName = 'contact___en-us';
      const { messages } = useMessages();

      messages.value;
      expect(mockTm).toHaveBeenCalledWith('contact');
    });

    it('uses baseRouteName as fallback for unknown routes', () => {
      mockRouteName = 'custom-page___en-us';
      const { messages } = useMessages();

      messages.value;
      expect(mockTm).toHaveBeenCalledWith('custom-page');
    });

    it('defaults to home when route name is empty', () => {
      mockRouteName = '';
      const { messages } = useMessages();

      messages.value;
      expect(mockTm).toHaveBeenCalledWith('home');
    });

    it('defaults to home when route name is not a string', () => {
      mockRouteName = undefined;
      const { messages } = useMessages();

      messages.value;
      expect(mockTm).toHaveBeenCalledWith('home');
    });

    it('falls back to empty object when tm returns falsy for route-based key', () => {
      mockRouteName = 'index___en-us';
      mockTm.mockReturnValue(null);
      const { messages } = useMessages();

      expect(messages.value).toEqual({});
    });
  });
});

describe('useGlobalMessages', () => {
  it('returns global section messages', () => {
    mockTm.mockReturnValue({ navbar: { home: 'Home', about: 'About' } });

    const { globalMessages } = useGlobalMessages('navbar');

    expect(globalMessages.value).toEqual({ home: 'Home', about: 'About' });
  });

  it('returns empty object for missing section', () => {
    mockTm.mockReturnValue({});

    const { globalMessages } = useGlobalMessages('footer');

    expect(globalMessages.value).toEqual({});
  });

  it('returns empty object when global tm returns falsy', () => {
    mockTm.mockReturnValue(null);

    const { globalMessages } = useGlobalMessages('navbar');

    expect(globalMessages.value).toEqual({});
  });
});
