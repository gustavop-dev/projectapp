import { createPinia, setActivePinia } from 'pinia';
import { useProjectStateStore } from '../../stores/project_states';
import {
  create_request,
  get_request,
  patch_request,
} from '../../stores/services/request_http';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
}));

const ACTIVE = {
  id: 2,
  name: 'Activo',
  system_key: 'active',
  operational_effect: 'operating',
  group: 4,
  is_active: true,
  merged_into: null,
};

describe('project state store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    jest.clearAllMocks();
  });

  it('loads the project catalog', async () => {
    get_request
      .mockResolvedValueOnce({ data: [ACTIVE] })
      .mockResolvedValueOnce({
        data: [{ id: 4, name: 'Ciclo del proyecto', selection_mode: 'exclusive' }],
      });
    const store = useProjectStateStore();

    const result = await store.fetchCatalog();

    expect(result.success).toBe(true);
    expect(get_request).toHaveBeenNthCalledWith(1, 'project-states/');
    expect(get_request).toHaveBeenNthCalledWith(2, 'project-state-groups/');
    expect(store.statesByGroup[0].states).toEqual([ACTIVE]);
  });

  it('keeps the impact returned by preview', async () => {
    const impact = {
      target_effect: 'suspended',
      impact_token: 'a'.repeat(64),
      blockers: [],
    };
    create_request.mockResolvedValueOnce({ data: impact });
    const store = useProjectStateStore();

    const result = await store.previewTransition(9, { state_id: 4 });

    expect(create_request).toHaveBeenCalledWith(
      'projects/9/state-transitions/preview/',
      { state_id: 4 },
    );
    expect(result.data).toEqual(impact);
    expect(store.preview).toEqual(impact);
  });

  it('clears preview after applying a transition', async () => {
    create_request.mockResolvedValueOnce({
      data: { project: { id: 9, status: 'suspended' } },
    });
    const store = useProjectStateStore();
    store.preview = { impact_token: 'a'.repeat(64) };
    const payload = {
      state_id: 4,
      impact_token: 'a'.repeat(64),
      resolutions: [],
    };

    const result = await store.applyTransition(9, payload);

    expect(create_request).toHaveBeenCalledWith(
      'projects/9/state-transitions/',
      payload,
    );
    expect(result.success).toBe(true);
    expect(store.preview).toBeNull();
  });

  it('returns similar states for explicit confirmation', async () => {
    create_request.mockRejectedValueOnce({
      response: {
        status: 409,
        data: {
          code: 'similar_states',
          detail: 'Hay estados parecidos.',
          suggestions: [{ id: 7, name: 'Activo cliente' }],
        },
      },
    });
    const store = useProjectStateStore();

    const result = await store.createState({ name: 'Activa' });

    expect(result.needsConfirmation).toBe(true);
    expect(result.suggestions).toEqual([{ id: 7, name: 'Activo cliente' }]);
  });

  it('loads the dated project history', async () => {
    const history = [{ id: 31, opened_at: '2026-08-26T10:00:00Z' }];
    get_request.mockResolvedValueOnce({ data: history });
    const store = useProjectStateStore();

    const result = await store.fetchHistory(9);

    expect(get_request).toHaveBeenCalledWith('projects/9/state-history/');
    expect(result.data).toEqual(history);
    expect(store.history).toEqual(history);
  });
});
