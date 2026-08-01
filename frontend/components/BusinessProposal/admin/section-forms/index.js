/**
 * Registry of per-section-type admin form components.
 * Mirrors the public sectionComponentMap idiom (see SectionPreviewModal.vue).
 * `technical_document` is intentionally absent: it stays delegated to TechnicalDocumentEditor.
 *
 * Forms are loaded lazily: SectionEditor only renders one once its section
 * is expanded, so importing all 17 up front put ~1.4k lines of form code in
 * the proposal edit chunk for a user who may expand none of them.
 */
import { defineAsyncComponent } from 'vue';


export const sectionFormRegistry = {
  greeting: { label: 'Saludo', component: defineAsyncComponent(() => import('./GreetingForm.vue')) },
  executive_summary: { label: 'Resumen ejecutivo', component: defineAsyncComponent(() => import('./ExecutiveSummaryForm.vue')) },
  context_diagnostic: { label: 'Diagnóstico', component: defineAsyncComponent(() => import('./ContextDiagnosticForm.vue')) },
  conversion_strategy: { label: 'Estrategia de conversión', component: defineAsyncComponent(() => import('./ConversionStrategyForm.vue')) },
  design_ux: { label: 'Diseño UX', component: defineAsyncComponent(() => import('./DesignUxForm.vue')) },
  creative_support: { label: 'Apoyo creativo', component: defineAsyncComponent(() => import('./CreativeSupportForm.vue')) },
  development_stages: { label: 'Etapas de desarrollo', component: defineAsyncComponent(() => import('./DevelopmentStagesForm.vue')) },
  functional_requirements: { label: 'Requerimientos', component: defineAsyncComponent(() => import('./FunctionalRequirementsForm.vue')) },
  timeline: { label: 'Cronograma', component: defineAsyncComponent(() => import('./TimelineForm.vue')) },
  investment: { label: 'Inversión', component: defineAsyncComponent(() => import('./InvestmentForm.vue')) },
  final_note: { label: 'Nota final', component: defineAsyncComponent(() => import('./FinalNoteForm.vue')) },
  proposal_summary: { label: 'Resumen de propuesta', component: defineAsyncComponent(() => import('./ProposalSummaryForm.vue')) },
  next_steps: { label: 'Próximos pasos', component: defineAsyncComponent(() => import('./NextStepsForm.vue')) },
  process_methodology: { label: 'Proceso y metodología', component: defineAsyncComponent(() => import('./ProcessMethodologyForm.vue')) },
  value_added_modules: { label: 'Valor agregado', component: defineAsyncComponent(() => import('./ValueAddedModulesForm.vue')) },
  roi_projection: { label: 'Proyección ROI', component: defineAsyncComponent(() => import('./RoiProjectionForm.vue')) },
  commercial_conditions: { label: 'Condiciones comerciales', component: defineAsyncComponent(() => import('./CommercialConditionsForm.vue')) },
};

export const SECTION_TYPE_OPTIONS = Object.entries(sectionFormRegistry).map(
  ([type, { label }]) => ({ type, label }),
);
