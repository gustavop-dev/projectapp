/**
 * Tests for the contacts store.
 *
 * Covers: init, fetchContactsData, sendContact, resetSubmitState,
 * happy path, error handling, loading states.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useContactsStore } from '../../stores/contacts';

// Mock the HTTP service
jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
}));

const { get_request, create_request } = require('../../stores/services/request_http');

describe('useContactsStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useContactsStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('initial state', () => {
    it('has empty contacts array', () => {
      expect(store.contacts).toEqual([]);
    });

    it('has areUpdateContacts as false', () => {
      expect(store.areUpdateContacts).toBe(false);
    });

    it('has isSubmitting as false', () => {
      expect(store.isSubmitting).toBe(false);
    });

    it('has submitError as null', () => {
      expect(store.submitError).toBeNull();
    });

    it('has submitSuccess as false', () => {
      expect(store.submitSuccess).toBe(false);
    });
  });

  describe('fetchContactsData', () => {
    it('fetches contacts and updates state', async () => {
      const mockContacts = [{ email: 'a@b.com', subject: 'Test' }];
      get_request.mockResolvedValue({ data: mockContacts });

      await store.fetchContactsData();

      expect(get_request).toHaveBeenCalledWith('/contacts/');
      expect(store.contacts).toEqual(mockContacts);
      expect(store.areUpdateContacts).toBe(true);
    });

    it('does not fetch if already updated', async () => {
      store.areUpdateContacts = true;

      await store.fetchContactsData();

      expect(get_request).not.toHaveBeenCalled();
    });

    it('handles API error gracefully', async () => {
      get_request.mockRejectedValue(new Error('Network error'));

      await store.fetchContactsData();

      expect(store.contacts).toEqual([]);
    });

    it('handles string JSON response', async () => {
      get_request.mockResolvedValue({ data: '[{"email":"a@b.com"}]' });

      await store.fetchContactsData();

      expect(store.contacts).toEqual([{ email: 'a@b.com' }]);
    });

    it('handles invalid JSON string by falling back to empty array', async () => {
      get_request.mockResolvedValue({ data: '{invalid json' });

      await store.fetchContactsData();

      expect(store.contacts).toEqual([]);
      expect(store.areUpdateContacts).toBe(true);
    });
  });

  describe('init', () => {
    it('calls fetchContactsData when not updated', async () => {
      get_request.mockResolvedValue({ data: [] });

      await store.init();

      expect(get_request).toHaveBeenCalled();
    });

    it('skips fetch when already updated', async () => {
      store.areUpdateContacts = true;

      await store.init();

      expect(get_request).not.toHaveBeenCalled();
    });
  });

  describe('sendContact', () => {
    const formData = {
      fullName: 'John Doe',
      email: 'john@example.com',
      phone: '+1234567890',
      project: 'Need a website',
      budget: '5-10K',
    };

    it('sends contact form and returns success', async () => {
      create_request.mockResolvedValue({ data: { id: 1 } });

      const result = await store.sendContact(formData);

      expect(create_request).toHaveBeenCalledWith('new-contact/', {
        email: 'john@example.com',
        phone_number: '+1234567890',
        subject: 'John Doe',
        message: 'Need a website',
        budget: '5-10K',
      });
      expect(result.success).toBe(true);
      expect(store.submitSuccess).toBe(true);
      expect(store.isSubmitting).toBe(false);
    });

    it('sets isSubmitting during request', async () => {
      let capturedSubmitting;
      create_request.mockImplementation(() => {
        capturedSubmitting = store.isSubmitting;
        return Promise.resolve({ data: {} });
      });

      await store.sendContact(formData);

      expect(capturedSubmitting).toBe(true);
      expect(store.isSubmitting).toBe(false);
    });

    it('handles API error with response data', async () => {
      create_request.mockRejectedValue({
        response: { data: { email: ['Invalid email'] } },
      });

      const result = await store.sendContact(formData);

      expect(result.success).toBe(false);
      expect(store.submitError).toEqual({ email: ['Invalid email'] });
      expect(store.isSubmitting).toBe(false);
    });

    it('handles network error without response', async () => {
      create_request.mockRejectedValue(new Error('Network error'));

      const result = await store.sendContact(formData);

      expect(result.success).toBe(false);
      expect(store.submitError).toBe('Error al enviar el formulario. Por favor intenta de nuevo.');
    });

    it('sends null for optional fields when empty', async () => {
      create_request.mockResolvedValue({ data: {} });

      await store.sendContact({
        fullName: 'Jane',
        email: 'jane@example.com',
        phone: '',
        project: 'Hello',
        budget: '',
      });

      expect(create_request).toHaveBeenCalledWith('new-contact/', {
        email: 'jane@example.com',
        phone_number: null,
        subject: 'Jane',
        message: 'Hello',
        budget: null,
      });
    });
  });

  describe('resetSubmitState', () => {
    it('resets all submission flags', () => {
      store.submitError = 'Some error';
      store.submitSuccess = true;
      store.isSubmitting = true;

      store.resetSubmitState();

      expect(store.submitError).toBeNull();
      expect(store.submitSuccess).toBe(false);
      expect(store.isSubmitting).toBe(false);
    });
  });
});
