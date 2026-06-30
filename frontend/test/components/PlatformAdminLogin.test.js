global.definePageMeta = jest.fn();
global.useHead = jest.fn();
global.useLocalePath = () => (path) => path;

let mockQuery = {};
global.useRoute = () => ({ query: mockQuery, path: '/platform/admin-login' });
global.navigateTo = jest.fn();

const mockAuthStore = {
  applyAuthenticatedSession: jest.fn(),
  fetchMe: jest.fn(),
};

jest.mock('../../stores/platform-auth', () => ({
  usePlatformAuthStore: () => mockAuthStore,
}));

import { mount, flushPromises } from '@vue/test-utils';
import AdminLogin from '../../pages/platform/admin-login.vue';

describe('platform/admin-login page', () => {
  beforeEach(() => {
    mockQuery = {};
    global.navigateTo.mockReset();
    mockAuthStore.applyAuthenticatedSession.mockReset();
    mockAuthStore.fetchMe.mockReset().mockResolvedValue({ success: true });
  });

  it('redirects to login when tokens are missing', async () => {
    mockQuery = {};
    mount(AdminLogin);
    await flushPromises();
    expect(mockAuthStore.applyAuthenticatedSession).not.toHaveBeenCalled();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/login');
  });

  it('stores tokens, hydrates and lands on dashboard by default', async () => {
    mockQuery = { access: 'a', refresh: 'r' };
    mount(AdminLogin);
    await flushPromises();
    expect(mockAuthStore.applyAuthenticatedSession).toHaveBeenCalledWith({ access: 'a', refresh: 'r' }, null);
    expect(mockAuthStore.fetchMe).toHaveBeenCalled();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/dashboard');
  });

  it('honors a platform redirect target', async () => {
    mockQuery = { access: 'a', refresh: 'r', redirect: '/platform/projects' };
    mount(AdminLogin);
    await flushPromises();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/projects');
  });

  it('ignores a non-platform redirect target', async () => {
    mockQuery = { access: 'a', refresh: 'r', redirect: 'https://evil.com' };
    mount(AdminLogin);
    await flushPromises();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/dashboard');
  });

  it('falls back to login when hydration fails', async () => {
    mockQuery = { access: 'a', refresh: 'r' };
    mockAuthStore.fetchMe.mockResolvedValue({ success: false });
    mount(AdminLogin);
    await flushPromises();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/login');
  });
});
