const content = {
  es: {
    hero: {
      eyebrow: 'Financiación para productos con visión de largo plazo',
      title: 'Construimos hoy. Crecemos contigo.',
      subtitle: 'Financiamos productos con potencial y compartimos el riesgo operativo.',
      trust_note: 'Una oportunidad puede convertirse en un producto real.',
    },
    eligibility: {
      title: 'Un programa sujeto a evaluación',
      summary: 'La propuesta define el aporte inicial y el saldo aprobado.',
      badge: 'Aprobación previa',
    },
    options: [
      ['five-year', 'Alianza a 5 años', 'Recomendada', true, 5],
      ['three-year', 'Alianza a 3 años', 'Alternativa', false, 3],
    ],
    conditionTitles: ['12 meses de financiación', 'Exclusividad y custodia responsable', 'Calculadora de requerimientos', '60 horas disponibles cada mes'],
    calculator: {
      eyebrow: 'Transparencia para decidir',
      title: 'De una necesidad en palabras a un rango útil para planear',
      summary: 'La herramienta recibe lenguaje natural y entrega una referencia comercial.',
      input: { title: 'Qué se ingresa', items: ['Descripción en lenguaje natural del cambio.'] },
      output: { title: 'Qué se obtiene', items: ['Esfuerzo, tiempo y rango de precio.'] },
      disclaimer: 'La cotización formal confirma el alcance.',
    },
    package: {
      title: 'Capacidad mensual para la evolución del producto',
      summary: 'Pensado principalmente para requerimientos pequeños y acotados.',
      renewal_label: 'Se renueva cada mes', rollover_label: 'No acumula horas',
      availability_label: 'Desde producción', included_label: 'Incluido sin costo adicional',
    },
    term: {
      title: 'Custodia de código no es cesión de propiedad',
      summary: 'Project App. protege la continuidad técnica.',
      item: 'La custodia no transfiere la propiedad intelectual.',
    },
    cta: {
      eyebrow: 'Conversemos sobre el potencial del proyecto',
      title: 'Solicita una evaluación de financiación',
      body: 'Cuéntanos qué producto quieres construir.',
      button: 'Hablar por WhatsApp',
    },
    disclaimer: 'Información comercial de referencia.',
  },
  en: {
    hero: {
      eyebrow: 'Financing for products built with a long-term vision',
      title: 'We build today. We grow with you.',
      subtitle: 'We finance products with potential and share operational risk.',
      trust_note: 'An opportunity can become a real product.',
    },
    eligibility: {
      title: 'A program subject to evaluation',
      summary: 'The proposal defines the initial contribution and approved balance.',
      badge: 'Prior approval',
    },
    options: [
      ['five-year', '5-year partnership', 'Recommended', true, 5],
      ['three-year', '3-year partnership', 'Alternative', false, 3],
    ],
    conditionTitles: ['12 months of financing', 'Exclusivity and responsible custody', 'Requirement calculator', '60 hours available every month'],
    calculator: {
      eyebrow: 'Transparency for better decisions',
      title: 'From a need in plain language to a useful planning range',
      summary: 'The tool receives plain language and returns a commercial reference.',
      input: { title: 'What goes in', items: ['A plain-language description of the change.'] },
      output: { title: 'What comes out', items: ['Effort, time, and a price range.'] },
      disclaimer: 'The formal quote confirms the scope.',
    },
    package: {
      title: 'Monthly capacity for product evolution',
      summary: 'Intended mainly for small, bounded requirements.',
      renewal_label: 'Renews every month', rollover_label: 'Hours do not roll over',
      availability_label: 'Available from production', included_label: 'Included at no additional cost',
    },
    term: {
      title: 'Code custody is not ownership transfer',
      summary: 'Project App. protects technical continuity.',
      item: 'Custody does not transfer intellectual property.',
    },
    cta: {
      eyebrow: 'Let’s discuss the project’s potential',
      title: 'Request a financing evaluation',
      body: 'Tell us what product you want to build.',
      button: 'Talk on WhatsApp',
    },
    disclaimer: 'Commercial information for reference.',
  },
}

export function financingProgramFixture(language = 'es', overrides = {}) {
  const copy = content[language]
  return {
    language,
    financing_months: 12,
    ordinary_interest_rate: '0%',
    canonical_path: language === 'en' ? '/en-us/financing' : '/es-co/financing',
    hero: copy.hero,
    eligibility: copy.eligibility,
    options: copy.options.map(([id, name, badge, included, years]) => ({
      id, name, badge, exclusivity_years: years, recommended: included,
      hour_package_included: included,
      summary: included ? 'Financing with monthly continuity.' : 'Financing without the monthly package.',
      highlights: ['12 months at 0% ordinary interest.'],
    })),
    conditions: copy.conditionTitles.map((title, index) => ({
      id: ['financing', 'exclusivity', 'calculator', 'hour-package'][index],
      number: String(index + 1).padStart(2, '0'),
      icon: ['↗', '◇', '◎', '◷'][index],
      title,
      summary: 'A clear commercial condition for the partnership.',
      commercial_reason: 'It protects continuity and makes decisions predictable.',
      highlights: ['The formal agreement defines its exact scope.'],
    })),
    calculator: copy.calculator,
    package: {
      ...copy.package,
      name: language === 'en' ? 'Pro Pack' : 'Paquete Pro',
      hours: 60,
      renews_monthly: true,
      rollover: false,
      catalog_synced: overrides.catalogSynced ?? true,
    },
    legal_terms: [{
      id: 'code-custody',
      title: copy.term.title,
      summary: copy.term.summary,
      items: [copy.term.item],
    }],
    cta: {
      ...copy.cta,
      whatsapp_url: 'https://wa.me/573238122373?text=financing',
    },
    disclaimer: copy.disclaimer,
  }
}
