import { defineStore } from 'pinia';
import { get_request, create_request, delete_request } from './services/request_http';

export const useLinktreeTemplatesStore = defineStore('linktree-templates', {
  state: () => ({ treeId: null, templates: [], versions: [], activeVersionId: null, nextOffset: null, canShare: false, busy: false }),
  actions: {
    async load(treeId, offset = 0) {
      if (this.treeId !== treeId) { this.$reset(); this.treeId = treeId; }
      const response = await get_request(`linktrees/admin/${treeId}/templates/?offset=${offset}`);
      const data = response.data;
      if (this.treeId !== treeId) return data;
      this.templates = data.templates || [];
      this.versions = offset ? [...this.versions, ...(data.versions || [])] : (data.versions || []);
      this.activeVersionId = data.active_version_id;
      this.canShare = data.can_share;
      this.nextOffset = data.next_offset;
      return data;
    },
    async mutate(treeId, suffix, payload = {}, method = 'POST') {
      this.busy = true;
      try {
        const path = `linktrees/admin/${treeId}/templates/${suffix}`;
        const response = method === 'DELETE' ? await delete_request(path) : await create_request(path, payload);
        if (this.treeId === treeId) await this.load(treeId);
        return response.data;
      } finally {
        this.busy = false;
      }
    },
  },
});
