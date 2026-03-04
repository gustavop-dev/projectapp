import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import BlogPost


# ---------------------------------------------------------------------------
# Pools of realistic AI-related blog data for dynamic generation
# ---------------------------------------------------------------------------

TITLES = [
    'GPT-5 y el futuro de la IA generativa',
    'Google DeepMind revoluciona la predicción de proteínas',
    'Meta lanza Llama 4: IA de código abierto más potente',
    'Agentes de IA: La próxima frontera del desarrollo de software',
    'Regulación de IA en 2025: ¿Qué nos espera?',
    'Cómo la IA está transformando la educación en Latinoamérica',
    'Midjourney V7: La generación de imágenes alcanza un nuevo nivel',
    'Anthropic presenta Claude 4 con razonamiento extendido',
    'El auge de los modelos de IA pequeños y eficientes',
    'IA y ciberseguridad: Amenazas y defensas en 2025',
    'Apple Intelligence llega a todos los dispositivos',
    'La IA en la salud: diagnósticos más rápidos y precisos',
    'Open source vs propietario: la batalla de los modelos de lenguaje',
    'Robots humanoides: de la ficción a las fábricas',
    'IA para desarrolladores: las mejores herramientas de 2025',
    'Nvidia domina el mercado de chips para IA',
    'Sora y la revolución del video generativo',
    'Startups de IA que están cambiando el juego',
    'El impacto de la IA en el mercado laboral latinoamericano',
    'Multimodalidad: la convergencia de texto, imagen y audio en IA',
]

EXCERPTS = [
    'Exploramos los avances más significativos y su impacto en la industria tecnológica.',
    'Un análisis profundo de los últimos desarrollos y lo que significan para el futuro.',
    'Las nuevas capacidades prometen transformar múltiples sectores de la economía.',
    '¿Qué implicaciones tiene este avance para desarrolladores y empresas?',
    'Revisamos las tendencias más importantes y las oportunidades que presentan.',
    'Un recorrido por las innovaciones que están redefiniendo lo posible.',
    'Los expertos analizan el impacto a corto y largo plazo de estos cambios.',
    'Cómo estas tecnologías están democratizando el acceso a herramientas avanzadas.',
    'Todo lo que necesitas saber sobre los últimos avances en inteligencia artificial.',
    'Un vistazo a las innovaciones que marcarán el rumbo de la tecnología.',
]

CONTENT_TEMPLATES = [
    (
        '<h2>{topic}</h2>'
        '<p>La inteligencia artificial continúa evolucionando a un ritmo impresionante. '
        'Los últimos avances sugieren un salto cualitativo en las capacidades de los '
        'sistemas modernos, con implicaciones profundas para la industria.</p>'
        '<h3>Contexto y antecedentes</h3>'
        '<p>Durante los últimos meses, hemos sido testigos de una aceleración sin '
        'precedentes en el desarrollo de modelos de IA. Empresas como OpenAI, Google '
        'y Meta compiten por liderar la próxima generación de herramientas inteligentes.</p>'
        '<h3>¿Qué podemos esperar?</h3>'
        '<p>Entre las mejoras anticipadas se encuentran una mejor comprensión del '
        'contexto, capacidades multimodales avanzadas y un razonamiento más robusto '
        'en tareas complejas de la vida real.</p>'
        '<h3>Impacto en la industria</h3>'
        '<p>Estas mejoras tendrán implicaciones directas en sectores como el desarrollo '
        'de software, la atención al cliente, la medicina y la educación. Las empresas '
        'que adopten estas tecnologías tempranamente tendrán una ventaja competitiva '
        'significativa.</p>'
    ),
    (
        '<h2>{topic}</h2>'
        '<p>El ecosistema de inteligencia artificial está experimentando cambios '
        'fundamentales que afectan tanto a grandes corporaciones como a startups '
        'y desarrolladores individuales.</p>'
        '<h3>Principales innovaciones</h3>'
        '<ul>'
        '<li>Mayor eficiencia en el entrenamiento de modelos</li>'
        '<li>Reducción de costos computacionales</li>'
        '<li>Mejoras en la calidad de las respuestas</li>'
        '<li>Nuevas capacidades multimodales</li>'
        '</ul>'
        '<h3>Desafíos pendientes</h3>'
        '<p>A pesar de los avances, la confiabilidad, la seguridad y la ética siguen '
        'siendo retos importantes que la industria debe abordar antes de una adopción '
        'masiva en entornos críticos.</p>'
        '<h3>Perspectiva a futuro</h3>'
        '<p>Los analistas coinciden en que estamos apenas en las primeras etapas de '
        'una transformación que redefinirá la forma en que trabajamos, aprendemos '
        'y nos comunicamos.</p>'
    ),
    (
        '<h2>{topic}</h2>'
        '<p>La carrera por la supremacía en inteligencia artificial se intensifica, '
        'con nuevos actores entrando al mercado y los líderes consolidando sus '
        'posiciones mediante avances significativos.</p>'
        '<h3>Estado actual del mercado</h3>'
        '<p>El mercado de IA generativa ha superado expectativas, con un crecimiento '
        'interanual que supera el 40%. Las inversiones en infraestructura de IA '
        'han alcanzado niveles récord a nivel mundial.</p>'
        '<h3>Oportunidades para Latinoamérica</h3>'
        '<p>La región tiene una oportunidad única de posicionarse como un hub de '
        'talento en IA. Países como Colombia, México y Brasil están formando '
        'profesionales altamente competitivos en este campo.</p>'
        '<blockquote>La democratización de la IA no es solo una promesa — es una '
        'realidad que está transformando economías emergentes.</blockquote>'
        '<h3>Conclusión</h3>'
        '<p>El futuro de la IA es colaborativo, accesible y lleno de posibilidades. '
        'Mantenerse informado y adaptarse será clave para aprovechar esta ola.</p>'
    ),
]

SOURCES_POOL = [
    {'name': 'OpenAI Blog', 'url': 'https://openai.com/blog'},
    {'name': 'Google AI Blog', 'url': 'https://blog.google/technology/ai/'},
    {'name': 'Meta AI Blog', 'url': 'https://ai.meta.com/blog/'},
    {'name': 'Microsoft AI Blog', 'url': 'https://blogs.microsoft.com/ai/'},
    {'name': 'Hugging Face Blog', 'url': 'https://huggingface.co/blog'},
    {'name': 'TechCrunch', 'url': 'https://techcrunch.com/category/artificial-intelligence/'},
    {'name': 'The Verge', 'url': 'https://www.theverge.com/ai-artificial-intelligence'},
    {'name': 'arXiv', 'url': 'https://arxiv.org/list/cs.AI/recent'},
    {'name': 'VentureBeat', 'url': 'https://venturebeat.com/ai/'},
    {'name': 'Ars Technica', 'url': 'https://arstechnica.com/ai/'},
    {'name': 'Nature', 'url': 'https://www.nature.com/'},
    {'name': 'MIT Technology Review', 'url': 'https://www.technologyreview.com/'},
    {'name': 'Wired', 'url': 'https://www.wired.com/tag/artificial-intelligence/'},
]


class Command(BaseCommand):
    help = 'Create fake blog posts for development/testing'

    """
    Usage:
      python manage.py create_fake_blog_posts            # creates 5 posts (default)
      python manage.py create_fake_blog_posts --count 3   # creates 3 posts
      python manage.py create_fake_blog_posts --count 10  # creates 10 posts
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=5,
            help='Number of blog posts to create (default: 5)',
        )

    def handle(self, *args, **options):
        count = options['count']
        now = timezone.now()

        created = 0
        for i in range(count):
            title = TITLES[i % len(TITLES)]
            # Append suffix to avoid slug collision when count > pool size
            if i >= len(TITLES):
                title = f'{title} — Parte {i // len(TITLES) + 1}'

            # Skip if title already exists
            if BlogPost.objects.filter(title=title).exists():
                self.stdout.write(self.style.WARNING(
                    f'Already exists: "{title}"'
                ))
                continue

            excerpt = EXCERPTS[i % len(EXCERPTS)]
            template = CONTENT_TEMPLATES[i % len(CONTENT_TEMPLATES)]
            content = template.format(topic=title)
            sources = random.sample(SOURCES_POOL, k=random.randint(2, 4))

            # ~80% published, 20% draft
            is_published = (i % 5) != 4
            published_at = (
                now - timedelta(days=i * 3 + random.randint(0, 2))
                if is_published else None
            )

            BlogPost.objects.create(
                title=title,
                excerpt=excerpt,
                content=content,
                sources=sources,
                is_published=is_published,
                published_at=published_at,
            )
            status_label = 'published' if is_published else 'draft'
            created += 1
            self.stdout.write(self.style.SUCCESS(
                f'[{status_label:>9}] Created: "{title}"'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Created {created} blog post(s).'
        ))
