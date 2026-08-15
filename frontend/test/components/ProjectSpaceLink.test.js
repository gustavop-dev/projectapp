/**
 * ProjectSpaceLink: the one-click jump from a panel reference of a project
 * to its platform space (PA-50).
 *
 * Covers the null-id contract ("Sin proyecto" cells must stay untouched),
 * the bridge call with the space URL, and the disabled state while the
 * bridge mints the JWT.
 */
import { ref } from 'vue';
import { mount } from '@vue/test-utils';
import ProjectSpaceLink from '../../components/panel/projects/ProjectSpaceLink.vue';

const mockGoToPlatform = jest.fn();
const mockIsBridging = ref(false);

jest.mock('../../composables/usePanelToPlatformBridge', () => ({
  usePanelToPlatformBridge: () => ({
    goToPlatform: mockGoToPlatform,
    isBridging: mockIsBridging,
  }),
}));

function mountLink(props = {}) {
  return mount(ProjectSpaceLink, {
    props,
    global: {
      stubs: {
        BaseButton: {
          props: ['variant', 'size', 'disabled', 'iconOnly'],
          emits: ['click'],
          template:
            '<button :disabled="disabled" @click="$emit(\'click\', $event)"><slot /></button>',
        },
      },
    },
  });
}

describe('ProjectSpaceLink', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsBridging.value = false;
  });

  it('renders nothing without a project id', () => {
    const wrapper = mountLink({ projectId: null, dataTestid: 'space-x' });

    expect(wrapper.find('button').exists()).toBe(false);
  });

  it('opens the space of exactly that project through the bridge', async () => {
    const wrapper = mountLink({ projectId: 42, dataTestid: 'space-42' });

    await wrapper.find('button').trigger('click');

    expect(mockGoToPlatform).toHaveBeenCalledWith('/platform/projects/42');
  });

  it('is disabled while the bridge is minting the session', () => {
    mockIsBridging.value = true;
    const wrapper = mountLink({ projectId: 42 });

    expect(wrapper.find('button').element.disabled).toBe(true);
  });
});
