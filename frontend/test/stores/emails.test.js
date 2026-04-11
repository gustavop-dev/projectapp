/**
 * Tests for the emails store.
 *
 * Covers: init, fetchDefaults, fetchHistory (pagination), sendEmail,
 * happy path, error handling, loading states.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useEmailStore } from '../../stores/emails';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
}));

const { get_request, create_request } = require('../../stores/services/request_http');

describe('useEmailStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useEmailStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  // ── Initial state ──────────────────────────────────────────────────────────

  describe('initial state', () => {
    it('has empty history array', () => {
      expect(store.history).toEqual([]);
    });

    it('has default historyPagination', () => {
      expect(store.historyPagination).toEqual({ total: 0, page: 1, has_next: false });
    });

    it('has default defaults with greeting and footer', () => {
      expect(store.defaults).toEqual({ greeting: '', footer: '' });
    });

    it('has isSending as false', () => {
      expect(store.isSending).toBe(false);
    });

    it('has isLoadingHistory as false', () => {
      expect(store.isLoadingHistory).toBe(false);
    });

    it('has isLoadingDefaults as false', () => {
      expect(store.isLoadingDefaults).toBe(false);
    });

    it('has error as null', () => {
      expect(store.error).toBeNull();
    });
  });

  // ── fetchDefaults ──────────────────────────────────────────────────────────

  describe('fetchDefaults', () => {
    it('fetches defaults and returns success with data', async () => {
      const mockDefaults = { greeting: 'Hello', footer: 'Best regards' };
      get_request.mockResolvedValue({ data: mockDefaults });

      const result = await store.fetchDefaults();

      expect(get_request).toHaveBeenCalledWith('emails/defaults/');
      expect(store.defaults).toEqual(mockDefaults);
      expect(result).toEqual({ success: true, data: mockDefaults });
      expect(store.isLoadingDefaults).toBe(false);
    });

    it('sets isLoadingDefaults during request', async () => {
      let capturedLoading;
      get_request.mockImplementation(() => {
        capturedLoading = store.isLoadingDefaults;
        return Promise.resolve({ data: {} });
      });

      await store.fetchDefaults();

      expect(capturedLoading).toBe(true);
      expect(store.isLoadingDefaults).toBe(false);
    });

    it('handles API error and sets error state', async () => {
      get_request.mockRejectedValue(new Error('Network error'));

      const result = await store.fetchDefaults();

      expect(store.error).toBe('fetch_defaults_failed');
      expect(result).toEqual({ success: false });
      expect(store.isLoadingDefaults).toBe(false);
    });
  });

  // ── fetchHistory ───────────────────────────────────────────────────────────

  describe('fetchHistory', () => {
    it('fetches page 1 and replaces history', async () => {
      const mockResults = [{ id: 1, subject: 'Email 1' }, { id: 2, subject: 'Email 2' }];
      get_request.mockResolvedValue({
        data: { results: mockResults, total: 10, page: 1, has_next: true },
      });

      const result = await store.fetchHistory(1);

      expect(get_request).toHaveBeenCalledWith('emails/history/?page=1');
      expect(store.history).toEqual(mockResults);
      expect(result.success).toBe(true);
    });

    it('fetches page > 1 and appends to history', async () => {
      store.history = [{ id: 1, subject: 'Existing' }];
      const newResults = [{ id: 2, subject: 'New' }];
      get_request.mockResolvedValue({
        data: { results: newResults, total: 10, page: 2, has_next: false },
      });

      await store.fetchHistory(2);

      expect(store.history).toHaveLength(2);
      expect(store.history[0].subject).toBe('Existing');
      expect(store.history[1].subject).toBe('New');
    });

    it('updates historyPagination from response', async () => {
      get_request.mockResolvedValue({
        data: { results: [], total: 25, page: 3, has_next: true },
      });

      await store.fetchHistory(3);

      expect(store.historyPagination).toEqual({ total: 25, page: 3, has_next: true });
    });

    it('sets isLoadingHistory during request', async () => {
      let capturedLoading;
      get_request.mockImplementation(() => {
        capturedLoading = store.isLoadingHistory;
        return Promise.resolve({ data: { results: [], total: 0, page: 1, has_next: false } });
      });

      await store.fetchHistory();

      expect(capturedLoading).toBe(true);
      expect(store.isLoadingHistory).toBe(false);
    });

    it('handles API error and returns fallback data', async () => {
      get_request.mockRejectedValue(new Error('Server error'));

      const result = await store.fetchHistory();

      expect(store.error).toBe('fetch_history_failed');
      expect(result).toEqual({
        success: false,
        data: { results: [], total: 0, page: 1, has_next: false },
      });
      expect(store.isLoadingHistory).toBe(false);
    });

    it('defaults to page 1 when no argument provided', async () => {
      get_request.mockResolvedValue({
        data: { results: [], total: 0, page: 1, has_next: false },
      });

      await store.fetchHistory();

      expect(get_request).toHaveBeenCalledWith('emails/history/?page=1');
    });
  });

  // ── sendEmail ──────────────────────────────────────────────────────────────

  describe('sendEmail', () => {
    const formData = { to: 'test@example.com', subject: 'Hello', body: 'World' };

    it('sends email with formData and returns success', async () => {
      const mockResponse = { id: 1, status: 'sent' };
      create_request.mockResolvedValue({ data: mockResponse });

      const result = await store.sendEmail(formData);

      expect(create_request).toHaveBeenCalledWith('emails/send/', formData);
      expect(result).toEqual({ success: true, data: mockResponse });
      expect(store.isSending).toBe(false);
    });

    it('sets isSending during request', async () => {
      let capturedSending;
      create_request.mockImplementation(() => {
        capturedSending = store.isSending;
        return Promise.resolve({ data: {} });
      });

      await store.sendEmail(formData);

      expect(capturedSending).toBe(true);
      expect(store.isSending).toBe(false);
    });

    it('handles error with response.data.error', async () => {
      create_request.mockRejectedValue({
        response: { data: { error: 'invalid_recipient' } },
      });

      const result = await store.sendEmail(formData);

      expect(store.error).toBe('invalid_recipient');
      expect(result).toEqual({ success: false, error: 'invalid_recipient' });
      expect(store.isSending).toBe(false);
    });

    it('falls back to send_failed when no response error', async () => {
      create_request.mockRejectedValue(new Error('Network error'));

      const result = await store.sendEmail(formData);

      expect(store.error).toBe('send_failed');
      expect(result).toEqual({ success: false, error: undefined });
    });
  });
});
