import{u as x}from"./web-developments-D2-3zOws.js";import{r as g,u as f,o as v,a as s,c as l,b as e,d as a,F as d,e as r,_ as b,t as n,f as w}from"./index-BL9c-49D.js";import k from"./Dune-CJvCoGzK.js";const y={class:"fixed top-0 left-0 w-full z-50"},D={class:"p-3 h-screen"},S={class:"w-full h-full grid grid-cols-2 rounded-xl overflow-hidden"},B=e("div",{class:"flex items-center bg-lemon px-16"},[e("h1",null,[e("span",{class:"text-6xl font-light text-esmerald"},"We prepare more than 500 web components only for You!"),e("br"),e("span",{class:"text-md font-medium text-esmerald"},"Did you know that we do all our developments with Tailwind CSS, the best framework for styles in web development.")])],-1),C={class:"mt-52"},$={class:"text-6xl font-light text-esmerald"},F={class:"text-4xl font-light text-esmerald mt-20"},L={class:"col-span-1"},N={class:"font-light text-esmerald text-lg"},T={class:"col-span-3 grid grid-cols-3 gap-8"},V=["onClick"],W={class:"border border-gray-200 rounded-lg"},z=["src","alt"],E={class:"mt-4 font-regular text-esmerald text-md"},M={class:"mt-2 bg-esmerald-light px-6 py-2 inline-block rounded-3xl text-esmerald text-sm"},R={class:"mt-52"},H={__name:"List",setup(Y){const c=x(),_=g([]),h=f(),p=(m,u,t)=>{h.push({name:"webDevelopmentsDetail",params:{development_id:m,section_id:u,component_id:t}})};return v(async()=>{await c.init(),_.value=c.getDevelopments}),(m,u)=>(s(),l("div",null,[e("div",y,[a(b)]),e("section",null,[e("div",D,[e("div",S,[B,e("div",null,[a(k,{spline:"/spline/Backgrounds/dune.splinecode"})])])])]),e("section",C,[(s(!0),l(d,null,r(_.value,t=>(s(),l("div",{key:t.id,class:"container mx-auto sm:px-6 lg:px-8"},[e("h1",$,n(t.title_en),1),e("h2",F,n(t.description_en),1),(s(!0),l(d,null,r(t.sections,i=>(s(),l("div",{key:i.id,class:"mt-40 grid grid-cols-4"},[e("div",L,[e("h2",N,n(i.title_en),1)]),e("div",T,[(s(!0),l(d,null,r(i.components,o=>(s(),l("div",{key:o.id,onClick:j=>p(t.id,i.id,o.id),class:"cursor-pointer"},[e("div",W,[e("img",{src:o.image_url,alt:o.id},null,8,z)]),e("h3",E,n(o.title_en),1),e("p",M,n(o.examples.length)+" components",1)],8,V))),128))])]))),128))]))),128))]),e("div",R,[a(w)])]))}};export{H as default};