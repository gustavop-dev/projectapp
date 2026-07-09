/**
 * Tests for ProposalStatusSelect (badge-styled admin status select).
 *
 * Covers: current status option, natural vs forced optgroups, change
 * emission with snap-back, and the updating spinner/disabled state.
 */

import { mount } from '@vue/test-utils';
import ProposalStatusSelect from '../../components/panel/proposal/ProposalStatusSelect.vue';

function factory(proposal = {}, props = {}) {
  return mount(ProposalStatusSelect, {
    props: {
      proposal: {
        id: 1,
        status: 'sent',
        available_transitions: ['negotiating', 'rejected'],
        ...proposal,
      },
      ...props,
    },
  });
}

describe('ProposalStatusSelect', () => {
  it('renders the current status as a disabled selected option', () => {
    const wrapper = factory();
    const current = wrapper.find('option[disabled]');
    expect(current.text()).toBe('Enviada');
    expect(wrapper.find('select').element.value).toBe('sent');
  });

  it('groups natural transitions under "Flujo normal"', () => {
    const wrapper = factory();
    const natural = wrapper.find('optgroup[label="Flujo normal"]');
    expect(natural.exists()).toBe(true);
    expect(natural.findAll('option').map((o) => o.element.value)).toEqual([
      'negotiating', 'rejected',
    ]);
  });

  it('groups the remaining statuses under "Forzar estado" excluding the current one', () => {
    const wrapper = factory();
    const forced = wrapper.find('optgroup[label="Forzar estado"]');
    const values = forced.findAll('option').map((o) => o.element.value);
    expect(values).toEqual(['draft', 'viewed', 'accepted', 'finished', 'expired']);
    expect(values).not.toContain('sent');
  });

  it('omits the "Flujo normal" group for terminal statuses', () => {
    const wrapper = factory({ status: 'finished', available_transitions: [] });
    expect(wrapper.find('optgroup[label="Flujo normal"]').exists()).toBe(false);
    expect(wrapper.find('optgroup[label="Forzar estado"]').exists()).toBe(true);
  });

  it('emits change with the picked status and snaps the select back', async () => {
    const wrapper = factory();
    const select = wrapper.find('select');
    await select.setValue('accepted');

    expect(wrapper.emitted('change')).toEqual([['accepted']]);
    expect(select.element.value).toBe('sent');
  });

  it('disables the select and shows the spinner while updating', () => {
    const wrapper = factory({}, { updating: true });
    expect(wrapper.find('select').element.disabled).toBe(true);
    expect(wrapper.find('svg.animate-spin').exists()).toBe(true);
  });
});
