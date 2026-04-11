import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import ExpirationBadge from '../../components/BusinessProposal/ExpirationBadge.vue';

jest.mock('../../composables/useExpirationTimer', () => ({
  useExpirationTimer: jest.fn(),
}));

const { useExpirationTimer } = require('../../composables/useExpirationTimer');

function setTimer({ isExpired = false, urgencyLevel = 'safe', countdown = '5 días' } = {}) {
  useExpirationTimer.mockReturnValue({
    isExpired: ref(isExpired),
    urgencyLevel: ref(urgencyLevel),
    formattedCountdown: ref(countdown),
  });
}

beforeEach(() => setTimer());

function mountBadge(props = {}) {
  return mount(ExpirationBadge, {
    props: { expiresAt: '2026-05-01T00:00:00Z', ...props },
  });
}

describe('ExpirationBadge', () => {
  it('renders the urgent full-width banner when urgencyLevel is urgent', () => {
    setTimer({ urgencyLevel: 'urgent' });
    const wrapper = mountBadge();

    const banner = wrapper.find('.expiration-badge.fixed.top-0');
    expect(banner.exists()).toBe(true);
  });

  it('applies red background class to the banner when urgencyLevel is urgent', () => {
    setTimer({ urgencyLevel: 'urgent' });
    const wrapper = mountBadge();

    expect(wrapper.find('.expiration-badge').classes()).toContain('bg-red-600');
  });

  it('renders the pill badge with orange classes when urgencyLevel is warning', () => {
    setTimer({ urgencyLevel: 'warning' });
    const wrapper = mountBadge();

    const badge = wrapper.find('.expiration-badge.rounded-full');
    expect(badge.exists()).toBe(true);
    expect(badge.classes()).toContain('bg-orange-50/90');
  });

  it('renders the pill badge with yellow classes when urgencyLevel is notice', () => {
    setTimer({ urgencyLevel: 'notice' });
    const wrapper = mountBadge();

    const badge = wrapper.find('.expiration-badge.rounded-full');
    expect(badge.exists()).toBe(true);
    expect(badge.classes()).toContain('bg-yellow-50/90');
  });

  it('renders the pill badge with emerald classes when urgencyLevel is safe', () => {
    setTimer({ urgencyLevel: 'safe' });
    const wrapper = mountBadge();

    const badge = wrapper.find('.expiration-badge.rounded-full');
    expect(badge.exists()).toBe(true);
    expect(badge.classes()).toContain('bg-emerald-50/90');
  });

  it('renders nothing when isExpired is true', () => {
    setTimer({ isExpired: true });
    const wrapper = mountBadge();

    expect(wrapper.find('.expiration-badge').exists()).toBe(false);
  });
});
