global.definePageMeta = jest.fn();
global.useHead = jest.fn();
global.useLocalePath = () => (path) => path;

let mockQuery = {};
global.useRoute = () => ({ query: mockQuery, path: '/platform/admin-login' });
global.navigateTo = jest.fn();

const mockAuthStore = {
  exchangeImpersonationCode: jest.fn(),
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
    mockAuthStore.exchangeImpersonationCode.mockReset().mockResolvedValue({ success: true });
    mockAuthStore.fetchMe.mockReset().mockResolvedValue({ success: true });
  });

  it('redirects to login when the code is missing', async () => {
    mockQuery = {};
    mount(AdminLogin);
    await flushPromises();
    expect(mockAuthStore.exchangeImpersonationCode).not.toHaveBeenCalled();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/login');
  });

  it('exchanges the code, hydrates and lands on dashboard by default', async () => {
    mockQuery = { code: 'abc' };
    mount(AdminLogin);
    await flushPromises();
    expect(mockAuthStore.exchangeImpersonationCode).toHaveBeenCalledWith('abc');
    expect(mockAuthStore.fetchMe).toHaveBeenCalled();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/dashboard');
  });

  it('honors a platform redirect target', async () => {
    mockQuery = { code: 'abc', redirect: '/platform/projects' };
    mount(AdminLogin);
    await flushPromises();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/projects');
  });

  it('ignores a non-platform redirect target', async () => {
    mockQuery = { code: 'abc', redirect: 'https://evil.com' };
    mount(AdminLogin);
    await flushPromises();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/dashboard');
  });

  it('falls back to login when the exchange fails', async () => {
    mockQuery = { code: 'abc' };
    mockAuthStore.exchangeImpersonationCode.mockResolvedValue({ success: false });
    mount(AdminLogin);
    await flushPromises();
    expect(mockAuthStore.fetchMe).not.toHaveBeenCalled();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/login');
  });

  it('falls back to login when hydration fails', async () => {
    mockQuery = { code: 'abc' };
    mockAuthStore.fetchMe.mockResolvedValue({ success: false });
    mount(AdminLogin);
    await flushPromises();
    expect(global.navigateTo).toHaveBeenCalledWith('/platform/login');
  });
});
