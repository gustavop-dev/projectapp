/**
 * Tests for the qr_cards store.
 * Covers: initial state, fetchCards, createCard, updateCard, deleteCard.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useQrCardsStore } from '../../stores/qr_cards';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request, create_request, patch_request, delete_request,
} = require('../../stores/services/request_http');

const mockCard = {
  id: '11111111-1111-1111-1111-111111111111',
  name: 'Tarjeta evento X',
  destination_url: '',
  is_active: true,
};

describe('useQrCardsStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useQrCardsStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('initial state', () => {
    it('starts empty, idle and error-free before any action runs', () => {
      expect(store.cards).toEqual([]);
      expect(store.isLoading).toBe(false);
      expect(store.error).toBeNull();
    });
  });

  describe('fetchCards', () => {
    it('fetches cards and updates state', async () => {
      get_request.mockResolvedValue({ data: [mockCard] });

      const result = await store.fetchCards();

      expect(get_request).toHaveBeenCalledWith('qr-cards/admin/');
      expect(store.cards).toHaveLength(1);
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      get_request.mockRejectedValue(new Error('Network error'));

      const result = await store.fetchCards();

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
    });
  });

  describe('createCard', () => {
    it('creates a card and prepends it to the list', async () => {
      create_request.mockResolvedValue({ data: mockCard });

      const result = await store.createCard({ name: 'Tarjeta evento X' });

      expect(create_request).toHaveBeenCalledWith('qr-cards/admin/create/', { name: 'Tarjeta evento X' });
      expect(store.cards[0]).toEqual(mockCard);
      expect(result.success).toBe(true);
    });

    it('returns validation errors on failure', async () => {
      const error = new Error('Bad request');
      error.response = { data: { name: ['This field is required.'] } };
      create_request.mockRejectedValue(error);

      const result = await store.createCard({});

      expect(result.success).toBe(false);
      expect(result.errors).toEqual({ name: ['This field is required.'] });
      expect(store.error).toBe('create_failed');
    });
  });

  describe('updateCard', () => {
    it('updates a card in place', async () => {
      store.cards = [mockCard];
      const updated = { ...mockCard, destination_url: 'https://example.com' };
      patch_request.mockResolvedValue({ data: updated });

      const result = await store.updateCard(mockCard.id, { destination_url: 'https://example.com' });

      expect(patch_request).toHaveBeenCalledWith(`qr-cards/admin/${mockCard.id}/update/`, { destination_url: 'https://example.com' });
      expect(store.cards[0].destination_url).toBe('https://example.com');
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      patch_request.mockRejectedValue(new Error('Network error'));

      const result = await store.updateCard(mockCard.id, {});

      expect(result.success).toBe(false);
      expect(store.error).toBe('update_failed');
    });
  });

  describe('deleteCard', () => {
    it('removes the card from the list', async () => {
      store.cards = [mockCard];
      delete_request.mockResolvedValue({});

      const result = await store.deleteCard(mockCard.id);

      expect(delete_request).toHaveBeenCalledWith(`qr-cards/admin/${mockCard.id}/delete/`);
      expect(store.cards).toHaveLength(0);
      expect(result.success).toBe(true);
    });

    it('handles API error gracefully', async () => {
      delete_request.mockRejectedValue(new Error('Network error'));

      const result = await store.deleteCard(mockCard.id);

      expect(result.success).toBe(false);
      expect(store.error).toBe('delete_failed');
    });
  });
});
