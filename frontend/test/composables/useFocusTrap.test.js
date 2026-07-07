/**
 * Tests for the useFocusTrap composable.
 *
 * Covers: initial focus priority (initialFocus > [data-autofocus] >
 * container), Tab/Shift+Tab wrapping, focus restoration on deactivate,
 * and inertness while inactive.
 */
import { mount } from '@vue/test-utils';
import { defineComponent, nextTick, ref } from 'vue';
import { useFocusTrap } from '../../composables/useFocusTrap';

function makeHarness({ initialFocus = null, content = '' } = {}) {
  return defineComponent({
    template: `
      <div>
        <button id="outside" type="button">fuera</button>
        <div ref="container" tabindex="-1" id="container">${content}</div>
      </div>
    `,
    setup() {
      const container = ref(null);
      const active = ref(false);
      useFocusTrap(container, { active, initialFocus });
      return { container, active };
    },
  });
}

async function mountHarness(options) {
  document.body.innerHTML = '';
  const wrapper = mount(makeHarness(options), { attachTo: document.body });
  await nextTick();
  return wrapper;
}

async function activate(wrapper) {
  wrapper.vm.active = true;
  await nextTick();
  await nextTick();
}

function pressTab(target, { shiftKey = false } = {}) {
  const event = new KeyboardEvent('keydown', {
    key: 'Tab',
    shiftKey,
    bubbles: true,
    cancelable: true,
  });
  target.dispatchEvent(event);
  return event;
}

describe('useFocusTrap', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('focuses the first [data-autofocus] descendant on activation', async () => {
    const wrapper = await mountHarness({
      content: '<button id="b1" type="button">1</button><button id="b2" data-autofocus type="button">2</button>',
    });
    document.getElementById('outside').focus();

    await activate(wrapper);

    expect(document.activeElement.id).toBe('b2');
    wrapper.unmount();
  });

  it('prefers the initialFocus() target over [data-autofocus]', async () => {
    const wrapper = await mountHarness({
      initialFocus: () => document.getElementById('b1'),
      content: '<button id="b1" type="button">1</button><button id="b2" data-autofocus type="button">2</button>',
    });

    await activate(wrapper);

    expect(document.activeElement.id).toBe('b1');
    wrapper.unmount();
  });

  it('falls back to the container itself when there are no focusables', async () => {
    const wrapper = await mountHarness({ content: '<p>solo texto</p>' });

    await activate(wrapper);

    expect(document.activeElement.id).toBe('container');
    wrapper.unmount();
  });

  it('wraps Tab from the last focusable to the first', async () => {
    const wrapper = await mountHarness({
      content: '<button id="b1" type="button">1</button><button id="b2" type="button">2</button>',
    });
    await activate(wrapper);

    const last = document.getElementById('b2');
    last.focus();
    const event = pressTab(last);

    expect(event.defaultPrevented).toBe(true);
    expect(document.activeElement.id).toBe('b1');
    wrapper.unmount();
  });

  it('wraps Shift+Tab from the first focusable to the last', async () => {
    const wrapper = await mountHarness({
      content: '<button id="b1" type="button">1</button><button id="b2" type="button">2</button>',
    });
    await activate(wrapper);

    const first = document.getElementById('b1');
    first.focus();
    const event = pressTab(first, { shiftKey: true });

    expect(event.defaultPrevented).toBe(true);
    expect(document.activeElement.id).toBe('b2');
    wrapper.unmount();
  });

  it('restores focus to the previously focused element on deactivation', async () => {
    const wrapper = await mountHarness({
      content: '<button id="b1" type="button">1</button>',
    });
    document.getElementById('outside').focus();
    await activate(wrapper);
    expect(document.activeElement.id).toBe('container');

    wrapper.vm.active = false;
    await nextTick();

    expect(document.activeElement.id).toBe('outside');
    wrapper.unmount();
  });

  it('does nothing while inactive', async () => {
    const wrapper = await mountHarness({
      content: '<button id="b1" type="button">1</button>',
    });
    const outside = document.getElementById('outside');
    outside.focus();
    await nextTick();

    expect(document.activeElement.id).toBe('outside');
    const event = pressTab(outside);
    expect(event.defaultPrevented).toBe(false);
    wrapper.unmount();
  });
});
