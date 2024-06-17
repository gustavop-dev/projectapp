import { defineStore } from 'pinia'
import { get_request } from "./services/request_http";

export const useWebDesignsStore = defineStore("web-designs",{
  state: () => ({
    designs: [],
    areUpdateDesigns: false,
  }),
  getters: {
    getDesigns: (state) => {
      return state.designs;
    },
  },
  actions: {
    async init() {
      if (!this.areUpdateDesigns) await this.fetchDesignsData();
    },

    async fetchDesignsData() {
      if (this.areUpdateDesigns) return;

      let response = await get_request("api/web-designs/");
      let jsonData = response.data;

      if (jsonData && typeof jsonData === "string") {
        try {
          jsonData = JSON.parse(jsonData);
        } catch (error) {
          console.error(error.message);
          jsonData = [];
        }
      }

      this.designs = jsonData ?? [];
      this.areUpdateDesigns = true;
    }

  }
})