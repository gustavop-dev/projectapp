import { mount } from '@vue/test-utils';
import TimelineSection from '../../components/WebAppDiagnostic/public/TimelineSection.vue';

const BASE_CONTENT = {
  index: '07',
  title: 'Cronograma',
  intro: 'Así se distribuirá el trabajo.',
  distributionTitle: 'Distribución por días',
  distribution: [
    { dayRange: 'Día 1', description: 'Kickoff y acceso a credenciales.' },
    { dayRange: 'Día 2', description: 'Radiografía técnica.' },
    { dayRange: 'Día 3', description: 'Evaluación de categorías.' },
    { dayRange: 'Día 4', description: 'Reporte ejecutivo.' },
    { dayRange: 'Día 5', description: 'Entrega final.' },
  ],
};

function mountTimeline(overrides = {}) {
  return mount(TimelineSection, {
    props: {
      content: { ...BASE_CONTENT, ...overrides.content },
      diagnostic: { duration_label: '5 días hábiles', ...overrides.diagnostic },
    },
  });
}

describe('WebAppDiagnostic / public / TimelineSection', () => {
  it('renders one item per distribution entry with its number and label', () => {
    const wrapper = mountTimeline();
    const items = wrapper.findAll('li');
    expect(items).toHaveLength(5);

    items.forEach((li, idx) => {
      expect(li.text()).toContain(String(idx + 1));
      expect(li.text()).toContain(BASE_CONTENT.distribution[idx].dayRange);
      expect(li.text()).toContain(BASE_CONTENT.distribution[idx].description);
    });
  });

  it('renders the duration label from the diagnostic prop', () => {
    const wrapper = mountTimeline();
    expect(wrapper.text()).toContain('5 días hábiles');
  });

  it('uses a flex layout for items so the badge does not overlap the content', () => {
    const wrapper = mountTimeline();
    const items = wrapper.findAll('li');
    items.forEach((li) => {
      expect(li.classes()).toContain('flex');
      expect(li.classes()).toContain('items-start');
      const badge = li.find('span');
      expect(badge.classes()).toContain('flex-none');
      // The badge must not be absolutely positioned (old bug).
      expect(badge.classes()).not.toContain('absolute');
    });
  });
});
