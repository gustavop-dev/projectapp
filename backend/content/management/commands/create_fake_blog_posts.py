import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import BlogPost


# ---------------------------------------------------------------------------
# Bilingual pools of realistic AI-related blog data
# ---------------------------------------------------------------------------

POSTS = [
    {
        'title_es': 'GPT-5 y el futuro de la IA generativa',
        'title_en': 'GPT-5 and the Future of Generative AI',
        'excerpt_es': 'Exploramos los avances más significativos y su impacto en la industria tecnológica.',
        'excerpt_en': 'We explore the most significant advances and their impact on the tech industry.',
        'cover_image_url': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1200&q=80',
    },
    {
        'title_es': 'Google DeepMind revoluciona la predicción de proteínas',
        'title_en': 'Google DeepMind Revolutionizes Protein Prediction',
        'excerpt_es': 'Un análisis profundo de los últimos desarrollos y lo que significan para el futuro.',
        'excerpt_en': 'A deep analysis of the latest developments and what they mean for the future.',
        'cover_image_url': 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=1200&q=80',
    },
    {
        'title_es': 'Meta lanza Llama 4: IA de código abierto más potente',
        'title_en': 'Meta Launches Llama 4: The Most Powerful Open-Source AI',
        'excerpt_es': 'Las nuevas capacidades prometen transformar múltiples sectores de la economía.',
        'excerpt_en': 'New capabilities promise to transform multiple sectors of the economy.',
        'cover_image_url': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=1200&q=80',
    },
    {
        'title_es': 'Agentes de IA: La próxima frontera del desarrollo de software',
        'title_en': 'AI Agents: The Next Frontier in Software Development',
        'excerpt_es': '¿Qué implicaciones tiene este avance para desarrolladores y empresas?',
        'excerpt_en': 'What implications does this advance have for developers and businesses?',
        'cover_image_url': 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200&q=80',
    },
    {
        'title_es': 'Regulación de IA en 2025: ¿Qué nos espera?',
        'title_en': 'AI Regulation in 2025: What Lies Ahead?',
        'excerpt_es': 'Revisamos las tendencias más importantes y las oportunidades que presentan.',
        'excerpt_en': 'We review the most important trends and the opportunities they present.',
        'cover_image_url': 'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200&q=80',
    },
    {
        'title_es': 'Cómo la IA está transformando la educación en Latinoamérica',
        'title_en': 'How AI Is Transforming Education in Latin America',
        'excerpt_es': 'Un recorrido por las innovaciones que están redefiniendo lo posible.',
        'excerpt_en': 'A tour through the innovations that are redefining what is possible.',
        'cover_image_url': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&q=80',
    },
    {
        'title_es': 'Midjourney V7: La generación de imágenes alcanza un nuevo nivel',
        'title_en': 'Midjourney V7: Image Generation Reaches a New Level',
        'excerpt_es': 'Los expertos analizan el impacto a corto y largo plazo de estos cambios.',
        'excerpt_en': 'Experts analyze the short and long-term impact of these changes.',
        'cover_image_url': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&q=80',
    },
    {
        'title_es': 'Anthropic presenta Claude 4 con razonamiento extendido',
        'title_en': 'Anthropic Introduces Claude 4 with Extended Reasoning',
        'excerpt_es': 'Cómo estas tecnologías están democratizando el acceso a herramientas avanzadas.',
        'excerpt_en': 'How these technologies are democratizing access to advanced tools.',
        'cover_image_url': 'https://images.unsplash.com/photo-1535378917042-10a22c95931a?w=1200&q=80',
    },
    {
        'title_es': 'El auge de los modelos de IA pequeños y eficientes',
        'title_en': 'The Rise of Small and Efficient AI Models',
        'excerpt_es': 'Todo lo que necesitas saber sobre los últimos avances en inteligencia artificial.',
        'excerpt_en': 'Everything you need to know about the latest advances in artificial intelligence.',
        'cover_image_url': 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1200&q=80',
    },
    {
        'title_es': 'IA y ciberseguridad: Amenazas y defensas en 2025',
        'title_en': 'AI and Cybersecurity: Threats and Defenses in 2025',
        'excerpt_es': 'Un vistazo a las innovaciones que marcarán el rumbo de la tecnología.',
        'excerpt_en': 'A look at the innovations that will shape the direction of technology.',
        'cover_image_url': 'https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=1200&q=80',
    },
]

CONTENT_TEMPLATES_ES = [
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

CONTENT_TEMPLATES_EN = [
    (
        '<h2>{topic}</h2>'
        '<p>Artificial intelligence continues to evolve at an impressive pace. '
        'The latest advances suggest a qualitative leap in the capabilities of '
        'modern systems, with profound implications for the industry.</p>'
        '<h3>Context and background</h3>'
        '<p>Over the past few months, we have witnessed an unprecedented acceleration '
        'in the development of AI models. Companies like OpenAI, Google '
        'and Meta are competing to lead the next generation of intelligent tools.</p>'
        '<h3>What can we expect?</h3>'
        '<p>Among the anticipated improvements are better context understanding, '
        'advanced multimodal capabilities, and more robust reasoning '
        'in complex real-world tasks.</p>'
        '<h3>Industry impact</h3>'
        '<p>These improvements will have direct implications in sectors such as software '
        'development, customer service, healthcare, and education. Companies '
        'that adopt these technologies early will have a significant competitive '
        'advantage.</p>'
    ),
    (
        '<h2>{topic}</h2>'
        '<p>The artificial intelligence ecosystem is experiencing fundamental changes '
        'that affect large corporations, startups, '
        'and individual developers alike.</p>'
        '<h3>Key innovations</h3>'
        '<ul>'
        '<li>Greater efficiency in model training</li>'
        '<li>Reduced computational costs</li>'
        '<li>Improved response quality</li>'
        '<li>New multimodal capabilities</li>'
        '</ul>'
        '<h3>Pending challenges</h3>'
        '<p>Despite the advances, reliability, security, and ethics remain '
        'important challenges that the industry must address before mass adoption '
        'in critical environments.</p>'
        '<h3>Future outlook</h3>'
        '<p>Analysts agree that we are only in the early stages of '
        'a transformation that will redefine the way we work, learn, '
        'and communicate.</p>'
    ),
    (
        '<h2>{topic}</h2>'
        '<p>The race for supremacy in artificial intelligence is intensifying, '
        'with new players entering the market and leaders consolidating their '
        'positions through significant advances.</p>'
        '<h3>Current market state</h3>'
        '<p>The generative AI market has exceeded expectations, with year-over-year '
        'growth surpassing 40%. AI infrastructure investments '
        'have reached record levels worldwide.</p>'
        '<h3>Opportunities for Latin America</h3>'
        '<p>The region has a unique opportunity to position itself as an AI '
        'talent hub. Countries like Colombia, Mexico, and Brazil are training '
        'highly competitive professionals in this field.</p>'
        '<blockquote>The democratization of AI is not just a promise — it is a '
        'reality that is transforming emerging economies.</blockquote>'
        '<h3>Conclusion</h3>'
        '<p>The future of AI is collaborative, accessible, and full of possibilities. '
        'Staying informed and adapting will be key to riding this wave.</p>'
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

CATEGORIES = [
    'technology', 'design', 'guides', 'business', 'case-study', 'ai', 'development',
    'marketing', 'startup', 'productivity', 'security', 'cloud', 'data',
    'no-code', 'trends', 'e-commerce', 'ux-ui',
]

CONTENT_JSON_TEMPLATES_ES = [
    {
        'intro': 'La inteligencia artificial continúa evolucionando a un ritmo impresionante con implicaciones profundas para múltiples industrias.',
        'sections': [
            {'heading': 'Contexto y antecedentes', 'content': 'Durante los últimos meses, hemos sido testigos de una aceleración sin precedentes en el desarrollo de modelos de IA.'},
            {'heading': 'Beneficios clave', 'list': ['Mayor eficiencia operativa', 'Reducción de costos', 'Automatización inteligente', 'Análisis predictivo avanzado']},
            {'heading': 'Proceso de implementación', 'timeline': [
                {'step': 'Evaluación inicial', 'description': 'Analizar las necesidades y oportunidades de IA en tu negocio.'},
                {'step': 'Diseño de solución', 'description': 'Crear una arquitectura personalizada basada en los requisitos.'},
                {'step': 'Desarrollo e integración', 'description': 'Implementar y conectar con los sistemas existentes.'},
            ]},
            {'heading': 'Casos de uso', 'examples': ['Chatbots con IA para atención al cliente', 'Sistemas de recomendación personalizados', 'Automatización de procesos repetitivos']},
        ],
        'conclusion': 'La IA no es solo una tendencia — es una herramienta fundamental para la competitividad empresarial en 2026.',
        'cta': '¿Listo para transformar tu negocio con IA? Agenda una consultoría gratuita.',
    },
    {
        'intro': 'El diseño de software moderno exige nuevas metodologías y herramientas que permitan crear productos digitales excepcionales.',
        'sections': [
            {'heading': 'El estado del arte', 'content': 'Las mejores prácticas de desarrollo han evolucionado significativamente en los últimos años.'},
            {'heading': 'Tecnologías emergentes', 'subsections': [
                {'title': 'Frameworks modernos', 'description': 'React, Vue, Next.js y Nuxt dominan el ecosistema frontend con arquitecturas más eficientes.'},
                {'title': 'Backend escalable', 'description': 'Django, FastAPI y Node.js ofrecen soluciones robustas para APIs y microservicios.'},
                {'title': 'DevOps y CI/CD', 'description': 'Automatización de despliegues con GitHub Actions, Docker y Kubernetes.'},
            ]},
            {'heading': 'Mejores prácticas', 'list': ['Testing automatizado desde el día 1', 'Documentación como código', 'Code reviews obligatorios', 'Monitoreo continuo en producción']},
        ],
        'conclusion': 'Invertir en buenas prácticas de desarrollo genera retornos exponenciales en calidad y velocidad de entrega.',
        'cta': 'Descubre cómo podemos elevar la calidad de tu producto digital.',
    },
    {
        'intro': 'La transformación digital ya no es opcional — es un requisito para la supervivencia empresarial en un mercado cada vez más competitivo.',
        'sections': [
            {'heading': '¿Por qué ahora?', 'content': 'Las empresas que no adoptan tecnología digital están perdiendo terreno frente a competidores más ágiles y conectados.'},
            {'heading': 'Pasos hacia la transformación', 'timeline': [
                {'step': 'Diagnóstico digital', 'description': 'Evaluar la madurez tecnológica actual de la organización.'},
                {'step': 'Estrategia digital', 'description': 'Definir objetivos claros y priorizados de transformación.'},
                {'step': 'Implementación gradual', 'description': 'Ejecutar por fases con medición continua de resultados.'},
                {'step': 'Optimización continua', 'description': 'Iterar basándose en datos y retroalimentación real.'},
            ]},
            {'heading': 'Resultados esperados', 'examples': ['Reducción del 40% en tiempos de respuesta al cliente', 'Aumento del 25% en conversiones digitales', 'Mejora del 60% en eficiencia operativa']},
        ],
        'conclusion': 'La transformación digital exitosa combina tecnología, procesos y personas en una estrategia coherente.',
        'cta': 'Hablemos sobre el futuro digital de tu empresa.',
    },
]

CONTENT_JSON_TEMPLATES_EN = [
    {
        'intro': 'Artificial intelligence continues to evolve at an impressive pace with profound implications for multiple industries.',
        'sections': [
            {'heading': 'Context and Background', 'content': 'Over the past few months, we have witnessed an unprecedented acceleration in AI model development.'},
            {'heading': 'Key Benefits', 'list': ['Greater operational efficiency', 'Cost reduction', 'Intelligent automation', 'Advanced predictive analytics']},
            {'heading': 'Implementation Process', 'timeline': [
                {'step': 'Initial Assessment', 'description': 'Analyze AI needs and opportunities in your business.'},
                {'step': 'Solution Design', 'description': 'Create a customized architecture based on requirements.'},
                {'step': 'Development & Integration', 'description': 'Implement and connect with existing systems.'},
            ]},
            {'heading': 'Use Cases', 'examples': ['AI chatbots for customer service', 'Personalized recommendation systems', 'Automation of repetitive processes']},
        ],
        'conclusion': 'AI is not just a trend — it is a fundamental tool for business competitiveness in 2026.',
        'cta': 'Ready to transform your business with AI? Schedule a free consultation.',
    },
    {
        'intro': 'Modern software design demands new methodologies and tools to create exceptional digital products.',
        'sections': [
            {'heading': 'State of the Art', 'content': 'Development best practices have evolved significantly in recent years.'},
            {'heading': 'Emerging Technologies', 'subsections': [
                {'title': 'Modern Frameworks', 'description': 'React, Vue, Next.js, and Nuxt dominate the frontend ecosystem with more efficient architectures.'},
                {'title': 'Scalable Backend', 'description': 'Django, FastAPI, and Node.js offer robust solutions for APIs and microservices.'},
                {'title': 'DevOps & CI/CD', 'description': 'Deployment automation with GitHub Actions, Docker, and Kubernetes.'},
            ]},
            {'heading': 'Best Practices', 'list': ['Automated testing from day 1', 'Documentation as code', 'Mandatory code reviews', 'Continuous production monitoring']},
        ],
        'conclusion': 'Investing in good development practices generates exponential returns in quality and delivery speed.',
        'cta': 'Discover how we can elevate your digital product quality.',
    },
    {
        'intro': 'Digital transformation is no longer optional — it is a requirement for business survival in an increasingly competitive market.',
        'sections': [
            {'heading': 'Why Now?', 'content': 'Companies that do not adopt digital technology are losing ground to more agile and connected competitors.'},
            {'heading': 'Steps Toward Transformation', 'timeline': [
                {'step': 'Digital Diagnosis', 'description': 'Assess the current technological maturity of the organization.'},
                {'step': 'Digital Strategy', 'description': 'Define clear and prioritized transformation goals.'},
                {'step': 'Gradual Implementation', 'description': 'Execute in phases with continuous measurement of results.'},
                {'step': 'Continuous Optimization', 'description': 'Iterate based on real data and feedback.'},
            ]},
            {'heading': 'Expected Results', 'examples': ['40% reduction in customer response times', '25% increase in digital conversions', '60% improvement in operational efficiency']},
        ],
        'conclusion': 'Successful digital transformation combines technology, processes, and people in a coherent strategy.',
        'cta': "Let's talk about your company's digital future.",
    },
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
            post_data = POSTS[i % len(POSTS)]
            title_es = post_data['title_es']
            title_en = post_data['title_en']

            # Append suffix to avoid slug collision when count > pool size
            if i >= len(POSTS):
                suffix = f' — Parte {i // len(POSTS) + 1}'
                title_es = f'{title_es}{suffix}'
                title_en = f'{title_en} — Part {i // len(POSTS) + 1}'

            # Skip if title already exists
            if BlogPost.objects.filter(title_es=title_es).exists():
                self.stdout.write(self.style.WARNING(
                    f'Already exists: "{title_es}"'
                ))
                continue

            excerpt_es = post_data['excerpt_es']
            excerpt_en = post_data['excerpt_en']
            template_es = CONTENT_TEMPLATES_ES[i % len(CONTENT_TEMPLATES_ES)]
            template_en = CONTENT_TEMPLATES_EN[i % len(CONTENT_TEMPLATES_EN)]
            content_es = template_es.format(topic=title_es)
            content_en = template_en.format(topic=title_en)
            sources = random.sample(SOURCES_POOL, k=random.randint(2, 4))

            # New fields: category, read_time, is_featured, content_json, SEO
            category = CATEGORIES[i % len(CATEGORIES)]
            read_time_minutes = random.randint(3, 15)
            is_featured = (i == 0)  # First post is featured

            # Content format mix: 0-3 = JSON+HTML, 4-6 = JSON only, 7-9 = HTML only
            mode = i % 10
            content_json_es = {}
            content_json_en = {}
            if mode <= 6:
                content_json_es = CONTENT_JSON_TEMPLATES_ES[i % len(CONTENT_JSON_TEMPLATES_ES)]
                content_json_en = CONTENT_JSON_TEMPLATES_EN[i % len(CONTENT_JSON_TEMPLATES_EN)]
            if mode >= 4 and mode <= 6:
                content_es = ''
                content_en = ''

            # SEO fields for ~50% of posts
            meta_title_es = ''
            meta_title_en = ''
            meta_description_es = ''
            meta_description_en = ''
            if i % 2 == 0:
                meta_title_es = f'{title_es} | Project App Blog'
                meta_title_en = f'{title_en} | Project App Blog'
                meta_description_es = excerpt_es[:160]
                meta_description_en = excerpt_en[:160]

            # ~80% published, 20% draft
            is_published = (i % 5) != 4
            published_at = (
                now - timedelta(days=i * 3 + random.randint(0, 2))
                if is_published else None
            )

            BlogPost.objects.create(
                title_es=title_es,
                title_en=title_en,
                excerpt_es=excerpt_es,
                excerpt_en=excerpt_en,
                content_es=content_es,
                content_en=content_en,
                content_json_es=content_json_es,
                content_json_en=content_json_en,
                cover_image_url=post_data.get('cover_image_url', ''),
                sources=sources,
                category=category,
                read_time_minutes=read_time_minutes,
                is_featured=is_featured,
                meta_title_es=meta_title_es,
                meta_title_en=meta_title_en,
                meta_description_es=meta_description_es,
                meta_description_en=meta_description_en,
                is_published=is_published,
                published_at=published_at,
            )
            fmt = 'json' if content_json_es else 'html'
            status_label = 'published' if is_published else 'draft'
            created += 1
            self.stdout.write(self.style.SUCCESS(
                f'[{status_label:>9}] [{fmt:>4}] [{category:>12}] "{title_es}"'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Created {created} blog post(s).'
        ))
