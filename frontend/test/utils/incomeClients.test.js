import {
  NO_CLIENT_KEY,
  groupByClient,
  groupHostingsByClient,
  hostingTotalsFor,
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

function hosting(overrides = {}) {
  return {
    id: 1,
    client: 5,
    client_name: 'Acme SAS',
    is_active: true,
    monthly_value: '50000.00',
    total_paid: '600000.00',
    cycles_count: 12,
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
  it('rounds a three-way tie via largest-remainder, not naive per-value rounding', () => {
    const groups = withClientWeights(groupByClient([
      income({ id: 1, client: 5, client_name: 'A', total_amount: '1000', pending_amount: '0' }),
      income({ id: 2, client: 7, client_name: 'B', total_amount: '1000', pending_amount: '0' }),
      income({ id: 3, client: 9, client_name: 'C', total_amount: '1000', pending_amount: '0' }),
    ]));

    // Each group is exactly 1/3 of the 3000 total (33.333...%). Naive
    // per-value rounding yields [33.3, 33.3, 33.3] (sums to 99.9, short by
    // one tenth). Falls if largestRemainder (utils/percent.js:60) is
    // bypassed or deleted and withClientWeights (incomeClients.js:103)
    // rounds each share independently instead of handing the leftover
    // tenth to the group with the largest remainder.
    expect(groups.map((group) => group.weightPct)).toEqual([33.4, 33.3, 33.3]);
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

describe('hostingTotalsFor', () => {
  it('counts an inactive hosting toward total paid but not monthly cost', () => {
    const totals = hostingTotalsFor([
      hosting({
        id: 1, is_active: true, monthly_value: '50000', total_paid: '600000', cycles_count: 12,
      }),
      hosting({
        id: 2, is_active: false, monthly_value: '30000', total_paid: '90000', cycles_count: 3,
      }),
    ]);

    // Falls if the is_active gate (incomeClients.js:82) is dropped and an
    // inactive hosting's monthly_value gets counted, overstating a client's
    // standing monthly cost in the "Hostings por cliente" table.
    expect(totals).toEqual({ monthly: 50000, paid: 690000, cycles: 15 });
  });
});

describe('groupHostingsByClient', () => {
  it('orders named clients by monthly cost, biggest first', () => {
    const groups = groupHostingsByClient([
      hosting({
        id: 1, client: 5, client_name: 'Acme', monthly_value: '50000', total_paid: '0', cycles_count: 0,
      }),
      hosting({
        id: 2, client: 7, client_name: 'Globex', monthly_value: '120000', total_paid: '0', cycles_count: 0,
      }),
    ]);

    // Falls if groupHostingsByClient stops sorting by monthly cost (e.g.
    // reverts to insertion order), silently reordering the client rows.
    expect(groups.map((group) => group.name)).toEqual(['Globex', 'Acme']);
  });

  it('collects hostings without a client into a trailing "Sin cliente" bucket', () => {
    const groups = groupHostingsByClient([
      hosting({
        id: 1, client: null, client_name: null, monthly_value: '40000', total_paid: '0', cycles_count: 0,
      }),
      hosting({
        id: 2, client: 5, client_name: 'Acme', monthly_value: '10000', total_paid: '0', cycles_count: 0,
      }),
    ]);

    // Falls if unassigned hostings stop bucketing under NO_CLIENT_KEY (e.g.
    // get merged into a named group or dropped), losing their monthly total.
    expect(groups.map((group) => group.id)).toEqual([5, NO_CLIENT_KEY]);
    expect(groups[1].name).toBe('Sin cliente');
    expect(groups[1].monthly).toBe(40000);
  });
});
