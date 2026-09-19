import { defineStore } from 'pinia';
import { get_request, create_request } from './services/request_http';

export const useProposalFormalizationStore = defineStore('proposal-formalization', {
  state: () => ({}),
  actions: {
    async options(proposalId) {
      return (await get_request(`proposals/${proposalId}/formalization/`)).data;
    },
    async prepare(proposalId, payload) {
      return (await create_request(`proposals/${proposalId}/formalization/prepare/`, payload)).data;
    },
    async send(proposalId, preparationId) {
      return (await create_request(`proposals/${proposalId}/formalization/preparations/${preparationId}/send/`, {})).data;
    },
    async detail(proposalId, preparationId) {
      return (await get_request(`proposals/${proposalId}/formalization/preparations/${preparationId}/`)).data;
    },
    async file(url) {
      return (await get_request(url.replace(/^\/api\//, ''), { responseType: 'blob' })).data;
    },
  },
});
