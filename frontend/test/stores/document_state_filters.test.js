import { createPinia, setActivePinia } from 'pinia';
import { useDocumentStore } from '../../stores/documents';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { get_request } = require('../../stores/services/request_http');

describe('document state filters', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useDocumentStore();
    get_request.mockReset().mockResolvedValue({ data: [] });
  });

  it('sends selected states with OR semantics in one query dimension', async () => {
    store.activeStateIds = [2, 4];

    await store.fetchDocuments();

    expect(get_request).toHaveBeenCalledWith('documents/?scope=active&states=2%2C4');
  });

  it('sends the absence filter independently', async () => {
    store.withoutStateIds = [6];

    await store.fetchDocuments();

    expect(get_request).toHaveBeenCalledWith('documents/?scope=active&without_states=6');
  });

  it('selecting a preset clears manual state filters', async () => {
    store.activeStateIds = [2];
    store.withoutStateIds = [6];

    await store.setStatePreset('sent_not_closed');

    expect(store.activeStateIds).toEqual([]);
    expect(store.withoutStateIds).toEqual([]);
    expect(get_request).toHaveBeenCalledWith('documents/?scope=active&preset=sent_not_closed');
  });

  it('selecting a manual state clears the preset', async () => {
    store.activeStatePreset = 'closed';

    await store.toggleStateFilter(2);

    expect(store.activeStatePreset).toBe('');
    expect(store.activeStateIds).toEqual([2]);
  });
});
