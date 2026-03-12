/**
 * Tests for the useGtagConversions composable.
 *
 * Covers: trackFormSubmission, trackWhatsAppClick, trackBookACall
 * with gtag present/absent and with/without URL callback.
 */
import { useGtagConversions } from '../../composables/useGtagConversions';

describe('useGtagConversions', () => {
  let originalGtag;

  beforeEach(() => {
    originalGtag = window.gtag;
  });

  afterEach(() => {
    if (originalGtag === undefined) {
      delete window.gtag;
    } else {
      window.gtag = originalGtag;
    }
  });

  describe('when gtag is not available', () => {
    beforeEach(() => {
      delete window.gtag;
    });

    it('trackFormSubmission does nothing', () => {
      const { trackFormSubmission } = useGtagConversions();

      expect(() => trackFormSubmission()).not.toThrow();
    });

    it('trackWhatsAppClick does nothing', () => {
      const { trackWhatsAppClick } = useGtagConversions();

      expect(() => trackWhatsAppClick()).not.toThrow();
    });

    it('trackBookACall does nothing', () => {
      const { trackBookACall } = useGtagConversions();

      expect(() => trackBookACall()).not.toThrow();
    });
  });

  describe('when gtag is available', () => {
    let mockGtag;

    beforeEach(() => {
      mockGtag = jest.fn();
      window.gtag = mockGtag;
    });

    it('trackFormSubmission sends conversion event', () => {
      const { trackFormSubmission } = useGtagConversions();

      trackFormSubmission();

      expect(mockGtag).toHaveBeenCalledWith('event', 'conversion', expect.objectContaining({
        send_to: 'AW-16942315762/foFwCMGynP0bEPLx3I4_',
        value: 150000.0,
        currency: 'COP',
      }));
    });

    it('trackWhatsAppClick sends conversion event', () => {
      const { trackWhatsAppClick } = useGtagConversions();

      trackWhatsAppClick();

      expect(mockGtag).toHaveBeenCalledWith('event', 'conversion', expect.objectContaining({
        send_to: 'AW-16942315762/GOn5COrQn_0bEPLx3I4_',
        value: 100000.0,
        currency: 'COP',
      }));
    });

    it('trackBookACall sends conversion event', () => {
      const { trackBookACall } = useGtagConversions();

      trackBookACall();

      expect(mockGtag).toHaveBeenCalledWith('event', 'conversion', expect.objectContaining({
        send_to: 'AW-16942315762/DPviCO3Qn_0bEPLx3I4_',
        value: 150000.0,
        currency: 'COP',
      }));
    });

    it('trackFormSubmission callback redirects when URL provided', () => {
      const { trackFormSubmission } = useGtagConversions();

      trackFormSubmission('https://example.com');

      const callArgs = mockGtag.mock.calls[0][2];
      const openSpy = jest.spyOn(window, 'open').mockImplementation(() => {});
      callArgs.event_callback();
      expect(openSpy).toHaveBeenCalledWith('https://example.com', '_self');
      openSpy.mockRestore();
    });

    it('trackFormSubmission callback does not redirect without URL', () => {
      const { trackFormSubmission } = useGtagConversions();

      trackFormSubmission();

      const callArgs = mockGtag.mock.calls[0][2];
      const locationBefore = window.location.href;
      callArgs.event_callback();
      expect(window.location.href).toBe(locationBefore);
    });

    it('trackWhatsAppClick callback redirects when URL provided', () => {
      const { trackWhatsAppClick } = useGtagConversions();

      trackWhatsAppClick('https://wa.me/123');

      const callArgs = mockGtag.mock.calls[0][2];
      const openSpy = jest.spyOn(window, 'open').mockImplementation(() => {});
      callArgs.event_callback();
      expect(openSpy).toHaveBeenCalledWith('https://wa.me/123', '_self');
      openSpy.mockRestore();
    });

    it('trackWhatsAppClick callback does not redirect without URL', () => {
      const { trackWhatsAppClick } = useGtagConversions();

      trackWhatsAppClick();

      const callArgs = mockGtag.mock.calls[0][2];
      const locationBefore = window.location.href;
      callArgs.event_callback();
      expect(window.location.href).toBe(locationBefore);
    });

    it('trackBookACall callback redirects when URL provided', () => {
      const { trackBookACall } = useGtagConversions();

      trackBookACall('https://calendly.com/test');

      const callArgs = mockGtag.mock.calls[0][2];
      const openSpy = jest.spyOn(window, 'open').mockImplementation(() => {});
      callArgs.event_callback();
      expect(openSpy).toHaveBeenCalledWith('https://calendly.com/test', '_self');
      openSpy.mockRestore();
    });

    it('trackBookACall callback does not redirect without URL', () => {
      const { trackBookACall } = useGtagConversions();

      trackBookACall();

      const callArgs = mockGtag.mock.calls[0][2];
      const locationBefore = window.location.href;
      callArgs.event_callback();
      expect(window.location.href).toBe(locationBefore);
    });
  });
});
