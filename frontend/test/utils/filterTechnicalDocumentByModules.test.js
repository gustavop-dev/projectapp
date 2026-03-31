import { filterTechnicalDocumentByModules } from '~/utils/filterTechnicalDocumentByModules';

describe('filterTechnicalDocumentByModules', () => {
  const doc = {
    purpose: 'x',
    epics: [
      {
        epicKey: 'a',
        title: 'Epic A',
        requirements: [
          { title: 'Base', description: 'always' },
          { title: 'Opt', linked_module_ids: ['module-5'], description: 'opt' },
        ],
      },
    ],
  };

  it('returns clone without mutating source', () => {
    const copy = { ...doc, epics: [{ ...doc.epics[0], requirements: [...doc.epics[0].requirements] }] };
    const out = filterTechnicalDocumentByModules(copy, []);
    expect(out).not.toBe(copy);
    expect(copy.epics[0].requirements).toHaveLength(2);
  });

  it('keeps unlinked requirements when selection empty', () => {
    const out = filterTechnicalDocumentByModules(doc, []);
    const epic = out.epics[0];
    expect(epic.requirements.map((r) => r.title)).toEqual(['Base']);
  });

  it('keeps linked requirement when module selected', () => {
    const out = filterTechnicalDocumentByModules(doc, ['module-5']);
    const titles = out.epics[0].requirements.map((r) => r.title);
    expect(titles).toContain('Base');
    expect(titles).toContain('Opt');
  });

  it('returns empty object when contentJson null', () => {
    expect(filterTechnicalDocumentByModules(null, [])).toEqual({});
  });

  it('returns out unchanged when epics missing', () => {
    const out = filterTechnicalDocumentByModules({ purpose: 'p' }, []);
    expect(out.epics).toBeUndefined();
  });

  it('skips null epic entries', () => {
    const out = filterTechnicalDocumentByModules({ epics: [null, { title: 'E', requirements: [] }] }, null);
    expect(out.epics).toHaveLength(1);
  });

  it('drops epic gated out by linked_module_ids', () => {
    const d = {
      epics: [{ title: 'Gated', linked_module_ids: ['x'], requirements: [{ title: 'r' }] }],
    };
    const out = filterTechnicalDocumentByModules(d, ['y']);
    expect(out.epics).toEqual([]);
  });

  it('accepts linkedModuleIds string on requirement', () => {
    const d = {
      epics: [{ title: 'E', requirements: [{ title: 'R', linkedModuleIds: 'module-1' }] }],
    };
    const out = filterTechnicalDocumentByModules(d, ['module-1']);
    expect(out.epics[0].requirements).toHaveLength(1);
  });

  it('keeps epic header when all requirements filtered out', () => {
    const d = {
      epics: [
        {
          title: 'OnlyHeader',
          requirements: [{ title: 'Opt', linked_module_ids: ['m'] }],
        },
      ],
    };
    const out = filterTechnicalDocumentByModules(d, []);
    expect(out.epics[0].requirements).toEqual([]);
    expect(out.epics[0].title).toBe('OnlyHeader');
  });

  it('treats object linked_module_ids as empty for visibility', () => {
    const d = {
      epics: [
        {
          title: 'E',
          requirements: [{ title: 'R', linked_module_ids: { not: 'valid' } }],
        },
      ],
    };
    const out = filterTechnicalDocumentByModules(d, []);
    expect(out.epics[0].requirements).toHaveLength(1);
  });
});
