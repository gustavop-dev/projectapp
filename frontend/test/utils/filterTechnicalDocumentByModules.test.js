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

  it('normIds treats empty string linked_module_ids as no filter', () => {
    const d = {
      epics: [{ title: 'E', requirements: [{ title: 'R', linkedModuleIds: '' }] }],
    };
    const out = filterTechnicalDocumentByModules(d, []);
    expect(out.epics[0].requirements).toHaveLength(1);
  });

  it('reqVisible returns true when selectedSet is null and requirement has linked ids', () => {
    const d = {
      epics: [{ title: 'E', requirements: [{ title: 'R', linked_module_ids: ['m1'] }] }],
    };
    // null selectedModuleIds → selectedSet = null → reqVisible returns true
    const out = filterTechnicalDocumentByModules(d, null);
    expect(out.epics[0].requirements).toHaveLength(1);
  });

  it('epicGatedOut returns false when selectedSet is null despite epic having linked ids', () => {
    const d = {
      epics: [{ title: 'E', linked_module_ids: ['m1'], requirements: [{ title: 'R' }] }],
    };
    // null selectedModuleIds → epicGatedOut returns false (not gated)
    const out = filterTechnicalDocumentByModules(d, null);
    expect(out.epics).toHaveLength(1);
  });

  it('epicMeaningfulHeader uses description when title is missing', () => {
    const d = {
      epics: [
        {
          description: 'Has desc',
          requirements: [{ title: 'R', linked_module_ids: ['m'] }],
        },
      ],
    };
    const out = filterTechnicalDocumentByModules(d, []);
    // requirements filtered out, but description keeps the epic header
    expect(out.epics[0].requirements).toEqual([]);
    expect(out.epics[0].description).toBe('Has desc');
  });

  it('epicMeaningfulHeader uses epicKey when title and description are missing', () => {
    const d = {
      epics: [
        {
          epicKey: 'epic-1',
          requirements: [{ title: 'R', linked_module_ids: ['m'] }],
        },
      ],
    };
    const out = filterTechnicalDocumentByModules(d, []);
    expect(out.epics[0].requirements).toEqual([]);
    expect(out.epics[0].epicKey).toBe('epic-1');
  });

  it('normIds treats whitespace-only string as empty', () => {
    const d = {
      epics: [{ title: 'E', requirements: [{ title: 'R', linked_module_ids: '   ' }] }],
    };
    // whitespace string → normIds returns [] → requirement treated as unlinked
    const out = filterTechnicalDocumentByModules(d, []);
    expect(out.epics[0].requirements).toHaveLength(1);
  });

  it('treats epic with no requirements field as having empty requirements', () => {
    const d = {
      epics: [{ title: 'E' }],
    };
    const out = filterTechnicalDocumentByModules(d, null);
    expect(out.epics).toHaveLength(1);
    expect(out.epics[0].requirements).toEqual([]);
  });

  it('keeps epic linked to always-included base group when selection is empty', () => {
    const d = {
      epics: [
        {
          title: 'Base epic',
          linked_module_ids: ['group-views'],
          requirements: [{ title: 'Base req', linked_module_ids: ['group-views'] }],
        },
      ],
    };

    const out = filterTechnicalDocumentByModules(d, [], ['group-views']);

    expect(out.epics).toHaveLength(1);
    expect(out.epics[0].requirements).toHaveLength(1);
  });

  it('still filters optional ids when selection is explicitly empty', () => {
    const d = {
      epics: [
        {
          title: 'Optional epic',
          linked_module_ids: ['module-pwa_module'],
          requirements: [{ title: 'Req', linked_module_ids: ['module-pwa_module'] }],
        },
      ],
    };

    const out = filterTechnicalDocumentByModules(d, [], ['group-views']);

    expect(out.epics).toEqual([]);
  });
});
