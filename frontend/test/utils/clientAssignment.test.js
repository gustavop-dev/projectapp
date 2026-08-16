import {
  buildAssignmentPlan,
  describeAssignmentPlan,
  describeAssignmentResult,
} from '../../utils/clientAssignment';

const ENTITY = { singular: 'hosting', plural: 'hostings' };

function hosting(overrides = {}) {
  return {
    id: 1,
    client: null,
    client_display_name: null,
    client_name: 'Kore - Marca',
    domain_url: 'kore.com.co',
    ...overrides,
  };
}

const ROWS = [
  hosting({ id: 1, client: null }),
  hosting({ id: 2, client: null, domain_url: 'tuhuella.co' }),
  hosting({ id: 3, client: 7, client_display_name: 'Kore SAS', domain_url: 'a.com' }),
  hosting({ id: 4, client: 7, client_display_name: 'Kore SAS', domain_url: 'b.com' }),
  hosting({ id: 5, client: 9, client_display_name: 'Juan Pérez', domain_url: 'c.com' }),
  hosting({ id: 6, client: 5, client_display_name: 'Ana Pérez', domain_url: 'd.com' }),
];

function assignPlan(selectedIds, targetClientId = 5) {
  return buildAssignmentPlan({
    rows: ROWS,
    selectedIds,
    mode: 'assign',
    targetClientId,
    targetClientLabel: 'Ana Pérez',
  });
}

describe('buildAssignmentPlan — assign', () => {
  it('splits a mixed selection instead of presenting it as one operation', () => {
    const plan = assignPlan([1, 2, 3, 5]);

    expect(plan.toAssign.map((r) => r.id)).toEqual([1, 2]);
    expect(plan.toReassign.map((r) => r.id)).toEqual([3, 5]);
    expect(plan.unchanged).toEqual([]);
    expect(plan.affected.map((r) => r.id)).toEqual([1, 2, 3, 5]);
  });

  it('holds back the rows already on the target so the promised count matches the write', () => {
    const plan = assignPlan([1, 6]);

    expect(plan.toAssign.map((r) => r.id)).toEqual([1]);
    expect(plan.unchanged.map((r) => r.id)).toEqual([6]);
    expect(plan.affected.map((r) => r.id)).toEqual([1]);
  });

  it('groups the source clients biggest-first, naming where each row comes from', () => {
    const plan = assignPlan([3, 4, 5]);

    expect(plan.byCurrentClient).toEqual([
      { id: 7, label: 'Kore SAS', count: 2 },
      { id: 9, label: 'Juan Pérez', count: 1 },
    ]);
  });

  it('drops ids with no matching record so a stale selection cannot inflate the count', () => {
    const plan = assignPlan([1, 999]);

    expect(plan.selectedCount).toBe(1);
    expect(plan.affected.map((r) => r.id)).toEqual([1]);
  });
});

describe('buildAssignmentPlan — unlink', () => {
  it('takes only the rows that have a client to lose', () => {
    const plan = buildAssignmentPlan({ rows: ROWS, selectedIds: [1, 3, 5], mode: 'unlink' });

    expect(plan.toUnlink.map((r) => r.id)).toEqual([3, 5]);
    expect(plan.unchanged.map((r) => r.id)).toEqual([1]);
    expect(plan.affected.map((r) => r.id)).toEqual([3, 5]);
  });

  it('leaves nothing to do when no selected row is linked', () => {
    const plan = buildAssignmentPlan({ rows: ROWS, selectedIds: [1, 2], mode: 'unlink' });

    expect(plan.toUnlink).toEqual([]);
    expect(plan.affected).toEqual([]);
  });
});

describe('describeAssignmentPlan', () => {
  it('names the client and the count when every row is unassigned', () => {
    const copy = describeAssignmentPlan(assignPlan([1, 2]), { entity: ENTITY });

    expect(copy.title).toBe('Asignar cliente');
    expect(copy.message).toBe('Se asignará Ana Pérez a 2 hostings sin cliente.');
    expect(copy.confirmText).toBe('Asignar');
  });

  it('calls a pure reassignment a change and says which client is being replaced', () => {
    const copy = describeAssignmentPlan(assignPlan([3, 4, 5]), { entity: ENTITY });

    expect(copy.title).toBe('Cambiar el cliente');
    expect(copy.message).toBe(
      '3 hostings cambiarán de cliente a Ana Pérez: 2 de Kore SAS, 1 de Juan Pérez.',
    );
  });

  it('keeps the two halves of a mixed selection apart', () => {
    const copy = describeAssignmentPlan(assignPlan([1, 2, 3]), { entity: ENTITY });

    expect(copy.message).toBe(
      'Se asignará Ana Pérez a 3 hostings: 2 sin cliente y 1 que cambia de cliente (1 de Kore SAS).',
    );
  });

  it('declares the untouched rows apart from the affected count', () => {
    const copy = describeAssignmentPlan(assignPlan([1, 6]), { entity: ENTITY });

    expect(copy.message).toBe(
      'Se asignará Ana Pérez a 1 hosting sin cliente. 1 hosting ya tiene a Ana Pérez y no cambia.',
    );
  });

  it('says how many rows are left loose and whose they were when unlinking', () => {
    const plan = buildAssignmentPlan({ rows: ROWS, selectedIds: [3, 4, 5], mode: 'unlink' });
    const copy = describeAssignmentPlan(plan, { entity: ENTITY });

    expect(copy.title).toBe('Desvincular cliente');
    expect(copy.message).toBe(
      '3 hostings quedarán sin cliente: 2 de Kore SAS, 1 de Juan Pérez.',
    );
    expect(copy.variant).toBe('danger');
  });
});

describe('describeAssignmentResult', () => {
  it('reports what the server actually wrote, not what was selected', () => {
    const plan = assignPlan([1, 2, 6]);

    expect(describeAssignmentResult(plan, 2, { entity: ENTITY })).toBe(
      '2 de 2 hostings actualizados; 1 sin cambios.',
    );
  });

  it('uses the unlink verb for an unlink run', () => {
    const plan = buildAssignmentPlan({ rows: ROWS, selectedIds: [3, 4], mode: 'unlink' });

    expect(describeAssignmentResult(plan, 2, { entity: ENTITY })).toBe(
      '2 de 2 hostings desvinculados.',
    );
  });
});

describe('buildAssignmentPlan — the project side effect', () => {
  it('counts the rows leaving a client that will also lose their project', () => {
    const rows = [
      hosting({ id: 3, client: 7, project: 40, project_name: 'Kore Web' }),
      hosting({ id: 1, client: null, project: 40, project_name: 'Kore Web' }),
      hosting({ id: 4, client: 7, project: null }),
    ];

    const plan = buildAssignmentPlan({
      rows,
      selectedIds: [3, 1, 4],
      mode: 'assign',
      targetClientId: 5,
      targetClientLabel: 'Ana Pérez',
    });

    // Only rows CHANGING client lose it: a client-less row keeps a project
    // its new client may already own — the server decides, the toast reports.
    expect(plan.projectCleared.map((row) => row.id)).toEqual([3]);
    const copy = describeAssignmentPlan(plan, { entity: ENTITY });
    expect(copy.message).toContain(
      '1 pierde también su proyecto (era del cliente anterior).',
    );
  });

  it('unlinking the client clears the project too and the copy says so', () => {
    const rows = [
      hosting({ id: 3, client: 7, project: 40, project_name: 'Kore Web' }),
    ];

    const plan = buildAssignmentPlan({ rows, selectedIds: [3], mode: 'unlink' });

    expect(plan.projectCleared.map((row) => row.id)).toEqual([3]);
    expect(describeAssignmentPlan(plan, { entity: ENTITY }).message)
      .toContain('1 pierde también su proyecto');
  });
});
