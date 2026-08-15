import { historySendsLink } from '~/utils/historyDeepLink';

describe('historySendsLink', () => {
  it('lands on the send subtab already narrowed to the record', () => {
    expect(historySendsLink('hosting', 42)).toEqual({
      path: '/panel/accounting/history',
      query: { tab: 'sends', entity_type: 'hosting', object_id: '42' },
    });
  });

  it('speaks the same filter keys the page writes when you filter by hand', () => {
    // The link is not a private protocol: pasting it, or editing the query
    // by hand, has to reach the same state as using the controls.
    const { query } = historySendsLink('collection_account', 7);

    expect(Object.keys(query).sort()).toEqual([
      'entity_type', 'object_id', 'tab',
    ]);
    expect(query.object_id).toBe('7');
  });
});
