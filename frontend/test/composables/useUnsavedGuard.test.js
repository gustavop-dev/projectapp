/**
 * `resetModules: true` está activo en jest.config.cjs: cada `it` estrena el
 * registro de módulos. Por eso vue, @vue/test-utils y el composable se cargan
 * con `require` DENTRO de cada test — un import de arriba dejaría al composable
 * con otra copia de vue y sus computed no reaccionarían al reactive del test.
 */

let routeLeaveGuard = null;

jest.mock('vue-router', () => ({
  onBeforeRouteLeave: jest.fn((cb) => { routeLeaveGuard = cb; }),
}));

/** Reproduce la semántica real de useConfirmModal para cada botón. */
function fakeConfirm(outcome) {
  const calls = [];
  const requestConfirm = async (options) => {
    calls.push(options);
    if (outcome === 'confirm') {
      if (options.onConfirm) await options.onConfirm();
      return true;
    }
    if (outcome === 'secondary') {
      // handleSecondaryAction hace `await fn()` y RECIÉN AHÍ resuelve false.
      if (options.onSecondary) await options.onSecondary();
      return false;
    }
    return false; // cancelar
  };
  return { requestConfirm, calls };
}

function setup({
  outcome = 'cancel',
  form: seed = { title: 'A', client: 1 },
  expose = null,
  ...overrides
} = {}) {
  const { defineComponent, reactive } = require('vue');
  const { mount } = require('@vue/test-utils');
  const { useUnsavedGuard } = require('~/composables/useUnsavedGuard');

  const form = reactive({ ...seed });
  const { requestConfirm, calls } = fakeConfirm(outcome);

  let api = null;
  const wrapper = mount(defineComponent({
    setup() {
      api = useUnsavedGuard({
        snapshot: () => (expose
          ? Object.fromEntries(expose.map((key) => [key, form[key]]))
          : { ...form }),
        labels: { title: 'título', client: 'cliente', project: 'proyecto', language: 'idioma' },
        confirm: requestConfirm,
        ...overrides,
      });
      return () => null;
    },
  }));

  return { api, form, wrapper, calls };
}

describe('useUnsavedGuard — naming what is unsaved', () => {
  it('reports nothing dirty before a baseline is committed', () => {
    const { api } = setup();
    expect(api.hasChanges.value).toBe(false);
    expect(api.dirtyLabels.value).toEqual([]);
  });

  it('names the single field that changed', () => {
    const { api, form } = setup();
    api.commit();
    form.client = 2;

    expect(api.dirtyLabels.value).toEqual(['cliente']);
    expect(api.unsavedTitle.value).toBe('Cliente sin guardar');
  });

  // El caso exacto del requerimiento.
  it('names both fields when client and project change together', () => {
    const { api, form } = setup({ form: { title: 'A', client: 1, project: null } });
    api.commit();
    form.client = 2;
    form.project = 9;

    expect(api.unsavedTitle.value).toBe('Cliente y proyecto sin guardar');
  });

  it('applies the e conjunction to the field list', () => {
    const { api, form } = setup({ form: { client: 1, language: 'es' } });
    api.commit();
    form.client = 2;
    form.language = 'en';

    expect(api.unsavedTitle.value).toBe('Cliente e idioma sin guardar');
  });

  it('counts instead of listing once past three fields', () => {
    const { api, form } = setup({ form: { title: 'A', client: 1, project: null, language: 'es' } });
    api.commit();
    form.title = 'B';
    form.client = 2;
    form.project = 9;
    form.language = 'en';

    expect(api.unsavedTitle.value).toBe('4 campos sin guardar');
    expect(api.unsavedDetail.value).toBe('Título, cliente, proyecto e idioma.');
  });

  // Comparar, no marcar "tocado": deshacer a mano deja el formulario limpio.
  it('goes back to clean when the value returns to its baseline', () => {
    const { api, form } = setup();
    api.commit();
    form.client = 2;
    expect(api.hasChanges.value).toBe(true);

    form.client = 1;
    expect(api.hasChanges.value).toBe(false);
  });

  it('re-baselines on commit so a saved form stops warning', () => {
    const { api, form } = setup();
    api.commit();
    form.client = 2;
    api.commit();

    expect(api.hasChanges.value).toBe(false);
  });

  // Excluir un campo que el servidor ya persistió (una portada subida) se hace
  // dejándolo fuera del snapshot: sin esto el aviso lo nombraría para siempre.
  it('ignores fields the snapshot does not expose', () => {
    const { api, form } = setup({
      form: { title: 'A', coverImage: 'vieja.png' },
      expose: ['title'],
    });
    api.commit();
    form.title = 'B';
    form.coverImage = 'subida.png';

    expect(api.dirtyLabels.value).toEqual(['título']);
  });
});

describe('useUnsavedGuard — the three exits', () => {
  it('lets navigation through untouched when nothing is dirty', async () => {
    const save = jest.fn();
    const { calls } = setup({ save });

    await expect(routeLeaveGuard()).resolves.toBe(true);
    expect(calls).toHaveLength(0);
  });

  it('saves and leaves when the primary exit is chosen', async () => {
    const save = jest.fn().mockResolvedValue(true);
    const { api, form } = setup({ outcome: 'confirm', save });
    api.commit();
    form.client = 2;

    await expect(routeLeaveGuard()).resolves.toBe(true);
    expect(save).toHaveBeenCalledTimes(1);
  });

  // La cuenta de cobro emitida: el backend rechaza y la página NO debe irse.
  it('stays on the page when the save it offered fails', async () => {
    const save = jest.fn().mockResolvedValue(false);
    const { api, form } = setup({ outcome: 'confirm', save });
    api.commit();
    form.client = 2;

    await expect(routeLeaveGuard()).resolves.toBe(false);
    expect(save).toHaveBeenCalledTimes(1);
  });

  // La regresión de todo el workaround: handleSecondaryAction resuelve FALSE,
  // igual que cancelar, así que sin las banderas "descartar" no dejaría salir.
  it('leaves without saving when the secondary exit is chosen', async () => {
    const save = jest.fn().mockResolvedValue(true);
    const { api, form } = setup({ outcome: 'secondary', save });
    api.commit();
    form.client = 2;

    await expect(routeLeaveGuard()).resolves.toBe(true);
    expect(save).not.toHaveBeenCalled();
  });

  it('keeps the user on the page when the dialog is cancelled', async () => {
    const save = jest.fn().mockResolvedValue(true);
    const { api, form } = setup({ outcome: 'cancel', save });
    api.commit();
    form.client = 2;

    await expect(routeLeaveGuard()).resolves.toBe(false);
    expect(save).not.toHaveBeenCalled();
  });

  it('puts saving on the primary button and discarding on the secondary', async () => {
    const save = jest.fn().mockResolvedValue(true);
    const { api, form, calls } = setup({ outcome: 'confirm', save });
    api.commit();
    form.client = 2;
    await routeLeaveGuard();

    expect(calls[0].confirmText).toBe('Guardar y salir');
    expect(calls[0].secondaryText).toBe('Salir sin guardar');
    expect(calls[0].cancelText).toBe('Seguir editando');
  });

  // Ofrecer un guardado que el backend contesta con 400 enseña a desconfiar
  // del diálogo: con canSave en false quedan dos salidas, no tres.
  it('drops the save exit when saving is blocked', async () => {
    const save = jest.fn();
    const { api, form, calls } = setup({
      outcome: 'confirm',
      save,
      canSave: () => false,
      blockedReason: 'Este documento está emitido.',
    });
    api.commit();
    form.client = 2;
    await routeLeaveGuard();

    expect(calls[0].secondaryText).toBeUndefined();
    expect(calls[0].confirmText).toBe('Salir sin guardar');
    expect(calls[0].message).toContain('Este documento está emitido.');
    expect(save).not.toHaveBeenCalled();
  });

  it('offers only two exits when the page passes no save function', async () => {
    const { api, form, calls } = setup({ outcome: 'confirm' });
    api.commit();
    form.client = 2;
    await routeLeaveGuard();

    expect(calls[0].secondaryText).toBeUndefined();
    expect(api.canSaveNow.value).toBe(false);
  });
});

describe('useUnsavedGuard — guarded refresh', () => {
  it('refreshes straight away when nothing is dirty', async () => {
    const reload = jest.fn().mockResolvedValue();
    const { api, calls } = setup({ reload });

    await api.guardedReload();

    expect(reload).toHaveBeenCalledTimes(1);
    expect(calls).toHaveLength(0);
  });

  it('skips the refresh that would overwrite unsaved edits when cancelled', async () => {
    const reload = jest.fn().mockResolvedValue();
    const save = jest.fn().mockResolvedValue(true);
    const { api, form, calls } = setup({ outcome: 'cancel', reload, save });
    api.commit();
    form.client = 2;

    await api.guardedReload();

    // Preguntó antes de recargar, y al cancelar los cambios siguen ahí.
    expect(calls[0].confirmText).toBe('Guardar y actualizar');
    expect(api.hasChanges.value).toBe(true);
    expect(form.client).toBe(2);
    expect(reload).not.toHaveBeenCalled();
    expect(save).not.toHaveBeenCalled();
  });

  it('refreshes after the user discards the pending edits', async () => {
    const reload = jest.fn().mockResolvedValue();
    const save = jest.fn().mockResolvedValue(true);
    const { api, form } = setup({ outcome: 'secondary', reload, save });
    api.commit();
    form.client = 2;

    await api.guardedReload();

    expect(reload).toHaveBeenCalledTimes(1);
    expect(save).not.toHaveBeenCalled();
  });

  it('saves before refreshing when that exit is chosen', async () => {
    const reload = jest.fn().mockResolvedValue();
    const save = jest.fn().mockResolvedValue(true);
    const { api, form, calls } = setup({ outcome: 'confirm', reload, save });
    api.commit();
    form.client = 2;

    await api.guardedReload();

    expect(save).toHaveBeenCalledTimes(1);
    expect(reload).toHaveBeenCalledTimes(1);
    expect(calls[0].confirmText).toBe('Guardar y actualizar');
  });
});

describe('useUnsavedGuard — tab close', () => {
  it('arms the browser dialog only while there are unsaved changes', () => {
    const addSpy = jest.spyOn(window, 'addEventListener');
    const { api, form } = setup();
    const handler = addSpy.mock.calls.find(([name]) => name === 'beforeunload')[1];

    const clean = { preventDefault: jest.fn(), returnValue: undefined };
    handler(clean);
    expect(clean.preventDefault).not.toHaveBeenCalled();

    api.commit();
    form.client = 2;
    const dirty = { preventDefault: jest.fn(), returnValue: undefined };
    handler(dirty);
    expect(dirty.preventDefault).toHaveBeenCalled();
    expect(dirty.returnValue).toBe('');

    addSpy.mockRestore();
  });

  it('unhooks the browser dialog when the page unmounts', () => {
    const removeSpy = jest.spyOn(window, 'removeEventListener');
    const { wrapper } = setup();

    wrapper.unmount();

    expect(removeSpy.mock.calls.some(([name]) => name === 'beforeunload')).toBe(true);
    removeSpy.mockRestore();
  });
});

describe('useUnsavedGuard — confirm modal ownership', () => {
  it('uses the injected requestConfirm without creating a second modal state', () => {
    const { api } = setup();
    // Un confirmState propio abriría un modal que la página no renderiza.
    expect(api.confirmState).toBeUndefined();
  });

  it('mounts its own modal state when the page injects nothing', () => {
    const { defineComponent } = require('vue');
    const { mount } = require('@vue/test-utils');
    const { useUnsavedGuard } = require('~/composables/useUnsavedGuard');

    let api = null;
    mount(defineComponent({
      setup() {
        api = useUnsavedGuard({ snapshot: () => ({ title: 'A' }), labels: { title: 'título' } });
        return () => null;
      },
    }));

    expect(api.confirmState.value.open).toBe(false);
    expect(typeof api.handleSecondaryAction).toBe('function');
  });
});
