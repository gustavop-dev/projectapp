import { getDiagnosticNextAction } from '../../utils/diagnosticNextAction';

const diagnostic = (overrides = {}) => ({
  status: 'draft',
  available_transitions: [],
  client: { email: 'cliente@x.com' },
  final_sent_at: null,
  ...overrides,
});

describe('getDiagnosticNextAction', () => {
  it('returns null for a nullish diagnostic', () => {
    expect(getDiagnosticNextAction(null)).toBeNull();
  });

  it('returns null for a draft without client email', () => {
    expect(getDiagnosticNextAction(diagnostic({ client: {} }))).toBeNull();
  });

  it('returns the send action for a draft with client email', () => {
    const action = getDiagnosticNextAction(diagnostic());
    expect(action.key).toBe('send');
    expect(action.label).toBe('Enviar envío inicial');
  });

  it('returns the analyze action for sent with negotiating available', () => {
    const action = getDiagnosticNextAction(diagnostic({
      status: 'sent', available_transitions: ['negotiating'],
    }));
    expect(action.key).toBe('analyze');
  });

  it('returns the analyze action for viewed with negotiating available', () => {
    const action = getDiagnosticNextAction(diagnostic({
      status: 'viewed', available_transitions: ['negotiating', 'rejected'],
    }));
    expect(action.key).toBe('analyze');
  });

  it('returns null for sent when negotiating is not available', () => {
    expect(getDiagnosticNextAction(diagnostic({
      status: 'sent', available_transitions: ['rejected'],
    }))).toBeNull();
  });

  it('treats a missing transitions list as empty for sent', () => {
    expect(getDiagnosticNextAction(diagnostic({
      status: 'sent', available_transitions: undefined,
    }))).toBeNull();
  });

  it('returns the send-final action while negotiating without final sent', () => {
    const action = getDiagnosticNextAction(diagnostic({ status: 'negotiating' }));
    expect(action.key).toBe('send-final');
  });

  it('returns null while negotiating once the final was sent', () => {
    expect(getDiagnosticNextAction(diagnostic({
      status: 'negotiating', final_sent_at: '2026-07-01T10:00:00Z',
    }))).toBeNull();
  });

  it('returns null for terminal statuses', () => {
    expect(getDiagnosticNextAction(diagnostic({ status: 'accepted' }))).toBeNull();
  });
});
