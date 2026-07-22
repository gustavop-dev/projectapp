import { mount } from '@vue/test-utils';

import DiagnosticStatusBadge from '../../components/WebAppDiagnostic/DiagnosticStatusBadge.vue';

describe('DiagnosticStatusBadge', () => {
  it('renders the label of a known status', () => {
    const wrapper = mount(DiagnosticStatusBadge, { props: { status: 'negotiating' } });
    expect(wrapper.text()).toBe('En negociación');
  });

  it('applies the status class of a known status', () => {
    const wrapper = mount(DiagnosticStatusBadge, { props: { status: 'rejected' } });
    expect(wrapper.classes()).toContain('bg-danger-soft');
  });

  it('falls back to the raw status text for unknown statuses', () => {
    const wrapper = mount(DiagnosticStatusBadge, { props: { status: 'limbo' } });
    expect(wrapper.text()).toBe('limbo');
    expect(wrapper.classes()).toContain('bg-surface-raised');
  });
});
