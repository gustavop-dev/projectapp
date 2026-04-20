// Only redirect on explicit 401/403 so transient 5xx / network errors don't
// boot a logged-in staff user out of the panel.
export default defineNuxtRouteMiddleware(async (to) => {
  if (!to.path.includes('/panel')) return;
  if (to.path.endsWith('/panel/login')) return;
  if (import.meta.server) return;

  const { useProposalStore } = await import('~/stores/proposals');
  const result = await useProposalStore().checkAdminAuth();

  if (result.success) return;
  if (result.status === 401 || result.status === 403) {
    window.location.href = `/admin/login/?next=${to.fullPath}`;
    return abortNavigation();
  }
});
