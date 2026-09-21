import { mount, flushPromises } from '@vue/test-utils';
import { reactive } from 'vue';
import LinktreeCard from '~/components/Linktree/LinktreeCard.vue';
import LinktreeAppearance from '~/components/panel/linktrees/LinktreeAppearance.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseSelect from '~/components/base/BaseSelect.vue';
import { LINKTREE_DEFAULTS } from '~/utils/linktreeTheme';

const tree = (overrides = {}) => ({ ...LINKTREE_DEFAULTS, kind: 'personal', display_name: 'Brand Test', show_brand_header: true, buttons: [], ...overrides });
const appearance = (form) => mount(LinktreeAppearance, {
  props: { form, 'onUpdate-field': (key, value) => { form[key] = value; } },
  global: { components: { BaseInput, BaseSelect }, stubs: {
    BaseFormField: { template: '<div><slot />{{ error }}</div>', props: ['error'] },
    BaseFormRow: { template: '<div><slot /></div>' },
    BaseButton: { template: '<button><slot /></button>' },
  } },
});
const originalFetch = global.fetch;
afterEach(() => { global.fetch = originalFetch; });

test('logo replaces wordmark while preserving the personal avatar', () => {
  const wrapper = mount(LinktreeCard, { props: { tree: tree({ logo: '/logo.png', avatar: '/photo.png' }) } });
  expect(wrapper.get('[data-testid="linktree-brand-logo"]').attributes('src')).toBe('/logo.png');
  expect(wrapper.get('img.lt-avatar__photo').attributes('src')).toBe('/photo.png');
  expect(wrapper.text()).not.toContain('ProjectApp.');
});

test('company logo follows the header visibility control', async () => {
  const wrapper = mount(LinktreeCard, { props: { tree: tree({ kind: 'company', logo: '/logo.png' }) } });
  expect(wrapper.get('[data-testid="linktree-brand-logo"]').attributes('src')).toBe('/logo.png');
  await wrapper.setProps({ tree: tree({ kind: 'company', logo: '/logo.png', show_brand_header: false }) });
  expect(wrapper.find('[data-testid="linktree-brand-logo"]').exists()).toBe(false);
});

test('preview updates its palette and font when branding changes', async () => {
  const wrapper = mount(LinktreeCard, { props: { tree: tree() } });
  await wrapper.setProps({ tree: tree({ accent_color: '#aabbcc', font_family: 'Lora' }) });
  expect(wrapper.element.style.getPropertyValue('--lt-accent')).toBe('#aabbcc');
  expect(wrapper.element.style.getPropertyValue('--lt-font')).toContain('Lora');
});

test('custom Google family is selectable after loading', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: true, text: async () => '@font-face {font-family:Lora;}' });
  const wrapper = appearance(reactive(tree()));
  await wrapper.get('#lt-google-font').setValue('Lora');
  await wrapper.get('#lt-google-font').trigger('keydown.enter');
  await flushPromises();
  expect(wrapper.get('#lt-font').element.value).toBe('Lora');
  expect(wrapper.text()).toContain('Lora cargada');
});

test('unavailable family leaves the selected font unchanged', async () => {
  global.fetch = jest.fn().mockResolvedValue({ ok: false });
  const wrapper = appearance(reactive(tree()));
  await wrapper.get('#lt-google-font').setValue('Missing Family');
  await wrapper.get('#lt-google-font').trigger('keydown.enter');
  await flushPromises();
  expect(wrapper.text()).toContain('No se encontró esa familia');
  expect(wrapper.get('#lt-font').element.value).toBe('Ubuntu');
});

test('Google connection failure lets the user retry without losing the selection', async () => {
  global.fetch = jest.fn().mockRejectedValue(new Error('offline'));
  const wrapper = appearance(reactive(tree()));
  await wrapper.get('#lt-google-font').setValue('Lora');
  await wrapper.get('#lt-google-font').trigger('keydown.enter');
  await flushPromises();
  expect(wrapper.text()).toContain('No se pudo conectar');
  expect(wrapper.get('#lt-font').element.value).toBe('Ubuntu');
});
