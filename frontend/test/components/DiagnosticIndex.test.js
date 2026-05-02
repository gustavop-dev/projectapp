import { mount } from '@vue/test-utils';
import DiagnosticIndex from '../../components/WebAppDiagnostic/public/DiagnosticIndex.vue';

const SECTIONS = [
  { id: 1, title: 'Propósito' },
  { id: 2, title: 'Radiografía' },
  { id: 3, title: 'Categorías Evaluadas' },
];

function mountIndex(props = {}) {
  return mount(DiagnosticIndex, {
    props: {
      sections: SECTIONS,
      currentIndex: 0,
      visitedIds: new Set(),
      ...props,
    },
  });
}

describe('DiagnosticIndex', () => {
  it('renders the toggle button', () => {
    const wrapper = mountIndex();
    expect(wrapper.find('[data-testid="diagnostic-index-toggle"]').exists()).toBe(true);
  });

  it('panel is closed on mount (no pointer events)', () => {
    const wrapper = mountIndex();
    const panel = wrapper.find('[data-testid="diagnostic-index-panel"]');
    expect(panel.classes()).toContain('pointer-events-none');
  });

  it('toggle click opens the panel', async () => {
    const wrapper = mountIndex();
    await wrapper.find('[data-testid="diagnostic-index-toggle"]').trigger('click');
    const panel = wrapper.find('[data-testid="diagnostic-index-panel"]');
    expect(panel.classes()).toContain('pointer-events-auto');
    expect(panel.classes()).not.toContain('pointer-events-none');
  });

  it('second toggle click closes the panel again', async () => {
    const wrapper = mountIndex();
    const toggle = wrapper.find('[data-testid="diagnostic-index-toggle"]');
    await toggle.trigger('click');
    await toggle.trigger('click');
    const panel = wrapper.find('[data-testid="diagnostic-index-panel"]');
    expect(panel.classes()).toContain('pointer-events-none');
  });

  it('renders a button for each section with its title', () => {
    const wrapper = mountIndex();
    const buttons = wrapper.findAll('[data-testid="diagnostic-index-panel"] li button');
    expect(buttons).toHaveLength(SECTIONS.length);
    expect(buttons[0].text()).toContain('Propósito');
    expect(buttons[1].text()).toContain('Radiografía');
    expect(buttons[2].text()).toContain('Categorías Evaluadas');
  });

  it('emits navigate with the correct index when a section button is clicked', async () => {
    const wrapper = mountIndex();
    await wrapper.find('[data-testid="diagnostic-index-toggle"]').trigger('click');
    const buttons = wrapper.findAll('[data-testid="diagnostic-index-panel"] li button');
    await buttons[1].trigger('click');
    expect(wrapper.emitted('navigate')).toEqual([[1]]);
  });

  it('closes the panel after clicking a section button', async () => {
    const wrapper = mountIndex();
    await wrapper.find('[data-testid="diagnostic-index-toggle"]').trigger('click');
    const buttons = wrapper.findAll('[data-testid="diagnostic-index-panel"] li button');
    await buttons[0].trigger('click');
    expect(wrapper.find('[data-testid="diagnostic-index-panel"]').classes()).toContain('pointer-events-none');
  });

  it('highlights the current section button', () => {
    const wrapper = mountIndex({ currentIndex: 1 });
    const buttons = wrapper.findAll('[data-testid="diagnostic-index-panel"] li button');
    expect(buttons[1].classes()).toContain('bg-primary/5');
    expect(buttons[0].classes()).not.toContain('bg-primary/5');
  });

  it('shows a checkmark badge for a visited section that is not current', () => {
    const wrapper = mountIndex({ currentIndex: 0, visitedIds: new Set([2]) });
    const visitedBadge = wrapper.findAll('[data-testid="diagnostic-index-panel"] li')[1].find('span');
    expect(visitedBadge.find('svg').exists()).toBe(true);
  });

  it('shows the section number in the badge for the current section even if visited', () => {
    const wrapper = mountIndex({ currentIndex: 1, visitedIds: new Set([2]) });
    // Section id=2 (index 1) is both current AND visited — should show the number, not checkmark
    const currentBadge = wrapper.findAll('[data-testid="diagnostic-index-panel"] li')[1].find('span');
    expect(currentBadge.find('svg').exists()).toBe(false);
    expect(currentBadge.text()).toContain('2');
  });
});
