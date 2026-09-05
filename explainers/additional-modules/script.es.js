/**
 * Guion en español del video "Módulos adicionales" (≈70 s).
 * Los textos entre llaves se rellenan con el contenido congelado en
 * content/additional-modules.es.js: {eyebrow} {title} {subtitle} {noPriceNotice}
 * {total} {categoryCount} {categories}.
 * `caption` es el subtítulo en pantalla; `narration` es lo que dice la voz opcional.
 */
export default {
  language: 'es',
  iconOverrides: {
    '🇨🇴': '🏦',
  },
  scenes: {
    'scene-intro': {
      eyebrow: '{eyebrow}',
      title: '{title}',
      caption: 'Un resumen de un minuto del catálogo de módulos adicionales.',
      narration: 'Este es un resumen de un minuto del catálogo de módulos adicionales de Project App.',
    },
    'scene-what': {
      eyebrow: 'Qué vas a encontrar',
      title: 'Capacidades listas para ampliar tu plataforma',
      lead: '{subtitle}',
      pill: '{noPriceNotice}',
      caption: 'Son capacidades que se integran a tu plataforma cuando el negocio las necesita. Aquí no verás precios: el alcance real se define en una propuesta.',
      narration: 'Son capacidades que se integran a tu plataforma cuando el negocio las necesita. Aquí no verás precios: el alcance real se define en una propuesta.',
    },
    'scene-categories': {
      eyebrow: '{categoryCount} categorías',
      title: 'Organizado para encontrar rápido lo que buscas',
      caption: 'El catálogo se organiza en {categoryCount} categorías: {categories}.',
      narration: 'El catálogo se organiza en {categoryCount} categorías: {categories}.',
    },
    'scene-carousel': {
      eyebrow: '{total} módulos disponibles',
      title: 'Un vistazo a todo el catálogo',
      caption: 'Desde facturación electrónica y pasarelas de pago hasta inteligencia artificial y reportes: cada módulo resuelve una necesidad concreta.',
      narration: 'Son {total} módulos: desde facturación electrónica y pasarelas de pago hasta inteligencia artificial y reportes. Cada uno resuelve una necesidad concreta de tu negocio.',
    },
    'scene-how': {
      eyebrow: 'Cómo explorarlo',
      title: 'Tres formas de sacarle provecho',
      beats: [
        {
          text: 'Abre cualquier módulo: qué es, para qué sirve, qué resuelve, qué se integra y qué hace falta',
          caption: 'Abre cualquier módulo para ver qué es, para qué sirve, qué resuelve, qué se integra y qué hace falta para implementarlo.',
        },
        {
          text: 'Míralo como tarjetas, lista o acordeón, y salta por categoría',
          caption: 'Míralo como tarjetas, lista o acordeón, cambia de idioma y salta directo a la categoría que te interesa.',
        },
        {
          text: 'Descárgalo en PDF o pide una selección a tu medida',
          caption: 'Descárgalo en PDF o pide una selección preparada para tu conversación.',
        },
      ],
      narration: 'Abre cualquier módulo para ver qué es, para qué sirve, qué resuelve, qué se integra y qué hace falta para implementarlo. Míralo como tarjetas, lista o acordeón, y salta directo a la categoría que te interesa. Y si lo prefieres, descárgalo en PDF o pide una selección preparada para tu conversación.',
    },
    'scene-close': {
      title: 'Explora el catálogo y conversemos sobre lo que tu plataforma necesita.',
      pill: 'projectapp.co/es-co/additional-modules',
      caption: 'Explora el catálogo y conversemos sobre lo que tu plataforma necesita.',
      narration: 'Explora el catálogo y conversemos sobre lo que tu plataforma necesita.',
    },
  },
}
