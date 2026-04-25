import { mount } from '@vue/test-utils';
import { ref, nextTick } from 'vue';
import PromptEditor from '../../components/WebAppDiagnostic/admin/PromptEditor.vue';

function makeState(overrides = {}) {
  const defaultPrompt = 'default prompt text';
  return {
    isEditing: ref(false),
    promptText: ref(defaultPrompt),
    defaultPrompt,
    save: jest.fn(),
    reset: jest.fn(),
    copy: jest.fn().mockResolvedValue(undefined),
    download: jest.fn(),
    ...overrides,
  };
}

function mountEditor(stateOverrides = {}, propOverrides = {}) {
  const state = makeState(stateOverrides);
  const wrapper = mount(PromptEditor, {
    props: { state, downloadFilename: 'prompt.md', ...propOverrides },
  });
  return { wrapper, state };
}

describe('PromptEditor', () => {
  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders pre-formatted text in view mode when isEditing is false', () => {
    const { wrapper } = mountEditor({ promptText: ref('hello prompt') });

    expect(wrapper.find('pre').text()).toBe('hello prompt');
    expect(wrapper.find('textarea').exists()).toBe(false);
  });

  it('renders textarea in edit mode when isEditing is true', () => {
    const { wrapper } = mountEditor({ isEditing: ref(true) });

    expect(wrapper.find('textarea').exists()).toBe(true);
    expect(wrapper.find('pre').exists()).toBe(false);
  });

  it('shows Editar and Copiar buttons in view mode', () => {
    const { wrapper } = mountEditor();

    const text = wrapper.text();
    expect(text).toContain('Editar');
    expect(text).toContain('Copiar');
  });

  it('shows Guardar and Cancelar buttons in edit mode', () => {
    const { wrapper } = mountEditor({ isEditing: ref(true) });

    const text = wrapper.text();
    expect(text).toContain('Guardar');
    expect(text).toContain('Cancelar');
  });

  it('startEdit sets isEditing to true and copies promptText into textarea', async () => {
    const { wrapper, state } = mountEditor({ promptText: ref('my prompt') });

    const editarBtn = wrapper.findAll('button').find((b) => b.text() === 'Editar');
    await editarBtn.trigger('click');
    await nextTick();

    expect(state.isEditing.value).toBe(true);
    expect(wrapper.find('textarea').element.value).toBe('my prompt');
  });

  it('saveEdit calls state.save with the current buffer value', async () => {
    const { wrapper, state } = mountEditor({ isEditing: ref(true), promptText: ref('original') });

    await wrapper.find('textarea').setValue('updated text');
    const guardarBtn = wrapper.findAll('button').find((b) => b.text() === 'Guardar');
    await guardarBtn.trigger('click');

    expect(state.save).toHaveBeenCalledWith('updated text');
  });

  it('saveEdit sets isEditing to false', async () => {
    const { wrapper, state } = mountEditor({ isEditing: ref(true) });

    const guardarBtn = wrapper.findAll('button').find((b) => b.text() === 'Guardar');
    await guardarBtn.trigger('click');

    expect(state.isEditing.value).toBe(false);
  });

  it('cancelEdit sets isEditing to false without calling state.save', async () => {
    const { wrapper, state } = mountEditor({ isEditing: ref(true) });

    const cancelBtn = wrapper.findAll('button').find((b) => b.text() === 'Cancelar');
    await cancelBtn.trigger('click');

    expect(state.isEditing.value).toBe(false);
    expect(state.save).not.toHaveBeenCalled();
  });

  it('shows Restaurar original button when promptText differs from defaultPrompt', () => {
    const { wrapper } = mountEditor({
      promptText: ref('custom text'),
      defaultPrompt: 'default text',
    });

    expect(wrapper.text()).toContain('Restaurar original');
  });

  it('hides Restaurar original button when promptText matches defaultPrompt', () => {
    const { wrapper } = mountEditor({
      promptText: ref('same'),
      defaultPrompt: 'same',
    });

    expect(wrapper.text()).not.toContain('Restaurar original');
  });

  it('onCopy calls state.copy and shows copied feedback', async () => {
    jest.useFakeTimers();
    const { wrapper, state } = mountEditor();

    const copiarBtn = wrapper.findAll('button').find((b) => b.text() === 'Copiar');
    await copiarBtn.trigger('click');
    await nextTick();

    expect(state.copy).toHaveBeenCalled();
    expect(wrapper.text()).toContain('¡Copiado!');
  });

  it('copied feedback reverts to Copiar after 1500ms', async () => {
    jest.useFakeTimers();
    const { wrapper } = mountEditor();

    const copiarBtn = wrapper.findAll('button').find((b) => b.text() === 'Copiar');
    await copiarBtn.trigger('click');
    await nextTick();

    jest.advanceTimersByTime(1500);
    await nextTick();

    expect(wrapper.text()).toContain('Copiar');
    expect(wrapper.text()).not.toContain('¡Copiado!');
  });

  it('onDownload calls state.download with the downloadFilename prop', async () => {
    const { wrapper, state } = mountEditor({}, { downloadFilename: 'my-file.md' });

    const descargarBtn = wrapper.findAll('button').find((b) => b.text().includes('Descargar'));
    await descargarBtn.trigger('click');

    expect(state.download).toHaveBeenCalledWith('my-file.md');
  });

  it('onReset calls state.reset', async () => {
    const { wrapper, state } = mountEditor({
      promptText: ref('custom'),
      defaultPrompt: 'different',
    });

    const restaurarBtn = wrapper.findAll('button').find((b) => b.text() === 'Restaurar original');
    await restaurarBtn.trigger('click');

    expect(state.reset).toHaveBeenCalled();
  });
});
