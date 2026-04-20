import { create_request } from '~/stores/services/request_http';

export function trackRequirementClick(proposalUuid, group) {
  if (!proposalUuid || typeof window === 'undefined') return;
  const isPreview = new URLSearchParams(window.location.search).get('preview') === '1';
  if (isPreview) return;
  create_request(`proposals/${proposalUuid}/track-requirement-click/`, {
    group_id: group?.id,
    group_title: group?.title,
  }).catch(() => {});
}
