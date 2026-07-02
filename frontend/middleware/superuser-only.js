// Guards superuser-only panel modules (accounting). Runs after admin-auth,
// which already populated proposalStore.adminUser via checkAdminAuth().
// Real enforcement lives in the backend (every accounting endpoint 403s
// for non-superusers); this only keeps the UI coherent.
export default defineNuxtRouteMiddleware(async () => {
  if (import.meta.server) return;

  const { useProposalStore } = await import('~/stores/proposals');
  const store = useProposalStore();

  if (!store.adminUser) {
    await store.checkAdminAuth();
  }
  if (!store.isSuperuser) {
    return navigateTo('/panel');
  }
});
