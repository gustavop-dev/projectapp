import {
  NO_CLIENT_KEY,
  groupByClient,
  sumClientGroups,
  withClientWeights,
} from '../../utils/incomeClients';

function income(overrides = {}) {
  return {
    id: 1,
    kind: 'expected',
    client: 5,
    client_name: 'Acme SAS',
    total_amount: '1000000.00',
    pending_amount: '1000000.00',
    ...overrides,
  };
}

describe('groupByClient', () => {
  it('separates billed (expected) from collected (liquid) so nothing double-counts', () => {
    const groups = groupByClient([
      income({ id: 1, kind: 'expected', total_amount: '1000', pending_amount: '400' }),
      income({ id: 2, kind: 'liquid', total_amount: '600', pending_amount: null }),
    ]);

    expect(groups).toHaveLength(1);
    expect(groups[0]).toMatchObject({
      id: 5,
      name: 'Acme SAS',
      count: 2,
      billed: 1000,
      collected: 600,
      pending: 400,
    });
  });

  it('collects rows without client into a trailing "Sin cliente" bucket', () => {
    const groups = groupByClient([
      income({ id: 1, client: null, client_name: null, total_amount: '500', pending_amount: '500' }),
      income({ id: 2, total_amount: '900', pending_amount: '900' }),
    ]);

    expect(groups.map((group) => group.id)).toEqual([5, NO_CLIENT_KEY]);
    expect(groups[1].name).toBe('Sin cliente');
    expect(groups[1].billed).toBe(500);
  });

  it('orders named clients by billed amount, biggest first', () => {
    const groups = groupByClient([
      income({ id: 1, client: 5, client_name: 'Acme', total_amount: '300', pending_amount: '0' }),
      income({ id: 2, client: 7, client_name: 'Globex', total_amount: '900', pending_amount: '0' }),
    ]);

    expect(groups.map((group) => group.name)).toEqual(['Globex', 'Acme']);
  });

  it('keeps lost income out of billed and collected', () => {
    const groups = groupByClient([
      income({ id: 1, kind: 'lost', total_amount: '750', pending_amount: null }),
    ]);

    expect(groups[0]).toMatchObject({ billed: 0, collected: 0, lost: 750 });
  });

  it('falls back to the id when the row carries no client name', () => {
    const groups = groupByClient([income({ client: 42, client_name: null })]);

    expect(groups[0].name).toBe('Cliente #42');
  });
});

describe('withClientWeights', () => {
  it('shares out billed amounts adding up to exactly 100', () => {
    const groups = withClientWeights(groupByClient([
      income({ id: 1, client: 5, client_name: 'A', total_amount: '1000', pending_amount: '0' }),
      income({ id: 2, client: 7, client_name: 'B', total_amount: '2000', pending_amount: '0' }),
      income({ id: 3, client: 9, client_name: 'C', total_amount: '3000', pending_amount: '0' }),
    ]));

    const total = groups.reduce((sum, group) => sum + group.weightPct, 0);
    expect(Math.round(total * 10) / 10).toBe(100);
  });

  it('yields zeros when there is nothing billed', () => {
    const groups = withClientWeights(groupByClient([
      income({ kind: 'liquid', total_amount: '500', pending_amount: null }),
    ]));

    expect(groups[0].weightPct).toBe(0);
  });
});

describe('sumClientGroups', () => {
  it('adds every column for the footer row', () => {
    const groups = groupByClient([
      income({ id: 1, client: 5, client_name: 'A', total_amount: '1000', pending_amount: '400' }),
      income({ id: 2, client: 7, client_name: 'B', kind: 'liquid', total_amount: '600' }),
      income({ id: 3, client: null, client_name: null, total_amount: '200', pending_amount: '200' }),
    ]);

    expect(sumClientGroups(groups)).toEqual({
      count: 3,
      billed: 1200,
      collected: 600,
      pending: 600,
      lost: 0,
    });
  });
});
