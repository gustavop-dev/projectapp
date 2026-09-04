from django.db import migrations
from django.db.models import Max


MODULES = [
    {
        'category': 'marketing-acquisition',
        'slug': 'audiovisual-experiences',
        'icon': '🎬',
        'name_es': 'Experiencias audiovisuales',
        'name_en': 'Audiovisual experiences',
        'summary_es': 'Convierte lo que cuesta explicar en una pieza audiovisual breve que se entiende en una sola pasada.',
        'summary_en': 'Turn what is hard to explain into a short audiovisual piece that lands in a single viewing.',
        'what_is_es': 'Una producción de piezas audiovisuales cortas, hechas a la medida de la marca, que muestran en movimiento una vista, una funcionalidad o un mensaje que en texto queda largo o pasa desapercibido. Es un trabajo colaborativo que se arma con recursos propios de la marca.',
        'what_is_en': 'A production of short, brand-tailored audiovisual pieces that show a view, a feature, or a message in motion when text alone runs long or goes unnoticed. It is collaborative work, built from the brand’s own material.',
        'purpose_es': 'Lograr que quien entra entienda de un vistazo de qué trata lo que está viendo, sin leer todo ni pedir explicaciones, y se lleve una impresión de marca cuidada.',
        'purpose_en': 'Let visitors grasp at a glance what they are looking at, without reading everything or asking for an explanation, and leave with a polished brand impression.',
        'problems_solved_es': [
            'Evita que una vista con mucho contenido se abandone antes de entender qué ofrece.',
            'Reduce las explicaciones repetidas sobre qué hace cada parte de la plataforma.',
            'Convierte una funcionalidad difícil de contar por escrito en algo que se entiende viéndolo.',
        ],
        'problems_solved_en': [
            'Prevents a content-heavy view from being abandoned before its value is understood.',
            'Reduces repeated explanations about what each part of the platform does.',
            'Turns a feature that is hard to describe in writing into something understood by watching.',
        ],
        'integrations_es': [
            'Vistas públicas, propuestas, landing pages y páginas de producto.',
            'Redes sociales, campañas publicitarias, correo y WhatsApp.',
            'Presentaciones comerciales y material de bienvenida para nuevos usuarios.',
        ],
        'integrations_en': [
            'Public views, proposals, landing pages, and product pages.',
            'Social media, advertising campaigns, email, and WhatsApp.',
            'Sales presentations and onboarding material for new users.',
        ],
        'implementation_requirements_es': [
            'Identidad de marca disponible: logo, paleta de colores y tipografías.',
            'Material propio existente: fotos, videos, capturas o piezas anteriores.',
            'Mensajes clave definidos: qué resaltar, en qué tono y con qué textos base.',
            'Acceso a la plataforma o a un entorno de demostración para grabar el producto real.',
            'Paquete de trabajo elegido: los paquetes iniciales son de 4, 8 y 16 recursos audiovisuales.',
            'Paquetes disponibles consultados con el representante comercial antes de empezar.',
        ],
        'implementation_requirements_en': [
            'Brand identity available: logo, color palette, and typography.',
            'Existing own material: photos, videos, screen captures, or previous pieces.',
            'Defined key messages: what to highlight, in what tone, and with what base copy.',
            'Access to the platform or a demo environment to record the real product.',
            'Chosen work package: initial packages are 4, 8, and 16 audiovisual assets.',
            'Available packages reviewed with the sales representative before starting.',
        ],
    },
]


def seed_audiovisual_module(apps, _schema_editor):
    Category = apps.get_model('content', 'AdditionalModuleCategory')
    Module = apps.get_model('content', 'AdditionalModule')
    categories = {
        category.slug: category
        for category in Category.objects.filter(
            slug__in={row['category'] for row in MODULES},
        )
    }
    missing = {row['category'] for row in MODULES} - set(categories)
    if missing:
        raise RuntimeError(
            f'Cannot seed audiovisual module; missing categories: {sorted(missing)}',
        )

    next_orders = {}
    for category in categories.values():
        maximum = Module.objects.filter(category=category).aggregate(
            value=Max('order'),
        )['value']
        next_orders[category.pk] = (maximum if maximum is not None else -1) + 1

    for row in MODULES:
        values = dict(row)
        category = categories[values.pop('category')]
        slug = values.pop('slug')
        if Module.objects.filter(slug=slug).exists():
            continue
        Module.objects.create(
            category=category,
            slug=slug,
            order=next_orders[category.pk],
            is_active=True,
            **values,
        )
        next_orders[category.pk] += 1


def unseed_audiovisual_module(apps, _schema_editor):
    Module = apps.get_model('content', 'AdditionalModule')
    Module.objects.filter(slug__in=[row['slug'] for row in MODULES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0246_multi_recipient_email_delivery'),
    ]

    operations = [
        migrations.RunPython(seed_audiovisual_module, unseed_audiovisual_module),
    ]
