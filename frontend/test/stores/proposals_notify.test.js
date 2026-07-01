/**
 * Tests the error/success contract that the proposals panel pages rely on to
 * build rich notifications: on failure the mutation actions expose the
 * normalized { message, code, hint } fields; on success they pass through
 * email_delivery.
 */

import { setActivePinia, createPinia } from 'pinia';
import { useProposalStore } from '../../stores/proposals';

jest.mock('../../stores/services/request_http', () => ({
  get_request: jest.fn(),
  create_request: jest.fn(),
  put_request: jest.fn(),
  patch_request: jest.fn(),
  delete_request: jest.fn(),
}));

const { create_request, patch_request } = require('../../stores/services/request_http');

function backend400(data) {
  return { response: { status: 400, data } };
}

describe('proposals store — notification contract', () => {
  let store;

  beforeEach(() => {
    setActivePinia(createPinia());
    store = useProposalStore();
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('updateProposalStatus surfaces backend message/code/hint on failure', async () => {
    patch_request.mockRejectedValue(backend400({
      error: 'Falta el correo del cliente.',
      code: 'missing_client_email',
      hint: 'Agrega el correo del cliente en la propuesta y vuelve a intentar.',
    }));

    const result = await store.updateProposalStatus(103, 'sent');

    expect(result.success).toBe(false);
    expect(result.message).toBe('Falta el correo del cliente.');
    expect(result.code).toBe('missing_client_email');
    expect(result.hint).toContain('Agrega el correo del cliente');
  });

  it('updateProposalStatus passes through email_delivery on success', async () => {
    patch_request.mockResolvedValue({
      data: { id: 103, status: 'sent', email_delivery: { ok: false, reason: 'send_failed', detail: 'No se pudo enviar el correo al cliente.' } },
    });

    const result = await store.updateProposalStatus(103, 'sent');

    expect(result.success).toBe(true);
    expect(result.email_delivery).toEqual({
      ok: false, reason: 'send_failed', detail: 'No se pudo enviar el correo al cliente.',
    });
  });

  it('sendProposal surfaces the normalized message on failure', async () => {
    create_request.mockRejectedValue(backend400({ error: 'Falta el correo del cliente.', code: 'missing_client_email' }));

    const result = await store.sendProposal(103);

    expect(result.success).toBe(false);
    expect(result.message).toBe('Falta el correo del cliente.');
    expect(result.code).toBe('missing_client_email');
  });

  it('resendProposal surfaces the normalized message on failure', async () => {
    create_request.mockRejectedValue(backend400({ error: 'El dominio del correo del cliente no puede recibir emails.', code: 'invalid_client_email_domain' }));

    const result = await store.resendProposal(103);

    expect(result.success).toBe(false);
    expect(result.code).toBe('invalid_client_email_domain');
    expect(result.message).toContain('dominio del correo');
  });
});
