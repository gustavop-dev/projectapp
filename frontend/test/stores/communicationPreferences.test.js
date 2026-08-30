jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

import { createPinia, setActivePinia } from 'pinia';
import {
  clearLegacyCommunicationPreferences,
  readLegacyCommunicationPreferences,
} from '../../constants/communicationPreferences';
import { useCommunicationsStore } from '../../stores/communications';
import { patch_request } from '../../stores/services/request_http';


const defaults = {
  navigation_mode: 'project',
  thread_order: 'recent',
  page_size: 20,
  default_channel: 'whatsapp',
  show_manual_help: true,
  navigation_width: 288,
};


describe('communication preference resilience', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
  });

  it('returns no legacy preferences when storage reads are blocked', () => {
    const blockedStorage = { getItem: () => { throw new Error('blocked'); } };

    expect(readLegacyCommunicationPreferences(blockedStorage)).toEqual({});
  });

  it('ignores blocked legacy cleanup', () => {
    const blockedStorage = { removeItem: () => { throw new Error('blocked'); } };

    expect(() => clearLegacyCommunicationPreferences(blockedStorage)).not.toThrow();
  });

  it('serializes preference writes in invocation order', async () => {
    let resolveFirst;
    patch_request
      .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve; }))
      .mockResolvedValueOnce({ data: { ...defaults, thread_order: 'title' } });
    const store = useCommunicationsStore();

    const first = store.updatePreferences({ thread_order: 'oldest' });
    const second = store.updatePreferences({ thread_order: 'title' });
    await Promise.resolve();
    await Promise.resolve();

    expect(patch_request).toHaveBeenCalledTimes(1);
    resolveFirst({ data: { ...defaults, thread_order: 'oldest' } });
    await first;
    await second;

    expect(patch_request.mock.calls.map(([, payload]) => payload)).toEqual([
      { thread_order: 'oldest' },
      { thread_order: 'title' },
    ]);
    expect(store.preferences.thread_order).toBe('title');
  });
});
