/**
 * Tests for PanelNotificationHost — renders the usePanelNotify queue and wires
 * up the action button (handler or router link) and the close button.
 */

import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';

const mockRouterPush = jest.fn();
jest.mock('vue-router', () => ({
  useRouter: () => ({ push: mockRouterPush }),
}));

import PanelNotificationHost from '../../components/panel/PanelNotificationHost.vue';
import { usePanelNotify } from '../../composables/usePanelNotify';

function mountHost() {
  return mount(PanelNotificationHost, {
    global: { stubs: { teleport: true } },
  });
}

describe('PanelNotificationHost', () => {
  let notify;

  beforeEach(() => {
    mockRouterPush.mockClear();
    notify = usePanelNotify();
    notify.clearAll();
  });

  afterEach(() => {
    notify.clearAll();
  });

  it('renders title and detail of a queued notification', async () => {
    const wrapper = mountHost();
    notify.error({ title: 'No se pudo enviar', detail: 'Falta el correo del cliente.', duration: 0 });
    await nextTick();

    const alerts = wrapper.findAll('[role="alert"]');
    expect(alerts).toHaveLength(1);
    expect(wrapper.text()).toContain('No se pudo enviar');
    expect(wrapper.text()).toContain('Falta el correo del cliente.');
  });

  it('renders an action button and runs its handler, then dismisses', async () => {
    const wrapper = mountHost();
    const handler = jest.fn();
    notify.error({ title: 'Correo falló', action: { label: 'Reenviar', handler }, duration: 0 });
    await nextTick();

    const actionBtn = wrapper.findAll('button').find((b) => b.text() === 'Reenviar');
    expect(actionBtn).toBeTruthy();
    await actionBtn.trigger('click');

    expect(handler).toHaveBeenCalledTimes(1);
    expect(notify.notifications.value).toHaveLength(0);
  });

  it('navigates with the router when the action has a `to`', async () => {
    const wrapper = mountHost();
    notify.error({ title: 'Falta correo', action: { label: 'Editar propuesta', to: '/panel/proposals/103/edit' }, duration: 0 });
    await nextTick();

    const actionBtn = wrapper.findAll('button').find((b) => b.text() === 'Editar propuesta');
    await actionBtn.trigger('click');

    expect(mockRouterPush).toHaveBeenCalledWith('/panel/proposals/103/edit');
    expect(notify.notifications.value).toHaveLength(0);
  });

  it('dismisses a notification via the close button', async () => {
    const wrapper = mountHost();
    notify.success({ title: 'Guardado', duration: 0 });
    await nextTick();

    const closeBtn = wrapper.find('[aria-label="Cerrar"]');
    await closeBtn.trigger('click');

    expect(notify.notifications.value).toHaveLength(0);
  });

  it('stacks multiple notifications', async () => {
    const wrapper = mountHost();
    notify.info({ title: 'uno', duration: 0 });
    notify.info({ title: 'dos', duration: 0 });
    await nextTick();

    expect(wrapper.findAll('[role="alert"]')).toHaveLength(2);
  });
});
