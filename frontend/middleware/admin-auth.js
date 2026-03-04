/**
 * Route middleware that checks if the current user is an authenticated
 * Django staff member via session/CSRF auth.
 *
 * Redirects to Django admin login if not authenticated.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  if (!to.path.startsWith('/panel')) return;

  // Skip for the login page itself
  if (to.path === '/panel/login') return;

  try {
    const { useProposalStore } = await import('~/stores/proposals');
    const proposalStore = useProposalStore();
    const result = await proposalStore.checkAdminAuth();

    if (!result.success) {
      if (import.meta.client) {
        window.location.href = `/admin/login/?next=${to.fullPath}`;
      }
      return abortNavigation();
    }
  } catch {
    if (import.meta.client) {
      window.location.href = `/admin/login/?next=${to.fullPath}`;
    }
    return abortNavigation();
  }
});
