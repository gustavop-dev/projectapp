import {
  COMMUNICATION_ORDER_STORAGE_KEY,
  communicationFiltersFromQuery,
  communicationFiltersToQuery,
  resolveCommunicationOrder,
} from '../../composables/useCommunicationFilters';

describe('communication filter URL contract', () => {
  it('reads comma-separated dimensions as arrays', () => {
    const filters = communicationFiltersFromQuery({
      by: 'project',
      project: 'none',
      status: 'open,closed',
      channel: 'email,whatsapp',
      order: 'oldest',
    });

    expect(filters.project).toBe('none');
    expect(filters.status).toEqual(['open', 'closed']);
    expect(filters.channel).toEqual(['email', 'whatsapp']);
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
      storedOrder: 'recent',
    });

    expect(order).toBe('title');
  });

  it('uses the saved view order when the URL omits it', () => {
    const order = resolveCommunicationOrder({
      savedOrder: 'oldest',
      storedOrder: 'title',
    });

    expect(order).toBe('oldest');
  });

  it('uses the browser preference as the final fallback', () => {
    const order = resolveCommunicationOrder({ storedOrder: 'title' });

    expect(order).toBe('title');
    expect(COMMUNICATION_ORDER_STORAGE_KEY).toBe('panel.communications.order');
  });

  it('falls back to recent for an unsupported explicit order', () => {
    const order = resolveCommunicationOrder({
      queryOrder: 'unsupported',
      savedOrder: 'oldest',
      storedOrder: 'title',
    });

    expect(order).toBe('recent');
  });
});
