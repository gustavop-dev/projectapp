import{i as r,j as p}from"./index-BL9c-49D.js";const d=r("web-developments",{state:()=>({developments:[],areUpdateDevelopments:!1}),getters:{getDevelopments:s=>s.developments,getExamplesById:s=>(e,l,a)=>{const n=s.developments.find(t=>t.id===parseInt(e));if(!n)return null;const o=n.sections.find(t=>t.id===parseInt(l));if(!o)return null;const i=o.components.find(t=>t.id===parseInt(a));return i?{development:{title_en:n.title_en,title_es:n.title_es},section:{title_en:o.title_en,title_es:o.title_es},component:{title_en:i.title_en,title_es:i.title_es},examples:i.examples}:null}},actions:{async init(){this.areUpdateDevelopments||await this.fetchDevelopmentsData()},async fetchDevelopmentsData(){if(this.areUpdateDevelopments)return;let e=(await p("api/categories-development/")).data;if(e&&typeof e=="string")try{e=JSON.parse(e)}catch(l){console.error(l.message),e=[]}this.developments=e??[],this.areUpdateDevelopments=!0}}});export{d as u};