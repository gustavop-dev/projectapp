import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { defineComponent } from 'vue';

import { usePanelRefresh } from '../../composables/usePanelRefresh';
import { usePanelRefreshStore } from '../../stores/panel_refresh';

const HostComponent = defineComponent({
  props: { handler: { type: Function, required: true } },
  setup(props) {
    usePanelRefresh(props.handler);
    return () => null;
  },
});

describe('usePanelRefresh', () => {
  let pinia;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
  });

  it('registers the page handler on the refresh store', () => {
    const handler = jest.fn();
    mount(HostComponent, { props: { handler }, global: { plugins: [pinia] } });
    expect(usePanelRefreshStore().handler).toBe(handler);
  });

  it('unregisters the handler when the page unmounts', () => {
    const wrapper = mount(HostComponent, {
      props: { handler: jest.fn() },
      global: { plugins: [pinia] },
    });
    wrapper.unmount();
    expect(usePanelRefreshStore().hasHandler).toBe(false);
  });

  it('hands back the store so pages can trigger refreshes manually', () => {
    let returned;
    const Probe = defineComponent({
      setup() {
        returned = usePanelRefresh(jest.fn());
        return () => null;
      },
    });
    mount(Probe, { global: { plugins: [pinia] } });
    expect(returned).toBe(usePanelRefreshStore());
  });
});
