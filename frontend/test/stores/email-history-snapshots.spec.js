import { createPinia, setActivePinia } from 'pinia';
import { useEmailStore } from '../../stores/emails';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  put_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { get_request, create_request } = require('../../stores/services/request_http');

describe('email history snapshots store', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useEmailStore();
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('retains the attachment type catalog returned by history', async () => {
    const options = [{ value: 'format:pdf', label: 'PDF', group: 'format' }];
    get_request.mockResolvedValue({
      data: {
        results: [], total: 0, page: 1, has_next: false,
        attachment_type_options: options,
      },
    });

    await store.fetchHistory();

    expect(store.attachmentTypeOptions).toEqual(options);
  });

  it('sends presence and business type filters to the history API', async () => {
    get_request.mockResolvedValue({
      data: { results: [], total: 0, page: 1, has_next: false },
    });

    await store.fetchHistory(1, {
      has_attachments: 'true',
      attachment_type: 'business:collection_account',
    });

    expect(get_request).toHaveBeenCalledWith(
      'emails/history/?scope=all&page=1&has_attachments=true&attachment_type=business%3Acollection_account',
    );
  });

  it('posts only the editable recipient during an exact resend', async () => {
    create_request.mockResolvedValue({ data: { email_log_id: 22 } });

    const result = await store.resendEmail(9, 'nuevo@example.com');

    expect(create_request).toHaveBeenCalledWith(
      'emails/history/9/resend/',
      { recipient: 'nuevo@example.com' },
    );
    expect(result).toEqual({ success: true, data: { email_log_id: 22 } });
    expect(store.isResending).toBe(false);
  });

  it('returns the archived-resend error from the backend', async () => {
    create_request.mockRejectedValue({
      response: { data: { detail: 'El snapshot no está disponible.' } },
    });

    const result = await store.resendEmail(9, 'nuevo@example.com');

    expect(result.message).toBe('El snapshot no está disponible.');
    expect(store.isResending).toBe(false);
  });
});
