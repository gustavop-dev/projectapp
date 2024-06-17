import { defineStore } from 'pinia';
import { get_request } from "./services/request_http";

export const useWebDevelopmentsStore = defineStore("web-developments", {
  state: () => ({
    developments: [],
    areUpdateDevelopments: false,
  }),
  getters: {
    getDevelopments: (state) => {
      return state.developments;
    },
    getExamplesById: (state) => (developmentId, sectionId, componentId) => {
        const development = state.developments.find(dev => dev.id === parseInt(developmentId));
        if (!development) return null;
  
        const section = development.sections.find(sec => sec.id === parseInt(sectionId));
        if (!section) return null;
  
        const component = section.components.find(comp => comp.id === parseInt(componentId));
        if (!component) return null;
  
        return {
          development: {
            title_en: development.title_en,
            title_es: development.title_es,
          },
          section: {
            title_en: section.title_en,
            title_es: section.title_es,
          },
          component: {
            title_en: component.title_en,
            title_es: component.title_es,
          },
          examples: component.examples
        };
    },
  },
  actions: {
    async init() {
      if (!this.areUpdateDevelopments) await this.fetchDevelopmentsData();
    },

    async fetchDevelopmentsData() {
      if (this.areUpdateDevelopments) return;

      let response = await get_request("api/categories-development/");
      let jsonData = response.data;

      if (jsonData && typeof jsonData === "string") {
        try {
          jsonData = JSON.parse(jsonData);
        } catch (error) {
          console.error(error.message);
          jsonData = [];
        }
      }

      this.developments = jsonData ?? [];
      this.areUpdateDevelopments = true;
    }
  }
});
