"""Management command — create fake PortfolioWork records for local / demo use.

Generates bilingual (ES/EN) portfolio case studies with a structured
``content_json`` (problem / solution / results), realistic categories and
SEO metadata. Idempotent by ``slug`` so re-running does not duplicate.
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import PortfolioWork


# ── Data pools ────────────────────────────────────────────────────────────

# Each entry is a realistic agency case study. Bilingual on purpose: the
# public portfolio renders ES or EN depending on the visitor's locale.
WORKS = [
    {
        'title_es': 'Tienda online para marca de café de origen',
        'title_en': 'Online store for a single-origin coffee brand',
        'category_es': 'E-Commerce', 'category_en': 'E-Commerce',
        'project_url': 'https://example.com/cafe-origen',
        'cover': 'https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=1200&h=630&fit=crop',
        'problem': 'La marca vendía solo por WhatsApp y perdía pedidos fuera de horario; no había inventario ni pagos en línea.',
        'solution': 'Construimos una tienda Nuxt + Django con catálogo, carrito, checkout Wompi y panel de inventario en tiempo real.',
        'results': 'Ventas en línea 24/7, +38% de conversión móvil y reducción del 70% en pedidos perdidos.',
        'highlights': ['Checkout Wompi', 'Inventario en tiempo real', 'Catálogo filtrable'],
    },
    {
        'title_es': 'Plataforma de reservas para clínica dental',
        'title_en': 'Booking platform for a dental clinic',
        'category_es': 'Aplicación web', 'category_en': 'Web App',
        'project_url': 'https://example.com/clinica-dental',
        'cover': 'https://images.unsplash.com/photo-1629909613654-28e377c37b09?w=1200&h=630&fit=crop',
        'problem': 'La agenda se llevaba en papel y se solapaban citas; el equipo perdía horas confirmando por teléfono.',
        'solution': 'Sistema de reservas con calendario por profesional, recordatorios automáticos y portal del paciente.',
        'results': 'Citas confirmadas sin llamadas, -45% de ausentismo y agenda visible para todo el equipo.',
        'highlights': ['Recordatorios automáticos', 'Agenda por profesional', 'Portal del paciente'],
    },
    {
        'title_es': 'Dashboard de logística para distribuidora',
        'title_en': 'Logistics dashboard for a distributor',
        'category_es': 'SaaS Dashboard', 'category_en': 'SaaS Dashboard',
        'project_url': 'https://example.com/logistica-andina',
        'cover': 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=1200&h=630&fit=crop',
        'problem': 'Las rutas se planeaban en Excel y no había visibilidad del estado de las entregas.',
        'solution': 'Tablero con seguimiento de pedidos, KPIs por zona y exportación de reportes.',
        'results': 'Visibilidad total de la operación, +22% de entregas a tiempo y reportes en un clic.',
        'highlights': ['KPIs por zona', 'Seguimiento de entregas', 'Reportes exportables'],
    },
    {
        'title_es': 'Landing de captación para fintech',
        'title_en': 'Lead-generation landing for a fintech',
        'category_es': 'Landing Profesional', 'category_en': 'Professional Landing',
        'project_url': 'https://example.com/fintech-landing',
        'cover': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=630&fit=crop',
        'problem': 'El sitio anterior cargaba lento y no comunicaba la propuesta de valor; el CPL era alto.',
        'solution': 'Landing optimizada en performance, copy orientado a conversión y formulario con validación.',
        'results': 'Carga bajo 1.5s, +64% de leads cualificados y reducción del costo por lead.',
        'highlights': ['Performance < 1.5s', 'A/B testing', 'Formulario validado'],
    },
    {
        'title_es': 'Rediseño de portal inmobiliario',
        'title_en': 'Real-estate portal redesign',
        'category_es': 'Rediseño', 'category_en': 'Redesign',
        'project_url': 'https://example.com/inmobiliaria',
        'cover': 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1200&h=630&fit=crop',
        'problem': 'El buscador era confuso y el portal no era responsive; el rebote en móvil superaba el 70%.',
        'solution': 'Rediseño mobile-first con buscador por mapa, filtros guardados y fichas enriquecidas.',
        'results': 'Rebote móvil -31%, +2.4x tiempo en sitio y más solicitudes de visita.',
        'highlights': ['Buscador por mapa', 'Mobile-first', 'Filtros guardados'],
    },
    {
        'title_es': 'Plataforma de cursos para academia online',
        'title_en': 'Course platform for an online academy',
        'category_es': 'Aplicación web', 'category_en': 'Web App',
        'project_url': 'https://example.com/academia',
        'cover': 'https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=1200&h=630&fit=crop',
        'problem': 'Los cursos se entregaban por Drive y no había seguimiento del progreso ni cobros recurrentes.',
        'solution': 'LMS con lecciones, progreso por alumno, certificados y suscripción mensual.',
        'results': 'Cobros recurrentes automatizados, +50% de finalización de cursos y soporte centralizado.',
        'highlights': ['Suscripción mensual', 'Progreso por alumno', 'Certificados'],
    },
    {
        'title_es': 'Sitio institucional para fundación ambiental',
        'title_en': 'Institutional site for an environmental foundation',
        'category_es': 'Sitio web', 'category_en': 'Website',
        'project_url': 'https://example.com/fundacion',
        'cover': 'https://images.unsplash.com/photo-1473773508845-188df298d2d1?w=1200&h=630&fit=crop',
        'problem': 'La fundación no podía recibir donaciones en línea ni comunicar su impacto.',
        'solution': 'Sitio con historias de impacto, donaciones recurrentes y blog editorial.',
        'results': '+3x donaciones en línea, base de donantes recurrentes y narrativa de impacto clara.',
        'highlights': ['Donaciones recurrentes', 'Historias de impacto', 'Blog editorial'],
    },
    {
        'title_es': 'App de inventario con lector de código de barras',
        'title_en': 'Inventory app with barcode scanning',
        'category_es': 'Aplicación web', 'category_en': 'Web App',
        'project_url': 'https://example.com/inventario',
        'cover': 'https://images.unsplash.com/photo-1553413077-190dd305871c?w=1200&h=630&fit=crop',
        'problem': 'El conteo de inventario era manual y propenso a errores entre bodega y punto de venta.',
        'solution': 'PWA con escaneo por cámara, sincronización offline y alertas de stock mínimo.',
        'results': 'Conteos 4x más rápidos, -90% de errores de stock y operación sin conexión.',
        'highlights': ['Escaneo por cámara', 'Modo offline', 'Alertas de stock'],
    },
    {
        'title_es': 'Marketplace de servicios locales',
        'title_en': 'Local services marketplace',
        'category_es': 'E-Commerce', 'category_en': 'E-Commerce',
        'project_url': 'https://example.com/marketplace',
        'cover': 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1200&h=630&fit=crop',
        'problem': 'No existía un canal único para conectar prestadores de servicios con clientes de la zona.',
        'solution': 'Marketplace con perfiles verificados, reseñas, agenda y pagos con comisión.',
        'results': 'Red de prestadores verificados, pagos seguros y reputación basada en reseñas.',
        'highlights': ['Perfiles verificados', 'Pagos con comisión', 'Sistema de reseñas'],
    },
    {
        'title_es': 'Panel de analítica para medio digital',
        'title_en': 'Analytics panel for a digital outlet',
        'category_es': 'SaaS Dashboard', 'category_en': 'SaaS Dashboard',
        'project_url': 'https://example.com/medio-analytics',
        'cover': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&h=630&fit=crop',
        'problem': 'El equipo editorial no sabía qué contenido funcionaba ni cómo priorizar la agenda.',
        'solution': 'Panel con métricas de audiencia, ranking de artículos y tendencias por categoría.',
        'results': 'Decisiones editoriales basadas en datos y +28% de lectura por sesión.',
        'highlights': ['Ranking de artículos', 'Tendencias por categoría', 'Métricas de audiencia'],
    },
    {
        'title_es': 'Portal de pagos para hosting recurrente',
        'title_en': 'Recurring hosting payments portal',
        'category_es': 'Aplicación web', 'category_en': 'Web App',
        'project_url': 'https://example.com/hosting-portal',
        'cover': 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&h=630&fit=crop',
        'problem': 'El cobro de hosting era manual cada mes y generaba cartera vencida.',
        'solution': 'Portal con suscripciones, tarjeta tokenizada y cobros automáticos vía Wompi.',
        'results': 'Cobros automáticos, -80% de cartera vencida y conciliación sin esfuerzo.',
        'highlights': ['Tarjeta tokenizada', 'Cobros automáticos', 'Conciliación'],
    },
    {
        'title_es': 'Plataforma de adopción y donaciones animal',
        'title_en': 'Animal adoption and donations platform',
        'category_es': 'Aplicación web', 'category_en': 'Web App',
        'project_url': 'https://example.com/adopcion',
        'cover': 'https://images.unsplash.com/photo-1450778869180-41d0601e046e?w=1200&h=630&fit=crop',
        'problem': 'Los refugios gestionaban adopciones por redes sociales, sin trazabilidad ni donaciones recurrentes.',
        'solution': 'Plataforma con catálogo de animales, solicitudes de adopción, padrinazgo y donaciones Wompi.',
        'results': 'Adopciones trazables, padrinazgos recurrentes y refugios con panel propio.',
        'highlights': ['Catálogo de animales', 'Padrinazgo recurrente', 'Panel de refugio'],
    },
]


SECTION_TITLES = {
    'es': {'problem': 'El reto', 'solution': 'La solución', 'results': 'Los resultados'},
    'en': {'problem': 'The challenge', 'solution': 'The solution', 'results': 'The results'},
}


def _content_json(spec, lang):
    """Build the problem/solution/results structure for one language."""
    titles = SECTION_TITLES[lang]
    return {
        'problem': {
            'title': titles['problem'],
            'description': spec['problem'],
            'highlights': spec['highlights'],
        },
        'solution': {
            'title': titles['solution'],
            'description': spec['solution'],
            'highlights': spec['highlights'],
        },
        'results': {
            'title': titles['results'],
            'description': spec['results'],
            'highlights': spec['highlights'],
            'testimonial_video_url': '',
        },
    }


class Command(BaseCommand):
    help = 'Create fake PortfolioWork records (bilingual case studies) for local/demo use.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=12,
            help='Number of portfolio works to create (default: 12).',
        )

    def handle(self, *args, **options):
        count = max(1, options['count'])
        rng = random.Random(42)
        created = 0
        skipped = 0

        for i in range(count):
            spec = WORKS[i % len(WORKS)]
            cycle = i // len(WORKS)
            suffix_es = f' — Caso {cycle + 1}' if cycle else ''
            suffix_en = f' — Case {cycle + 1}' if cycle else ''
            title_es = spec['title_es'] + suffix_es
            title_en = spec['title_en'] + suffix_en

            if PortfolioWork.objects.filter(title_es=title_es).exists():
                skipped += 1
                continue

            is_published = rng.random() < 0.8  # ~80% published, rest drafts
            published_at = None
            if is_published:
                published_at = timezone.now() - timedelta(days=i * 4 + rng.randint(0, 3))

            excerpt_es = spec['results']
            excerpt_en = spec['results']

            work = PortfolioWork(
                title_es=title_es,
                title_en=title_en,
                project_url=spec['project_url'],
                cover_image_url=spec['cover'],
                category_title_es=spec['category_es'],
                category_title_en=spec['category_en'],
                excerpt_es=excerpt_es,
                excerpt_en=excerpt_en,
                content_json_es=_content_json(spec, 'es'),
                content_json_en=_content_json(spec, 'en'),
                meta_title_es=title_es,
                meta_title_en=title_en,
                meta_description_es=excerpt_es[:160],
                meta_description_en=excerpt_en[:160],
                meta_keywords_es=spec['category_es'],
                meta_keywords_en=spec['category_en'],
                is_published=is_published,
                published_at=published_at,
                order=i,
            )
            work.save()
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'{created} portfolio works created ({skipped} skipped, already existed).'
        ))
