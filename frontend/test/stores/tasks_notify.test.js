/**
 * Tests that tasks store mutation actions expose a normalized `message` on
 * failure, so the board pages can show a descriptive notification instead of
 * failing silently.
 */

import { setActivePinia, createPinia } from 'pinia';
import { useTaskStore } from '../../stores/tasks';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { create_request, patch_request } = require('../../stores/services/request_http');

describe('tasks store — notification contract', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useTaskStore();
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('createTask exposes a field-error message on failure', async () => {
    create_request.mockRejectedValue({
      response: { status: 400, data: { title: ['Este campo es obligatorio.'] } },
    });

    const result = await store.createTask({ title: '' });

    expect(result.success).toBe(false);
    expect(result.message).toBe('Este campo es obligatorio.');
    expect(result.fieldErrors).toEqual({ title: 'Este campo es obligatorio.' });
  });

  it('moveTask exposes the Spanish status message on failure', async () => {
    patch_request.mockRejectedValue({
      response: { status: 400, data: { status: 'Estado no válido.' } },
    });

    const result = await store.moveTask(5, 'bogus', 0);

    expect(result.success).toBe(false);
    expect(result.message).toBe('Estado no válido.');
  });
});
