/**
 * CommercialConditionsForm — hour-packages source switch (auto/manual).
 * Auto disables the catalog-owned fields; manual enables editing, the
 * apply-to-all action and the per-package pricing preview.
 */
import { reactive } from 'vue';
import { mount } from '@vue/test-utils';
import CommercialConditionsForm from '../../components/BusinessProposal/admin/section-forms/CommercialConditionsForm.vue';
import { buildFormFromJson } from '../../components/BusinessProposal/admin/sectionEditorUtils.js';

const BASE_JSON = {
  index: '17',
  title: 'Condiciones comerciales',
  packagesTitle: 'Paquetes',
  packagesIntro: 'intro',
  hourlyRate: 40,
  currency: 'USD',
  packages: [
    { name: 'Pro', hours: 60, discountPercent: 10, note: 'x' },
    { name: 'Ágil', hours: 20, discountPercent: 0, note: 'y', hourlyRate: 45 },
  ],
  effortBadge: 'badge',
  scopeTitle: 'Alcance',
  scopeParagraphs: ['p1'],
};

function mountForm(jsonOverrides = {}) {
  const form = reactive(
    buildFormFromJson({ ...BASE_JSON, ...jsonOverrides }, 'commercial_conditions', {}),
  );
  const wrapper = mount(CommercialConditionsForm, {
    props: { form, proposalData: {} },
  });
  return { wrapper, form };
}

describe('CommercialConditionsForm hour-packages mode', () => {
  it('auto mode disables rate, currency and package inputs but keeps titles and scope editable', () => {
    const { wrapper } = mountForm();

    const disabledInputs = wrapper.findAll('input:disabled');
    expect(disabledInputs.length).toBeGreaterThanOrEqual(6);
    expect(wrapper.find('select').attributes('disabled')).toBeDefined();
    const addBtn = wrapper.findAll('button').find((b) => b.text().includes('+ Agregar paquete'));
    expect(addBtn.attributes('disabled')).toBeDefined();
    expect(wrapper.find('[data-testid="apply-base-rate-all"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="hour-packages-mode-hint"]').text()).toContain('catálogo');

    const titleInput = wrapper.findAll('input').find((i) => i.element.value === 'Condiciones comerciales');
    expect(titleInput.attributes('disabled')).toBeUndefined();
    const scopeTextarea = wrapper.findAll('textarea').find((t) => t.element.value.includes('p1'));
    expect(scopeTextarea.attributes('disabled')).toBeUndefined();
  });

  it('switching to Manual enables package editing and shows the apply-to-all button', async () => {
    const { wrapper, form } = mountForm();

    await wrapper.find('[data-testid="hour-packages-mode-manual"]').trigger('click');

    expect(form.hourPackagesMode).toBe('manual');
    expect(wrapper.findAll('input:disabled')).toHaveLength(0);
    expect(wrapper.find('select').attributes('disabled')).toBeUndefined();
    expect(wrapper.find('[data-testid="apply-base-rate-all"]').exists()).toBe(true);
  });

  it('apply-to-all clears every per-package hourlyRate so the base rate drives pricing', async () => {
    const { wrapper, form } = mountForm({ hourPackagesMode: 'manual' });
    expect(form.packages[1].hourlyRate).toBe(45);

    await wrapper.find('[data-testid="apply-base-rate-all"]').trigger('click');

    expect(form.packages.every((p) => p.hourlyRate === '')).toBe(true);
  });

  it('per-package preview computes effective rate and total with base-rate fallback', () => {
    const { wrapper } = mountForm({ hourPackagesMode: 'manual' });

    // Pro: no own rate → base 40 USD, 10% discount → 36/h, 60h → 2,160.
    const pro = wrapper.find('[data-testid="hour-package-preview-0"]').text();
    expect(pro).toContain('$36 USD/h');
    expect(pro).toContain('$2,160 USD');

    // Ágil: own rate 45, no discount → 45/h, 20h → 900.
    const agil = wrapper.find('[data-testid="hour-package-preview-1"]').text();
    expect(agil).toContain('$45 USD/h');
    expect(agil).toContain('$900 USD');
  });
});
