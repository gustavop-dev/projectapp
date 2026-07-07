import {
  getDiagnosticAttention,
  ATTENTION_THRESHOLDS,
} from '../../utils/diagnosticAttention';

const NOW = new Date('2026-07-06T12:00:00Z');
const daysAgo = (n) => new Date(NOW.getTime() - n * 86_400_000).toISOString();

describe('getDiagnosticAttention', () => {
  it('returns null for drafts, responded and non-sent statuses', () => {
    expect(getDiagnosticAttention({ status: 'draft' }, NOW)).toBeNull();
    expect(getDiagnosticAttention({ status: 'accepted', view_count: 9 }, NOW)).toBeNull();
    expect(
      getDiagnosticAttention(
        { status: 'sent', view_count: 9, responded_at: daysAgo(1) },
        NOW,
      ),
    ).toBeNull();
  });

  it('flags a hot lead when views reach the threshold without response', () => {
    const result = getDiagnosticAttention(
      { status: 'sent', view_count: ATTENTION_THRESHOLDS.HOT_VIEWS_MIN },
      NOW,
    );
    expect(result).toEqual({
      key: 'hot',
      label: `${ATTENTION_THRESHOLDS.HOT_VIEWS_MIN} vistas sin respuesta`,
      tone: 'danger',
    });
  });

  it('flags a stale send as warning after the warning threshold', () => {
    const result = getDiagnosticAttention(
      { status: 'sent', view_count: 0, initial_sent_at: daysAgo(4) },
      NOW,
    );
    expect(result.key).toBe('stale');
    expect(result.tone).toBe('warning');
    expect(result.label).toBe('4 d sin respuesta');
  });

  it('escalates to danger after the danger threshold, measured from last view', () => {
    const result = getDiagnosticAttention(
      {
        status: 'sent',
        view_count: 1,
        initial_sent_at: daysAgo(20),
        last_viewed_at: daysAgo(8),
      },
      NOW,
    );
    expect(result.tone).toBe('danger');
    expect(result.label).toBe('8 d sin respuesta');
  });

  it('stays quiet inside the warning window', () => {
    expect(
      getDiagnosticAttention(
        { status: 'sent', view_count: 1, initial_sent_at: daysAgo(2) },
        NOW,
      ),
    ).toBeNull();
  });
});
