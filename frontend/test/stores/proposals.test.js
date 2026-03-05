/**
 * Tests for the proposals store.
 *
 * Covers: fetchPublicProposal, fetchProposals, fetchProposal,
 * createProposal, updateProposal, deleteProposal, sendProposal,
 * updateSection, reorderSections, respondToProposal, checkAdminAuth,
 * getters: getProposalById, enabledSections, totalSections.
 */
import { setActivePinia, createPinia } from 'pinia';
import { useProposalStore } from '../../stores/proposals';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const {
  get_request, create_request, patch_request, delete_request,
} = require('../../stores/services/request_http');

describe('useProposalStore', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useProposalStore();
    jest.clearAllMocks();
    jest.restoreAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('initial state', () => {
    it('has empty proposals array', () => {
      expect(store.proposals).toEqual([]);
    });

    it('has null currentProposal', () => {
      expect(store.currentProposal).toBeNull();
    });

    it('has isLoading false', () => {
      expect(store.isLoading).toBe(false);
    });

    it('has isUpdating false', () => {
      expect(store.isUpdating).toBe(false);
    });

    it('has error null', () => {
      expect(store.error).toBeNull();
    });
  });

  describe('getters', () => {
    it('getProposalById finds proposal', () => {
      store.proposals = [{ id: 1, title: 'A' }, { id: 2, title: 'B' }];
      expect(store.getProposalById(2)).toEqual({ id: 2, title: 'B' });
    });

    it('getProposalById returns undefined for missing id', () => {
      store.proposals = [{ id: 1 }];
      expect(store.getProposalById(99)).toBeUndefined();
    });

    it('enabledSections returns sorted enabled sections', () => {
      store.currentProposal = {
        sections: [
          { id: 1, is_enabled: true, order: 2 },
          { id: 2, is_enabled: false, order: 0 },
          { id: 3, is_enabled: true, order: 1 },
        ],
      };
      const result = store.enabledSections;
      expect(result).toHaveLength(2);
      expect(result[0].order).toBe(1);
      expect(result[1].order).toBe(2);
    });

    it('enabledSections returns empty array when no proposal', () => {
      expect(store.enabledSections).toEqual([]);
    });

    it('totalSections counts only enabled sections', () => {
      store.currentProposal = {
        sections: [
          { id: 1, is_enabled: true },
          { id: 2, is_enabled: false },
          { id: 3, is_enabled: true },
        ],
      };
      expect(store.totalSections).toBe(2);
    });
  });

  describe('fetchPublicProposal', () => {
    it('fetches proposal by UUID', async () => {
      const data = { id: 1, uuid: 'abc-123', title: 'Test' };
      get_request.mockResolvedValue({ data });

      const result = await store.fetchPublicProposal('abc-123');

      expect(get_request).toHaveBeenCalledWith('proposals/abc-123/');
      expect(store.currentProposal).toEqual(data);
      expect(result.success).toBe(true);
    });

    it('sets expired error on 410', async () => {
      get_request.mockRejectedValue({ response: { status: 410 } });

      const result = await store.fetchPublicProposal('expired-uuid');

      expect(result.success).toBe(false);
      expect(store.error).toBe('expired');
    });

    it('sets not_found error on 404', async () => {
      get_request.mockRejectedValue({ response: { status: 404 } });

      const result = await store.fetchPublicProposal('missing-uuid');

      expect(store.error).toBe('not_found');
    });

    it('sets unknown error on other status', async () => {
      get_request.mockRejectedValue({ response: { status: 500 } });

      const result = await store.fetchPublicProposal('error-uuid');

      expect(store.error).toBe('unknown');
    });

    it('resets isLoading after request', async () => {
      get_request.mockResolvedValue({ data: {} });

      await store.fetchPublicProposal('uuid');

      expect(store.isLoading).toBe(false);
    });
  });

  describe('fetchProposals', () => {
    it('fetches all proposals without filter', async () => {
      get_request.mockResolvedValue({ data: [{ id: 1 }, { id: 2 }] });

      const result = await store.fetchProposals();

      expect(get_request).toHaveBeenCalledWith('proposals/');
      expect(store.proposals).toHaveLength(2);
      expect(result.success).toBe(true);
    });

    it('fetches proposals with status filter', async () => {
      get_request.mockResolvedValue({ data: [{ id: 1, status: 'sent' }] });

      await store.fetchProposals('sent');

      expect(get_request).toHaveBeenCalledWith('proposals/?status=sent');
    });

    it('handles error', async () => {
      get_request.mockRejectedValue(new Error('fail'));

      const result = await store.fetchProposals();

      expect(result.success).toBe(false);
      expect(store.error).toBe('fetch_failed');
    });
  });

  describe('fetchProposal', () => {
    it('fetches single proposal by id', async () => {
      const data = { id: 5, title: 'Test', sections: [] };
      get_request.mockResolvedValue({ data });

      const result = await store.fetchProposal(5);

      expect(get_request).toHaveBeenCalledWith('proposals/5/detail/');
      expect(store.currentProposal).toEqual(data);
      expect(result.success).toBe(true);
    });

    it('handles error', async () => {
      get_request.mockRejectedValue(new Error('fail'));

      const result = await store.fetchProposal(99);

      expect(store.error).toBe('fetch_failed');
    });
  });

  describe('createProposal', () => {
    it('creates proposal and sets currentProposal', async () => {
      const newData = { id: 10, title: 'New', sections: [] };
      create_request.mockResolvedValue({ data: newData });

      const payload = { title: 'New', client_name: 'Client' };
      const result = await store.createProposal(payload);

      expect(create_request).toHaveBeenCalledWith('proposals/create/', payload);
      expect(store.currentProposal).toEqual(newData);
      expect(result.success).toBe(true);
    });

    it('handles validation error', async () => {
      create_request.mockRejectedValue({
        response: { data: { title: ['Required'] } },
      });

      const result = await store.createProposal({});

      expect(result.success).toBe(false);
      expect(store.error).toBe('create_failed');
    });
  });

  describe('updateProposal', () => {
    it('updates proposal metadata', async () => {
      const updated = { id: 1, title: 'Updated' };
      patch_request.mockResolvedValue({ data: updated });

      const result = await store.updateProposal(1, { title: 'Updated' });

      expect(patch_request).toHaveBeenCalledWith('proposals/1/update/', { title: 'Updated' });
      expect(store.currentProposal).toEqual(updated);
      expect(result.success).toBe(true);
    });

    it('handles error', async () => {
      patch_request.mockRejectedValue(new Error('fail'));

      const result = await store.updateProposal(1, {});

      expect(store.error).toBe('update_failed');
    });
  });

  describe('deleteProposal', () => {
    it('removes proposal from list', async () => {
      store.proposals = [{ id: 1 }, { id: 2 }];
      delete_request.mockResolvedValue({});

      const result = await store.deleteProposal(1);

      expect(delete_request).toHaveBeenCalledWith('proposals/1/delete/');
      expect(store.proposals).toEqual([{ id: 2 }]);
      expect(result.success).toBe(true);
    });

    it('clears currentProposal if matching', async () => {
      store.currentProposal = { id: 1 };
      store.proposals = [{ id: 1 }];
      delete_request.mockResolvedValue({});

      await store.deleteProposal(1);

      expect(store.currentProposal).toBeNull();
    });

    it('handles error', async () => {
      delete_request.mockRejectedValue(new Error('fail'));

      const result = await store.deleteProposal(1);

      expect(store.error).toBe('delete_failed');
    });
  });

  describe('sendProposal', () => {
    it('sends proposal and updates currentProposal', async () => {
      const sentData = { id: 1, status: 'sent', sent_at: '2026-03-04' };
      create_request.mockResolvedValue({ data: sentData });

      const result = await store.sendProposal(1);

      expect(create_request).toHaveBeenCalledWith('proposals/1/send/', {});
      expect(store.currentProposal).toEqual(sentData);
      expect(result.success).toBe(true);
    });

    it('handles send error', async () => {
      create_request.mockRejectedValue({
        response: { data: { error: 'Missing email' } },
      });

      const result = await store.sendProposal(1);

      expect(result.success).toBe(false);
      expect(store.error).toBe('send_failed');
    });
  });

  describe('updateSection', () => {
    it('updates section content_json and syncs currentProposal', async () => {
      store.currentProposal = {
        sections: [
          { id: 10, section_type: 'greeting', content_json: { clientName: 'Old' } },
          { id: 11, section_type: 'timeline', content_json: {} },
        ],
      };
      const updatedSection = {
        id: 10,
        section_type: 'greeting',
        content_json: { clientName: 'New Client' },
      };
      patch_request.mockResolvedValue({ data: updatedSection });

      const result = await store.updateSection(10, {
        content_json: { clientName: 'New Client' },
      });

      expect(patch_request).toHaveBeenCalledWith(
        'proposals/sections/10/update/',
        { content_json: { clientName: 'New Client' } },
      );
      expect(result.success).toBe(true);
      expect(store.currentProposal.sections[0]).toEqual(updatedSection);
    });

    it('updates section with complex content_json (executive_summary)', async () => {
      store.currentProposal = {
        sections: [{ id: 20, section_type: 'executive_summary', content_json: {} }],
      };
      const complexContent = {
        index: '1',
        title: 'Executive Summary',
        paragraphs: ['First paragraph.', 'Second paragraph.'],
        highlightsTitle: 'Includes',
        highlights: ['Custom design', 'Responsive development', 'SEO optimization'],
      };
      const updatedSection = { id: 20, section_type: 'executive_summary', content_json: complexContent };
      patch_request.mockResolvedValue({ data: updatedSection });

      const result = await store.updateSection(20, { content_json: complexContent });

      expect(result.success).toBe(true);
      expect(store.currentProposal.sections[0].content_json.paragraphs).toHaveLength(2);
      expect(store.currentProposal.sections[0].content_json.highlights).toHaveLength(3);
    });

    it('updates section with functional_requirements content_json', async () => {
      store.currentProposal = {
        sections: [{ id: 30, section_type: 'functional_requirements', content_json: {} }],
      };
      const reqContent = {
        index: '7',
        title: 'Functional Requirements',
        intro: 'Project requirements.',
        groups: [
          {
            id: 'views',
            icon: '🖥️',
            title: 'Views',
            description: 'Website screens.',
            items: [
              { icon: '🏠', name: 'Home', description: 'Main landing.' },
              { icon: '📧', name: 'Contact', description: 'Contact form.' },
            ],
          },
        ],
        additionalModules: [],
      };
      patch_request.mockResolvedValue({
        data: { id: 30, section_type: 'functional_requirements', content_json: reqContent },
      });

      const result = await store.updateSection(30, { content_json: reqContent });

      expect(result.success).toBe(true);
      expect(store.currentProposal.sections[0].content_json.groups[0].items).toHaveLength(2);
    });

    it('handles section update error', async () => {
      patch_request.mockRejectedValue(new Error('fail'));

      const result = await store.updateSection(10, {});

      expect(store.error).toBe('update_section_failed');
    });
  });

  describe('reorderSections', () => {
    it('reorders sections and updates local order', async () => {
      store.currentProposal = {
        sections: [
          { id: 1, order: 0 },
          { id: 2, order: 1 },
        ],
      };
      create_request.mockResolvedValue({});

      const newOrder = [{ id: 1, order: 1 }, { id: 2, order: 0 }];
      const result = await store.reorderSections(99, newOrder);

      expect(create_request).toHaveBeenCalledWith(
        'proposals/99/reorder-sections/',
        { sections: newOrder },
      );
      expect(result.success).toBe(true);
      expect(store.currentProposal.sections.find(s => s.id === 1).order).toBe(1);
      expect(store.currentProposal.sections.find(s => s.id === 2).order).toBe(0);
    });

    it('handles reorder error', async () => {
      create_request.mockRejectedValue(new Error('fail'));

      const result = await store.reorderSections(1, []);

      expect(result.success).toBe(false);
    });
  });

  describe('respondToProposal', () => {
    it('accepts proposal and updates currentProposal status', async () => {
      store.currentProposal = { uuid: 'abc', status: 'sent' };
      create_request.mockResolvedValue({ data: { status: 'accepted' } });

      const result = await store.respondToProposal('abc', 'accepted');

      expect(create_request).toHaveBeenCalledWith('proposals/abc/respond/', { action: 'accepted' });
      expect(result.success).toBe(true);
      expect(store.currentProposal.status).toBe('accepted');
    });

    it('rejects proposal', async () => {
      store.currentProposal = { uuid: 'abc', status: 'sent' };
      create_request.mockResolvedValue({ data: { status: 'rejected' } });

      const result = await store.respondToProposal('abc', 'rejected');

      expect(store.currentProposal.status).toBe('rejected');
    });

    it('handles error', async () => {
      create_request.mockRejectedValue(new Error('fail'));

      const result = await store.respondToProposal('abc', 'accepted');

      expect(result.success).toBe(false);
    });
  });

  describe('checkAdminAuth', () => {
    it('returns success with user data', async () => {
      get_request.mockResolvedValue({ data: { user: { username: 'admin', is_staff: true } } });

      const result = await store.checkAdminAuth();

      expect(get_request).toHaveBeenCalledWith('auth/check/');
      expect(result.success).toBe(true);
      expect(result.user.is_staff).toBe(true);
    });

    it('returns failure on error', async () => {
      get_request.mockRejectedValue(new Error('unauthorized'));

      const result = await store.checkAdminAuth();

      expect(result.success).toBe(false);
    });
  });
});
