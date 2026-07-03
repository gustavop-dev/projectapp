import { buildExportParams } from '../../utils/accountingExportParams';

const MAPPING = {
  periodAfter: 'date_from',
  amountMin: 'amount_min',
  kind: 'kind',
  ledger: 'ledger',
  categories: 'category',
  search: 'q',
};

describe('buildExportParams', () => {
  it('skips empty, null and undefined values', () => {
    const params = buildExportParams(
      { periodAfter: '', amountMin: null, kind: undefined, search: 'kore' },
      MAPPING,
    );
    expect(params).toEqual({ q: 'kore' });
  });

  it('maps local keys to server keys and stringifies values', () => {
    const params = buildExportParams(
      { periodAfter: '2026-01-01', amountMin: 500, kind: 'liquid' },
      MAPPING,
    );
    expect(params).toEqual({
      date_from: '2026-01-01',
      amount_min: '500',
      kind: 'liquid',
    });
  });

  it('joins array values with commas and skips empty arrays', () => {
    expect(
      buildExportParams({ categories: ['business', 'personal'] }, MAPPING),
    ).toEqual({ category: 'business,personal' });
    expect(buildExportParams({ categories: [] }, MAPPING)).toEqual({});
  });
});
