import { defineStore } from 'pinia';
import { get_request, create_request } from '~/stores/services/request_http';

const base = (type, id) => `entity-history/${type}/${id}/`;

// History data belongs to each mounted viewer, never to a shared current entity.
// In particular, revealed secrets are not kept in Pinia or browser storage.
export const useEntityHistoryStore = defineStore('entity_history', {
  state: () => ({}),
  actions: {
    async list(type, id, page = 1, order = 'recent') {
      return (await get_request(`${base(type, id)}?page=${page}&order=${order}`)).data;
    },
    async version(type, id, revision) {
      return (await get_request(`${base(type, id)}versions/${revision}/`)).data;
    },
    async compare(type, id, from, to) {
      return (await get_request(`${base(type, id)}compare/?from=${from}&to=${to}`)).data;
    },
    async reveal(type, id, revision, field) {
      return (await create_request(`${base(type, id)}versions/${revision}/reveal/`, { field })).data;
    },
  },
});
