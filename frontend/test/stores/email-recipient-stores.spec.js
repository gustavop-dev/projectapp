import { createPinia, setActivePinia } from 'pinia';
import { useDocumentStore } from '../../stores/documents';
import { useEmailStore } from '../../stores/emails';


jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  put_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { create_request: mockCreateRequest } = require('../../stores/services/request_http');


describe('email recipient store payloads', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockCreateRequest.mockReset().mockResolvedValue({ data: { ok: true } });
  });

  it('sends recipient groups during exact resend', async () => {
    const store = useEmailStore();

    await store.resendEmail(
      19,
      [{ email: 'uno@example.com' }, { email: 'dos@example.com' }],
      [{ email: 'copia@example.com' }],
    );

    expect(mockCreateRequest).toHaveBeenCalledWith(
      'emails/history/19/resend/',
      {
        recipient_emails: ['uno@example.com', 'dos@example.com'],
        cc_emails: ['copia@example.com'],
      },
    );
  });

  it('sends recipient groups from the document composer', async () => {
    const store = useDocumentStore();

    await store.sendDocumentEmail({
      recipient_emails: [{ email: 'uno@example.com' }],
      cc_emails: [{ email: 'copia@example.com' }],
      subject: 'Documento',
      greeting: 'Hola',
      footer: 'Saludos',
      sections: ['Contenido'],
      document_ids: [4],
    });

    const formData = mockCreateRequest.mock.calls[0][1];
    expect(formData.get('recipient_emails')).toBe('["uno@example.com"]');
    expect(formData.get('cc_emails')).toBe('["copia@example.com"]');
  });
});
