/**
 * Tests for normalizeApiError — turns the various backend error payload shapes
 * into a consistent { message, code, hint, fieldErrors, status }.
 */

import { normalizeApiError } from '../../stores/services/normalize_api_error';

function axiosError(status, data) {
  return { response: { status, data } };
}

describe('normalizeApiError', () => {
  it('reads { error, code, hint }', () => {
    const r = normalizeApiError(axiosError(400, {
      error: 'Falta el correo del cliente.',
      code: 'missing_client_email',
      hint: 'Agrega el correo del cliente.',
    }));
    expect(r).toEqual({
      message: 'Falta el correo del cliente.',
      code: 'missing_client_email',
      hint: 'Agrega el correo del cliente.',
      fieldErrors: null,
      status: 400,
    });
  });

  it('falls back to DRF { detail }', () => {
    const r = normalizeApiError(axiosError(403, { detail: 'No autorizado.' }));
    expect(r.message).toBe('No autorizado.');
    expect(r.status).toBe(403);
  });

  it('reads { message }', () => {
    const r = normalizeApiError(axiosError(400, { message: 'Algo pasó.' }));
    expect(r.message).toBe('Algo pasó.');
  });

  it('extracts serializer field errors and uses the first as the message', () => {
    const r = normalizeApiError(axiosError(400, {
      email: ['Correo inválido.'],
      name: ['Requerido.'],
    }));
    expect(r.message).toBe('Correo inválido.');
    expect(r.fieldErrors).toEqual({ email: 'Correo inválido.', name: 'Requerido.' });
  });

  it('keeps field errors alongside a direct message', () => {
    const r = normalizeApiError(axiosError(400, {
      error: 'Revisa el formulario.',
      email: ['Correo inválido.'],
    }));
    expect(r.message).toBe('Revisa el formulario.');
    expect(r.fieldErrors).toEqual({ email: 'Correo inválido.' });
  });

  it('handles a bare string payload', () => {
    const r = normalizeApiError(axiosError(500, 'Internal Server Error'));
    expect(r.message).toBe('Internal Server Error');
  });

  it('uses the fallback when there is no response', () => {
    const r = normalizeApiError(new Error('network down'), 'Sin conexión.');
    expect(r.message).toBe('Sin conexión.');
    expect(r.status).toBeNull();
  });

  it('uses the fallback for an empty object payload', () => {
    const r = normalizeApiError(axiosError(400, {}), 'Error genérico.');
    expect(r.message).toBe('Error genérico.');
  });
});
