/**
 * Registry of per-section-type admin form components.
 * Mirrors the public sectionComponentMap idiom (see SectionPreviewModal.vue).
 * `technical_document` is intentionally absent: it stays delegated to TechnicalDocumentEditor.
 */
import GreetingForm from './GreetingForm.vue';
import ExecutiveSummaryForm from './ExecutiveSummaryForm.vue';
import ContextDiagnosticForm from './ContextDiagnosticForm.vue';
import ConversionStrategyForm from './ConversionStrategyForm.vue';
import DesignUxForm from './DesignUxForm.vue';
import CreativeSupportForm from './CreativeSupportForm.vue';
import DevelopmentStagesForm from './DevelopmentStagesForm.vue';
import FunctionalRequirementsForm from './FunctionalRequirementsForm.vue';
import TimelineForm from './TimelineForm.vue';
import InvestmentForm from './InvestmentForm.vue';
import FinalNoteForm from './FinalNoteForm.vue';
import ProposalSummaryForm from './ProposalSummaryForm.vue';
import NextStepsForm from './NextStepsForm.vue';
import ProcessMethodologyForm from './ProcessMethodologyForm.vue';
import ValueAddedModulesForm from './ValueAddedModulesForm.vue';
import RoiProjectionForm from './RoiProjectionForm.vue';
import CommercialConditionsForm from './CommercialConditionsForm.vue';

export const sectionFormRegistry = {
  greeting: { label: 'Saludo', component: GreetingForm },
  executive_summary: { label: 'Resumen ejecutivo', component: ExecutiveSummaryForm },
  context_diagnostic: { label: 'Diagnóstico', component: ContextDiagnosticForm },
  conversion_strategy: { label: 'Estrategia de conversión', component: ConversionStrategyForm },
  design_ux: { label: 'Diseño UX', component: DesignUxForm },
  creative_support: { label: 'Apoyo creativo', component: CreativeSupportForm },
  development_stages: { label: 'Etapas de desarrollo', component: DevelopmentStagesForm },
  functional_requirements: { label: 'Requerimientos', component: FunctionalRequirementsForm },
  timeline: { label: 'Cronograma', component: TimelineForm },
  investment: { label: 'Inversión', component: InvestmentForm },
  final_note: { label: 'Nota final', component: FinalNoteForm },
  proposal_summary: { label: 'Resumen de propuesta', component: ProposalSummaryForm },
  next_steps: { label: 'Próximos pasos', component: NextStepsForm },
  process_methodology: { label: 'Proceso y metodología', component: ProcessMethodologyForm },
  value_added_modules: { label: 'Valor agregado', component: ValueAddedModulesForm },
  roi_projection: { label: 'Proyección ROI', component: RoiProjectionForm },
  commercial_conditions: { label: 'Condiciones comerciales', component: CommercialConditionsForm },
};

export const SECTION_TYPE_OPTIONS = Object.entries(sectionFormRegistry).map(
  ([type, { label }]) => ({ type, label }),
);
