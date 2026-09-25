const mockSavedTabs = [];
const mockStore = {
  preferences: { navigation_mode: 'project', thread_order: 'recent', page_size: 20 },
  fetchPreferences: jest.fn(),
};

jest.mock('~/composables/useSavedFilterTabs', () => {
  const { ref } = require('vue');
  return {
    sameFilters: (left, right) => JSON.stringify(left) === JSON.stringify(right),
    useSavedFilterTabs: () => ({
      savedTabs: ref(mockSavedTabs),
      isReady: ref(true),
      isTabLimitReached: ref(false),
      lastError: ref(null),
      loadTabs: jest.fn().mockResolvedValue(undefined),
      updateTabFilters: jest.fn(),
      saveTab: jest.fn(),
      deleteTab: jest.fn(),
      renameTab: jest.fn(),
      restoreTab: jest.fn(),
      rebaseTab: jest.fn(),
      reorderTabs: jest.fn(),
    }),
  };
});
jest.mock('~/stores/communications', () => ({
  useCommunicationsStore: () => mockStore,
}));

import { flushPromises, mount } from '@vue/test-utils';
import { reactive } from 'vue';
import {
  communicationFiltersFromQuery,
  communicationFiltersToQuery,
  resolveCommunicationOrder,
  useCommunicationFilters,
} from '../../composables/useCommunicationFilters';
import { COMMUNICATION_BUILTIN_TABS } from '../../constants/communicationFilters';

describe('communication filter URL contract', () => {
  // Falla si un folder de URL deja de recuperar o serializar su valor exacto.
  it.each([
    [55, '55'],
    ['none', 'none'],
  ])('round-trips folder %s through filter URL state', (folder, expectedFolder) => {
    const filters = communicationFiltersFromQuery({ by: 'project', project: '3', folder });

    expect(filters.folder).toBe(expectedFolder);
    expect(communicationFiltersToQuery(filters)).toEqual({ by: 'project', project: '3', folder: expectedFolder });
  });

  it('reads comma-separated dimensions as arrays', () => {
    const filters = communicationFiltersFromQuery({
      by: 'project',
      project: 'none',
      status: 'open,closed',
      channel: 'email,whatsapp',
      reply_status: 'answered,unanswered',
      order: 'oldest',
    });

    expect(filters.project).toBe('none');
    expect(filters.status).toEqual(['open', 'closed']);
    expect(filters.channel).toEqual(['email', 'whatsapp']);
    expect(filters.reply_status).toEqual(['answered', 'unanswered']);
    expect(filters.order).toBe('oldest');
  });

  it('infers client navigation for compatible old links', () => {
    const filters = communicationFiltersFromQuery({ client: '17' });

    expect(filters.by).toBe('client');
    expect(filters.client).toBe('17');
    expect(filters.project).toBe('');
  });

  it('serializes only the active mode selection', () => {
    const query = communicationFiltersToQuery({
      ...communicationFiltersFromQuery(),
      by: 'client',
      client: '17',
      project: '9',
      message_status: ['draft', 'sent'],
      q: '  alcance  ',
    });

    expect(query).toEqual({
      by: 'client',
      client: '17',
      message_status: 'draft,sent',
      q: 'alcance',
    });
  });

  it('normalizes scalar values restored from legacy saved views', () => {
    const filters = communicationFiltersFromQuery({
      status: 'open', direction: 'incoming', order: 'unsupported',
    });

    expect(filters.status).toEqual(['open']);
    expect(filters.direction).toEqual(['incoming']);
    expect(filters.order).toBe('recent');
  });

  it('prefers an explicit URL order', () => {
    const order = resolveCommunicationOrder({
      queryOrder: 'title',
      savedOrder: 'oldest',
      preferredOrder: 'recent',
    });

    expect(order).toBe('title');
  });

  it('uses the saved view order when the URL omits it', () => {
    const order = resolveCommunicationOrder({
      savedOrder: 'oldest',
      preferredOrder: 'title',
    });

    expect(order).toBe('oldest');
  });

  it('uses the account preference as the final fallback', () => {
    const order = resolveCommunicationOrder({ preferredOrder: 'title' });

    expect(order).toBe('title');
  });

  it('falls back to recent for an unsupported explicit order', () => {
    const order = resolveCommunicationOrder({
      queryOrder: 'unsupported',
      savedOrder: 'oldest',
      preferredOrder: 'title',
    });

    expect(order).toBe('recent');
  });
});

const FilterHarness = {
  setup() {
    return { filters: useCommunicationFilters() };
  },
  template: `
    <button data-testid="select-navigation" @click="filters.selectNavigation('9')">Seleccionar</button>
    <output data-testid="folder">{{ filters.currentFilters.folder }}</output>
  `,
};

describe('communication folder navigation state', () => {
  let route;

  beforeEach(() => {
    mockSavedTabs.splice(0);
    mockStore.fetchPreferences.mockReset().mockResolvedValue({ success: true });
    route = reactive({ query: { by: 'project', project: '3', folder: '55' } });
    global.useRoute = () => route;
    global.useRouter = () => ({ replace: jest.fn().mockResolvedValue(undefined) });
  });

  // Falla si cambiar de proyecto conserva una carpeta del contexto anterior.
  it('clears the selected folder after navigation changes', async () => {
    const wrapper = mount(FilterHarness);
    await flushPromises();

    await wrapper.get('[data-testid="select-navigation"]').trigger('click');

    expect(wrapper.get('[data-testid="folder"]').text()).toBe('');
  });

  // Falla si una vista guardada pierde su ubicación Sin carpeta al restaurarse.
  it('restores an unfiled folder from a saved filter', async () => {
    route.query = { tab: '7' };
    mockSavedTabs.push({
      id: 7,
      builtin_key: '',
      filters: { by: 'project', project: '3', folder: 'none', order: 'recent' },
    });
    const wrapper = mount(FilterHarness);
    await flushPromises();

    expect(wrapper.get('[data-testid="folder"]').text()).toBe('none');
  });
});

describe('communication factory filter contract', () => {
  it('puts pending drafts first', () => {
    expect(COMMUNICATION_BUILTIN_TABS[0]).toMatchObject({
      id: 'draft-pending',
      name: 'Borradores pendientes',
      filters: { message_status: ['draft'] },
    });
  });

  it('limits unanswered sends to open threads', () => {
    expect(COMMUNICATION_BUILTIN_TABS.find((tab) => tab.id === 'sent-unanswered')?.filters)
      .toEqual({
        status: ['open'],
        direction: ['outgoing'],
        message_status: ['sent'],
        reply_status: ['unanswered'],
      });
  });
});
