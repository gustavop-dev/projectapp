/**
 * Tests for the useSellerPrompt composable.
 *
 * Covers: loadSavedPrompt, savePrompt, resetPrompt, copyPrompt,
 * downloadPrompt, isEditing ref, DEFAULT_PROMPT export,
 * localStorage error handling, missing clipboard fallback.
 */

let useSellerPrompt;

beforeEach(() => {
  localStorage.clear();
  jest.resetModules();
  jest.isolateModules(() => {
    useSellerPrompt = require('../../composables/useSellerPrompt').useSellerPrompt;
  });
});

afterEach(() => {
  localStorage.clear();
  jest.restoreAllMocks();
});

describe('useSellerPrompt', () => {
  describe('initial state', () => {
    it('returns promptText with DEFAULT_PROMPT content', () => {
      const { promptText, DEFAULT_PROMPT } = useSellerPrompt();

      expect(promptText.value).toBe(DEFAULT_PROMPT);
    });

    it('returns isEditing as false', () => {
      const { isEditing } = useSellerPrompt();

      expect(isEditing.value).toBe(false);
    });

    it('exports DEFAULT_PROMPT as a non-empty string', () => {
      const { DEFAULT_PROMPT } = useSellerPrompt();

      expect(typeof DEFAULT_PROMPT).toBe('string');
      expect(DEFAULT_PROMPT.length).toBeGreaterThan(0);
    });
  });

  describe('loadSavedPrompt', () => {
    it('loads saved prompt from localStorage', () => {
      const customPrompt = 'Custom seller prompt text';
      localStorage.setItem('projectapp-seller-prompt-override', customPrompt);

      const { promptText, loadSavedPrompt } = useSellerPrompt();
      loadSavedPrompt();

      expect(promptText.value).toBe(customPrompt);
    });

    it('keeps DEFAULT_PROMPT when localStorage is empty', () => {
      const { promptText, DEFAULT_PROMPT, loadSavedPrompt } = useSellerPrompt();
      loadSavedPrompt();

      expect(promptText.value).toBe(DEFAULT_PROMPT);
    });

    it('gracefully handles localStorage error', () => {
      jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new Error('localStorage disabled');
      });

      const { promptText, DEFAULT_PROMPT, loadSavedPrompt } = useSellerPrompt();
      loadSavedPrompt();

      expect(promptText.value).toBe(DEFAULT_PROMPT);
    });
  });

  describe('savePrompt', () => {
    it('updates promptText ref and persists to localStorage', () => {
      const { promptText, savePrompt } = useSellerPrompt();
      const newText = 'Updated prompt content';

      savePrompt(newText);

      expect(promptText.value).toBe(newText);
      expect(localStorage.getItem('projectapp-seller-prompt-override')).toBe(newText);
    });

    it('gracefully handles localStorage write error', () => {
      jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('QuotaExceeded');
      });

      const { promptText, savePrompt } = useSellerPrompt();
      const newText = 'Some text';

      savePrompt(newText);

      expect(promptText.value).toBe(newText);
    });
  });

  describe('resetPrompt', () => {
    it('resets promptText to DEFAULT_PROMPT and clears localStorage', () => {
      localStorage.setItem('projectapp-seller-prompt-override', 'custom');
      const { promptText, DEFAULT_PROMPT, resetPrompt } = useSellerPrompt();
      promptText.value = 'custom';

      resetPrompt();

      expect(promptText.value).toBe(DEFAULT_PROMPT);
      expect(localStorage.getItem('projectapp-seller-prompt-override')).toBeNull();
    });

    it('gracefully handles localStorage removeItem error', () => {
      jest.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
        throw new Error('localStorage disabled');
      });

      const { promptText, DEFAULT_PROMPT, resetPrompt } = useSellerPrompt();

      resetPrompt();

      expect(promptText.value).toBe(DEFAULT_PROMPT);
    });
  });

  describe('copyPrompt', () => {
    it('calls navigator.clipboard.writeText with current prompt', async () => {
      const writeTextMock = jest.fn().mockResolvedValue(undefined);
      Object.assign(navigator, {
        clipboard: { writeText: writeTextMock },
      });

      const { promptText, copyPrompt } = useSellerPrompt();

      await copyPrompt();

      expect(writeTextMock).toHaveBeenCalledWith(promptText.value);
    });

    it('returns resolved promise when clipboard is unavailable', async () => {
      const originalClipboard = navigator.clipboard;
      Object.defineProperty(navigator, 'clipboard', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      const { copyPrompt } = useSellerPrompt();

      await expect(copyPrompt()).resolves.toBeUndefined();

      Object.defineProperty(navigator, 'clipboard', {
        value: originalClipboard,
        writable: true,
        configurable: true,
      });
    });
  });

  describe('downloadPrompt', () => {
    it('creates a blob download link and triggers click', () => {
      const clickMock = jest.fn();
      const appendChildMock = jest.spyOn(document.body, 'appendChild').mockImplementation(() => {});
      const removeChildMock = jest.spyOn(document.body, 'removeChild').mockImplementation(() => {});
      const createElementSpy = jest.spyOn(document, 'createElement').mockReturnValue({
        href: '',
        download: '',
        click: clickMock,
      });
      const revokeObjectURLMock = jest.fn();
      const createObjectURLMock = jest.fn().mockReturnValue('blob:fake-url');
      global.URL.createObjectURL = createObjectURLMock;
      global.URL.revokeObjectURL = revokeObjectURLMock;

      const { downloadPrompt } = useSellerPrompt();
      downloadPrompt();

      expect(createElementSpy).toHaveBeenCalledWith('a');
      expect(createObjectURLMock).toHaveBeenCalled();
      expect(clickMock).toHaveBeenCalled();
      expect(revokeObjectURLMock).toHaveBeenCalledWith('blob:fake-url');
      expect(appendChildMock).toHaveBeenCalled();
      expect(removeChildMock).toHaveBeenCalled();

      createElementSpy.mockRestore();
      appendChildMock.mockRestore();
      removeChildMock.mockRestore();
    });

    it('sets correct download filename', () => {
      const mockAnchor = { href: '', download: '', click: jest.fn() };
      jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor);
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => {});
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => {});
      global.URL.createObjectURL = jest.fn().mockReturnValue('blob:test');
      global.URL.revokeObjectURL = jest.fn();

      const { downloadPrompt } = useSellerPrompt();
      downloadPrompt();

      expect(mockAnchor.download).toBe('prompt-proposal.md');

      jest.restoreAllMocks();
    });
  });

  describe('isEditing', () => {
    it('can be toggled to true', () => {
      const { isEditing } = useSellerPrompt();

      isEditing.value = true;

      expect(isEditing.value).toBe(true);
    });

    it('can be toggled back to false', () => {
      const { isEditing } = useSellerPrompt();
      isEditing.value = true;

      isEditing.value = false;

      expect(isEditing.value).toBe(false);
    });
  });
});

describe('useSellerPrompt DEFAULT_PROMPT coherence rules (regression guard)', () => {
  const { useSellerPrompt } = require('../../composables/useSellerPrompt')
  const { DEFAULT_PROMPT } = useSellerPrompt()

  it.each([
    'sections.executiveSummary.paragraphs[]',
    'sections.contextDiagnostic.paragraphs[]',
    'sections.conversionStrategy.intro',
    'sections.roiProjection.subtitle',
    'sections.designUX.paragraphs[]',
    'sections.creativeSupport.paragraphs[]',
    'sections.developmentStages.intro',
    'sections.processMethodology.intro',
    'sections.functionalRequirements.intro',
    'sections.valueAddedModules.intro',
    'sections.investment.introText',
    'sections.timeline.introText',
    'sections.proposalSummary.subtitle',
    'sections.finalNote.message',
  ])('requires safe bold emphasis in %s', fieldPath => {
    expect(DEFAULT_PROMPT).toContain(`\`${fieldPath}\``)
  })

  it('forbids full-copy and Markdown emphasis in section leads', () => {
    expect(DEFAULT_PROMPT).toContain('No pongas en negrilla una oración o párrafo completo')
    expect(DEFAULT_PROMPT).toContain('no uses Markdown `**`')
    expect(DEFAULT_PROMPT).toContain('no inventes contenido para campos')
  })

  it('defines the deterministic slug algorithm for item ids', () => {
    expect(DEFAULT_PROMPT).toContain('Algoritmo del slug')
    expect(DEFAULT_PROMPT).toContain('item-<id_del_grupo>-<slug-del-nombre>')
    expect(DEFAULT_PROMPT).toContain('ñ→n')
  })

  it('defines deterministic dedupe by document order', () => {
    expect(DEFAULT_PROMPT).toContain('la PRIMERA aparición conserva el slug base')
  })

  it('locks id stability and language dependence', () => {
    expect(DEFAULT_PROMPT).toContain('NUNCA cambies un `id` ya asignado')
    expect(DEFAULT_PROMPT).toContain('nunca reutilices ids ni detalle técnico entre versiones ES/EN')
  })

  it('states the commercial↔technical synergy principle', () => {
    expect(DEFAULT_PROMPT).toContain('SINERGIA COMERCIAL↔TÉCNICA')
    expect(DEFAULT_PROMPT).toContain('DOS VISTAS DE LA MISMA HISTORIA')
  })

  it('guards item descriptions against non-selected module claims', () => {
    expect(DEFAULT_PROMPT).toContain('PROHIBIDO afirmar en un item capacidades')
  })

  it('lists the full 17-module catalog including the newest modules', () => {
    expect(DEFAULT_PROMPT).toContain('17 módulos opcionales')
    expect(DEFAULT_PROMPT).toContain('biometric_verification_module')
    expect(DEFAULT_PROMPT).toContain('behavior_tracking_module')
    expect(DEFAULT_PROMPT).toContain('qr_generator_module')
    expect(DEFAULT_PROMPT).toContain('content_generator_module')
    expect(DEFAULT_PROMPT).not.toContain('13 módulos')
    expect(DEFAULT_PROMPT).not.toContain('16 módulos')
  })

  it('treats ai_automation_module as the 5th base module', () => {
    expect(DEFAULT_PROMPT).toContain('agrupa los 5 módulos base sin costo extra')
    expect(DEFAULT_PROMPT).toContain(
      '["admin_module","analytics_dashboard","kpi_dashboard_module","manual_module","ai_automation_module"]',
    )
    expect(DEFAULT_PROMPT).not.toContain('4 módulos base')
    expect(DEFAULT_PROMPT).not.toContain('7 grupos base')
  })

  it('defines cross-cutting features as a contextual ninth base group', () => {
    expect(DEFAULT_PROMPT).toContain('9 grupos base')
    expect(DEFAULT_PROMPT).toContain('26 grupos (9 base + 17 opcionales)')
    expect(DEFAULT_PROMPT).toContain('catálogo inicial editable')
    expect(DEFAULT_PROMPT).toContain('no una lista fija')
    expect(DEFAULT_PROMPT).toContain('\`cross_cutting_features\` está después de \`features\`')
    expect(DEFAULT_PROMPT).not.toContain('8 grupos base en su orden original')
  })

  it('separates specific behaviors from cross-cutting qualities', () => {
    expect(DEFAULT_PROMPT).toContain('\`features\` contiene comportamientos')
    expect(DEFAULT_PROMPT).toContain('\`cross_cutting_features\` contiene cualidades')
    expect(DEFAULT_PROMPT).toContain('No dupliques una capacidad entre ambos grupos')
  })

  it('separates requirement discovery from QA and deployment', () => {
    expect(DEFAULT_PROMPT).toContain('levantamiento de requerimientos')
    expect(DEFAULT_PROMPT).toContain('QA y despliegue NUNCA se fusionan')
  })

  it('keeps warranty language tied to contractual context', () => {
    expect(DEFAULT_PROMPT).toContain('copiarse del contexto contractual')
    expect(DEFAULT_PROMPT).toContain('Nunca inventes un plazo')
  })

  it('prevents invented analytics summary cards', () => {
    expect(DEFAULT_PROMPT).toContain('No agregues una tarjeta de reportes/analítica')
    expect(DEFAULT_PROMPT).toContain('Resumen sin capacidades inventadas')
  })

  it('frames the functional requirements introduction around reviewable content', () => {
    expect(DEFAULT_PROMPT).toContain('Introducción orientada al contenido')
    expect(DEFAULT_PROMPT).toContain('No menciones módulos opcionales')
  })

  it('forbids inferred institutional scope', () => {
    expect(DEFAULT_PROMPT).toContain('No derivar alcance institucional')
    expect(DEFAULT_PROMPT).toContain('no inventes administración, autenticación, usuarios, roles, permisos')
  })

  it('includes the pre-output checklist', () => {
    expect(DEFAULT_PROMPT).toContain('CHECKLIST ANTES DE RESPONDER')
    expect(DEFAULT_PROMPT).toContain('Ids de items:')
  })
})
