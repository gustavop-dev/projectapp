import {
  buildProjectAssignmentPlan,
  describeProjectAssignmentPlan,
  describeProjectAssignmentResult,
} from '../../utils/projectAssignment';

const ENTITY = { singular: 'hosting', plural: 'hostings' };

const PROJECT = {
  id: 40,
  name: 'Kore Web',
  client: { profile_id: 7, name: 'Kore SAS' },
};

const ROWS = [
  { id: 1, client: 7, project: null },
  { id: 2, client: 7, project: 41, project_name: 'Vieja Web' },
  { id: 3, client: 7, project: 40, project_name: 'Kore Web' },
  { id: 4, client: 9, project: null },
  { id: 5, client: null, project: null },
];

describe('buildProjectAssignmentPlan', () => {
  it('splits an assign selection into its four groups and excludes the blocked ones', () => {
    const plan = buildProjectAssignmentPlan({
      rows: ROWS,
      selectedIds: [1, 2, 3, 4, 5],
      mode: 'assign',
      targetProject: PROJECT,
    });

    expect(plan.toAssign.map((row) => row.id)).toEqual([1]);
    expect(plan.toReassign.map((row) => row.id)).toEqual([2]);
    expect(plan.unchanged.map((row) => row.id)).toEqual([3]);
    // A foreign client AND a client-less row are both ownership mismatches.
    expect(plan.blockedClientMismatch.map((row) => row.id)).toEqual([4, 5]);
    expect(plan.affected.map((row) => row.id)).toEqual([1, 2]);
    expect(plan.targetProjectId).toBe(40);
    expect(plan.targetProjectLabel).toBe('Kore Web');
  });

  it('unlink collects every row with a project and blocks nothing', () => {
    const plan = buildProjectAssignmentPlan({
      rows: ROWS,
      selectedIds: [1, 2, 3, 4],
      mode: 'unlink',
    });

    expect(plan.toUnlink.map((row) => row.id)).toEqual([2, 3]);
    expect(plan.unchanged.map((row) => row.id)).toEqual([1, 4]);
    expect(plan.blockedClientMismatch).toEqual([]);
    expect(plan.affected.map((row) => row.id)).toEqual([2, 3]);
  });

  it('names the origin projects biggest group first', () => {
    const rows = [
      { id: 1, client: 7, project: 41, project_name: 'Vieja Web' },
      { id: 2, client: 7, project: 42, project_name: 'Landing' },
      { id: 3, client: 7, project: 42, project_name: 'Landing' },
    ];

    const plan = buildProjectAssignmentPlan({
      rows,
      selectedIds: [1, 2, 3],
      mode: 'assign',
      targetProject: PROJECT,
    });

    expect(plan.byCurrentProject.map((group) => [group.label, group.count]))
      .toEqual([['Landing', 2], ['Vieja Web', 1]]);
  });

  it('drops selected ids with no row behind them', () => {
    const plan = buildProjectAssignmentPlan({
      rows: ROWS,
      selectedIds: [1, 99],
      mode: 'assign',
      targetProject: PROJECT,
    });

    expect(plan.selectedCount).toBe(1);
    expect(plan.affected.map((row) => row.id)).toEqual([1]);
  });
});

describe('describeProjectAssignmentPlan', () => {
  it('a mixed selection names both halves, the origins and the blocked rows', () => {
    const plan = buildProjectAssignmentPlan({
      rows: ROWS,
      selectedIds: [1, 2, 4],
      mode: 'assign',
      targetProject: PROJECT,
    });

    const copy = describeProjectAssignmentPlan(plan, { entity: ENTITY });

    expect(copy.title).toBe('Asignar proyecto');
    expect(copy.variant).toBe('warning');
    expect(copy.message).toContain(
      'Se asignará el proyecto "Kore Web" a 2 hostings: 1 sin proyecto y 1 que cambia de proyecto (1 de Vieja Web).',
    );
    expect(copy.message).toContain(
      '1 hosting pertenece a otro cliente y no se toca: reasigna primero su cliente.',
    );
  });

  it('unlink is destructive and names what each row loses', () => {
    const plan = buildProjectAssignmentPlan({
      rows: ROWS,
      selectedIds: [2, 3],
      mode: 'unlink',
    });

    const copy = describeProjectAssignmentPlan(plan, { entity: ENTITY });

    expect(copy.title).toBe('Quitar proyecto');
    expect(copy.variant).toBe('danger');
    expect(copy.message).toContain('2 hostings quedarán sin proyecto');
    expect(copy.message).toContain('1 de Vieja Web');
    expect(copy.message).toContain('1 de Kore Web');
  });
});

describe('describeProjectAssignmentResult', () => {
  it('reports what the server wrote next to what stayed untouched', () => {
    const plan = buildProjectAssignmentPlan({
      rows: ROWS,
      selectedIds: [1, 3, 4],
      mode: 'assign',
      targetProject: PROJECT,
    });

    const detail = describeProjectAssignmentResult(plan, 1, { entity: ENTITY });

    expect(detail).toBe(
      '1 de 1 hosting actualizado; 1 sin cambios; 1 de otro cliente sin tocar.',
    );
  });
});
