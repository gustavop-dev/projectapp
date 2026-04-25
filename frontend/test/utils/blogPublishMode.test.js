import { resolveBlogPublishMode } from '../../utils/blogPublishMode';

const NOW = new Date('2026-04-25T15:00:00Z');

describe('resolveBlogPublishMode', () => {
  it('returns "now" mode for an already-published post', () => {
    const result = resolveBlogPublishMode(
      { is_published: true, published_at: '2026-04-20T12:00:00Z' },
      NOW,
    );
    expect(result).toEqual({ mode: 'now', scheduledIso: null, overdue: false });
  });

  it('returns "schedule" mode (not overdue) for a draft with future published_at', () => {
    const result = resolveBlogPublishMode(
      { is_published: false, published_at: '2026-04-25T18:00:00Z' },
      NOW,
    );
    expect(result.mode).toBe('schedule');
    expect(result.overdue).toBe(false);
    expect(result.scheduledIso).toBe('2026-04-25T18:00');
  });

  it('returns "schedule" mode WITH overdue=true for a draft whose scheduled time has passed', () => {
    // This is the bug fix: a post with is_published=false and published_at in the past
    // must NOT silently fall back to "draft" — the user perceives that as
    // "the post was demoted to borrador" when it was simply waiting for the safety-net.
    const result = resolveBlogPublishMode(
      { is_published: false, published_at: '2026-04-25T14:00:00Z' },
      NOW,
    );
    expect(result.mode).toBe('schedule');
    expect(result.overdue).toBe(true);
    expect(result.scheduledIso).toBe('2026-04-25T14:00');
  });

  it('returns "draft" mode for a true draft (no published_at)', () => {
    const result = resolveBlogPublishMode(
      { is_published: false, published_at: null },
      NOW,
    );
    expect(result).toEqual({ mode: 'draft', scheduledIso: null, overdue: false });
  });

  it('handles missing fields gracefully', () => {
    expect(resolveBlogPublishMode({}, NOW)).toEqual({
      mode: 'draft',
      scheduledIso: null,
      overdue: false,
    });
    expect(resolveBlogPublishMode(null, NOW)).toEqual({
      mode: 'draft',
      scheduledIso: null,
      overdue: false,
    });
  });
});
