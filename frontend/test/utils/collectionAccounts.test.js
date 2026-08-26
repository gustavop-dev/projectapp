import {
  NO_COLLECTION_GROUP_KEY,
  groupCollectionAccounts,
  sumCollectionAccountGroups,
} from '../../utils/collectionAccounts';

function account(overrides = {}) {
  return {
    id: 1,
    client: 5,
    client_display_name: 'Acme SAS',
    customer_name: 'Acme SAS',
    project_id: 10,
    project_name: 'Portal',
    total: '1000.00',
    commercial_status: 'issued',
    is_overdue: false,
    ...overrides,
  };
}

describe('groupCollectionAccounts', () => {
  it('classifies monetary totals by commercial status', () => {
    const [group] = groupCollectionAccounts([
      account({ id: 1, commercial_status: 'draft', total: '100' }),
      account({ id: 2, commercial_status: 'issued', total: '200' }),
      account({ id: 3, commercial_status: 'paid', total: '300' }),
      account({ id: 4, commercial_status: 'cancelled', total: '400' }),
    ]);

    expect(group).toMatchObject({
      emitted: 500,
      pending: 200,
      collected: 300,
      cancelled: 400,
    });
  });

  it('counts overdue as a subset of issued', () => {
    const [group] = groupCollectionAccounts([
      account({ id: 1, commercial_status: 'issued', is_overdue: true }),
      account({ id: 2, commercial_status: 'issued', is_overdue: false }),
    ]);

    expect(group.statusCounts).toEqual({
      draft: 0,
      issued: 2,
      overdue: 1,
      paid: 0,
      cancelled: 0,
    });
  });

  it('uses the live client as the group identity', () => {
    const groups = groupCollectionAccounts([
      account({ id: 1, client: 5, client_display_name: 'Acme' }),
      account({ id: 2, client: 7, client_display_name: 'Globex' }),
      account({ id: 3, client: 5, client_display_name: 'Acme' }),
    ], 'client');

    expect(groups.map(({ id, count }) => ({ id, count }))).toEqual([
      { id: 5, count: 2 },
      { id: 7, count: 1 },
    ]);
  });

  it('keeps snapshot-only projects in historical groups', () => {
    const groups = groupCollectionAccounts([
      account({ id: 1, project_id: null, project_name: 'Sitio legado' }),
    ], 'project');

    expect(groups[0]).toMatchObject({
      id: 'historical:Sitio legado',
      name: 'Sitio legado (histórico)',
      isHistorical: true,
    });
  });

  it('puts truly projectless accounts in the unassigned group', () => {
    const groups = groupCollectionAccounts([
      account({ project_id: null, project_name: '' }),
    ], 'project');

    expect(groups[0]).toMatchObject({
      id: NO_COLLECTION_GROUP_KEY,
      name: 'Sin proyecto',
      isUnassigned: true,
    });
  });

  it('orders named groups by pending amount descending', () => {
    const groups = groupCollectionAccounts([
      account({ id: 1, client: 5, client_display_name: 'Beta', total: '100' }),
      account({ id: 2, client: 7, client_display_name: 'Gamma', total: '500' }),
      account({ id: 3, client: 9, client_display_name: 'Alfa', total: '100' }),
    ]);

    expect(groups.map((group) => group.name)).toEqual(['Gamma', 'Alfa', 'Beta']);
  });

  it('keeps the unassigned group last despite its pending amount', () => {
    const groups = groupCollectionAccounts([
      account({ id: 1, client: null, client_display_name: null, total: '900' }),
      account({ id: 2, client: 7, client_display_name: 'Gamma', total: '100' }),
    ]);

    expect(groups.map((group) => group.id)).toEqual([7, NO_COLLECTION_GROUP_KEY]);
  });
});

describe('sumCollectionAccountGroups', () => {
  it('totals exactly the rows represented by the groups', () => {
    const groups = groupCollectionAccounts([
      account({ id: 1, client: 5, commercial_status: 'issued', total: '200' }),
      account({ id: 2, client: 7, commercial_status: 'paid', total: '300' }),
      account({ id: 3, client: 7, commercial_status: 'cancelled', total: '400' }),
    ]);

    expect(sumCollectionAccountGroups(groups)).toEqual({
      count: 3,
      emitted: 500,
      pending: 200,
      collected: 300,
      cancelled: 400,
      statusCounts: {
        draft: 0,
        issued: 1,
        overdue: 0,
        paid: 1,
        cancelled: 1,
      },
    });
  });
});
