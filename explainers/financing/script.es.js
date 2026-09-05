/**
 * Guion en español del video "Financiación" (≈72 s).
 * Plantillas disponibles desde content/financing.es.js: {eyebrow} {title} {subtitle}
 * {trustNote} {months} {interest} {hours} {eligibilityBadge} {eligibilityTitle}
 * {ctaButton} {optionsTitle} {optionsIntro}; dentro de `facts`: {years} {cycles}.
 * `caption` es el subtítulo en pantalla; `narration` es lo que dice la voz opcional.
 */
export default {
  language: 'es',
  iconOverrides: {},
  scenes: {
    'scene-intro': {
      eyebrow: '{eyebrow}',
      title: '{title}',
      caption: 'El programa de financiación de Project App, en un minuto.',
      narration: 'Este es el programa de financiación de Project App, resumido en un minuto.',
    },
    'scene-what': {
      eyebrow: 'Qué es',
      title: 'Financiamos productos con potencial y compartimos el riesgo',
      lead: '{subtitle}',
      caption: 'Financiamos el desarrollo e implementación de productos con valor y potencial sostenible. Entregamos antes de recuperar la inversión y compartimos el riesgo.',
      narration: 'Project App puede financiar el desarrollo e implementación de productos de software con valor y potencial sostenible. Entregamos antes de recuperar la totalidad de la inversión y compartimos el riesgo operativo del proyecto.',
    },
    'scene-conditions': {
      eyebrow: 'Cinco puntos clave',
      title: 'Así compartimos el riesgo',
      conditions: {
        financing: 'Financiamos el saldo aprobado del desarrollo en {months} meses, con {interest} de interés ordinario.',
        exclusivity: 'Somos tu casa desarrolladora durante la alianza y custodiamos el código sin quedarnos con la propiedad intelectual.',
        calculator: 'La calculadora anticipa esfuerzo, tiempo y rango de inversión de cada cambio futuro antes de cotizarlo.',
        'hour-package': 'La alianza a cinco años incluye {hours} horas cada mes para requerimientos aprobados.',
        'payment-discipline': 'Cuotas con fecha clara cada mes y reglas explícitas para cubrir el riesgo de impago.',
      },
      narration: 'Cinco puntos clave. Uno: financiamos el saldo aprobado del desarrollo en {months} meses, con cero por ciento de interés ordinario. Dos: somos tu casa desarrolladora durante la alianza y custodiamos el código sin quedarnos con la propiedad intelectual. Tres: la calculadora de requerimientos anticipa esfuerzo, tiempo y rango de inversión de cada cambio futuro. Cuatro: la alianza a cinco años incluye {hours} horas cada mes para requerimientos aprobados. Y cinco: cuotas con fecha clara y reglas explícitas para cubrir el riesgo de impago.',
    },
    'scene-options': {
      eyebrow: '{optionsTitle}',
      title: 'Cinco o tres años: tú eliges el horizonte',
      note: '{optionsIntro}',
      facts: {
        'five-year': ['{years} años de exclusividad', 'Hasta {cycles} ciclos de financiación', 'Paquete mensual de {hours} horas incluido'],
        'three-year': ['{years} años de exclusividad', '{cycles} ciclo de financiación', 'Sin paquete mensual de horas'],
      },
      caption: 'La alianza a cinco años suma un segundo ciclo de financiación y el paquete mensual de horas; la de tres años conserva financiación, exclusividad y custodia.',
      narration: 'Hay dos formas de estructurar la alianza. La de cinco años, recomendada, permite hasta dos ciclos de financiación e incluye el paquete mensual de {hours} horas. La de tres años conserva la financiación, la exclusividad y la custodia del código, sin el paquete mensual. El plazo de financiación es el mismo; cambia el horizonte.',
    },
    'scene-apply': {
      eyebrow: '{eligibilityBadge}',
      title: '{eligibilityTitle}',
      beats: [
        'Cada solicitud pasa por una revisión técnica, comercial y de riesgo',
        'El análisis define el aporte inicial y el saldo financiado',
        'Solicita la evaluación con un mensaje: {ctaButton}',
      ],
      caption: 'Cada solicitud pasa por una revisión técnica, comercial y de riesgo que define el aporte inicial y el saldo aprobado. Solicita la evaluación por WhatsApp.',
      narration: 'Es un programa sujeto a evaluación: cada solicitud pasa por una revisión técnica, comercial y de riesgo que define el aporte inicial y el saldo aprobado. Solicita la evaluación por WhatsApp o revisa las reglas completas en la página.',
    },
    'scene-close': {
      title: '{trustNote}',
      pill: 'projectapp.co/es-co/financing',
      caption: 'Una alternativa para convertir una buena oportunidad en un producto real.',
      narration: 'Una alternativa para convertir una buena oportunidad en un producto real, sin trasladar todo el esfuerzo financiero al inicio.',
    },
  },
}
