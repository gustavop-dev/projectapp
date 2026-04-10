import { mount } from '@vue/test-utils';

global.useLocalePath = jest.fn(() => (path) => path);

jest.mock('../../composables/useMessages', () => ({
  useMessages: jest.fn(() => ({
    messages: require('vue').ref({
      whatWeBuild: {
        title: '¿Qué desarrollamos?',
        subtitle: 'Tienes un equipo listo para tu proyecto.',
        web: {
          title: 'Diseño Web',
          description: 'Sitios que convierten visitantes en clientes.',
          items: ['Landing Pages', 'E-Commerce', 'Plataformas Web'],
          cta: 'Cotizar proyecto web',
        },
        apps: {
          title: 'Apps Móviles',
          description: 'Una app nativa ofrece velocidad.',
          items: ['iOS & Android', 'Flutter & React Native'],
          cta: 'Desarrollo de Apps',
          ctaQuote: 'Cotizar app',
        },
        software: {
          title: 'Software a la Medida',
          description: 'Automatiza procesos y escala tu operación.',
          items: ['CRMs & ERPs personalizados'],
          cta: 'Cotizar software',
        },
      },
    }),
  })),
}));

import WhatWeBuild from '../../components/home/WhatWeBuild.vue';

function mountWhatWeBuild() {
  return mount(WhatWeBuild, {
    global: {
      stubs: {
        BackgroundGradientAnimation: true,
        NuxtLink: { template: '<a v-bind="$attrs"><slot /></a>' },
        Transition: true,
      },
    },
  });
}

describe('WhatWeBuild', () => {
  it('renders the section element', () => {
    const wrapper = mountWhatWeBuild();

    expect(wrapper.find('section').exists()).toBe(true);
  });

  it('renders the section title', () => {
    const wrapper = mountWhatWeBuild();

    expect(wrapper.text()).toContain('¿Qué desarrollamos?');
  });

  it('renders 3 service tabs', () => {
    const wrapper = mountWhatWeBuild();

    expect(wrapper.findAll('.tab-btn')).toHaveLength(3);
  });

  it('renders the web tab content by default', () => {
    const wrapper = mountWhatWeBuild();

    expect(wrapper.text()).toContain('Sitios que convierten visitantes en clientes.');
  });

  it('activates apps tab on click', async () => {
    const wrapper = mountWhatWeBuild();

    const appTab = wrapper.findAll('.tab-btn')[1];
    await appTab.trigger('click');

    expect(wrapper.text()).toContain('Una app nativa ofrece velocidad.');
  });
});
