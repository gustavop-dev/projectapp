import { ref } from 'vue';

import { JSON_TEXTAREA_ROWS, makeJsonStats } from '../../utils/proposalJsonStats';

const stats = ({ source, raw, keys, updatedAt } = {}) => makeJsonStats({
  sourceRef: ref(source),
  rawStringRef: raw === undefined ? undefined : ref(raw),
  expectedKeys: keys || ['executiveSummary', 'investment', 'timeline'],
  updatedAtRef: updatedAt === undefined ? undefined : ref(updatedAt),
}).value;

describe('proposalJsonStats', () => {
  it('exports the shared textarea rows constant', () => {
    expect(JSON_TEXTAREA_ROWS).toBe(18);
  });

  it('counts only the expected keys present in the source', () => {
    const result = stats({ source: { executiveSummary: {}, investment: {}, extra: 1 } });
    expect(result.sectionCount).toBe(2);
  });

  it('counts zero sections for a nullish source', () => {
    expect(stats({ source: null }).sectionCount).toBe(0);
  });

  it('counts zero sections for an array source', () => {
    expect(stats({ source: [1, 2] }).sectionCount).toBe(0);
  });

  it('rounds the progress percentage', () => {
    const result = stats({ source: { executiveSummary: {}, investment: {} } });
    expect(result.progress).toBe(67);
  });

  it('reports zero progress when no keys are expected', () => {
    expect(stats({ source: {}, keys: [] }).progress).toBe(0);
  });

  it('reports the raw string size in bytes below one kilobyte', () => {
    expect(stats({ source: {}, raw: 'x'.repeat(512) }).size).toBe('512 B');
  });

  it('reports one decimal for sizes under ten kilobytes', () => {
    expect(stats({ source: {}, raw: 'x'.repeat(2048) }).size).toBe('2.0 KB');
  });

  it('reports whole kilobytes for sizes of ten kilobytes or more', () => {
    expect(stats({ source: {}, raw: 'x'.repeat(12 * 1024) }).size).toBe('12 KB');
  });

  it('derives the raw string from the source when no raw ref is given', () => {
    const result = stats({ source: { executiveSummary: { a: 1 } } });
    expect(result.size).toMatch(/ B$/);
  });

  it('formats the updated-at timestamp with the weekday standard', () => {
    const result = stats({ source: {}, updatedAt: '2026-07-16' });
    expect(result.updatedAt).toBe('Jue, 16 jul 2026');
  });

  it('falls back to the dash placeholder without an updated-at ref', () => {
    expect(stats({ source: {} }).updatedAt).toBe('—');
  });
});
