import { defineStore } from 'pinia';
import { get_request } from "./services/request_http";

export const useModels3dStore = defineStore("models-3d", {
  state: () => ({
    models3d: [],
    areUpdateModels3d: false,
  }),
  getters: {
    getModels3d: (state) => {
      return state.models3d;
    },
  },
  actions: {
    async init() {
      if (!this.areUpdateModels3d) {
        await this.fetchModels3dData();
      }
    },
    async fetchModels3dData() {
      if (this.areUpdateModels3d) return;
      try {
        let response = await get_request("api/models-3d/");
        let jsonData = response.data;
        if (jsonData && typeof jsonData === "string") {
          try {
            jsonData = JSON.parse(jsonData);
          } catch (error) {
            console.error(error.message);
            jsonData = [];
          }
        }
        this.models3d = jsonData ?? [];
        this.areUpdateModels3d = true;
      } catch (error) {
        console.error('Error fetching 3D models:', error);
      }
    }
  }
});
