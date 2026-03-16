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
