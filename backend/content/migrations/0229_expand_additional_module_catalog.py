from django.db import migrations
from django.db.models import Max


MODULES = [
    {
        'category': 'marketing-acquisition',
        'slug': 'sales-crm-pipeline',
        'icon': '🎯',
        'name_es': 'CRM y embudo comercial',
        'name_en': 'CRM and sales pipeline',
        'summary_es': 'Centraliza prospectos, oportunidades y próximos pasos desde el primer contacto hasta el cierre.',
        'summary_en': 'Centralize leads, opportunities, and next steps from first contact through closing.',
        'what_is_es': 'Un espacio comercial que organiza contactos, oportunidades, etapas, responsables, actividad y tareas de seguimiento en un solo embudo.',
        'what_is_en': 'A sales workspace that organizes contacts, opportunities, stages, owners, activity, and follow-up tasks in one pipeline.',
        'purpose_es': 'Dar continuidad a cada oportunidad y hacer visible qué debe ocurrir después, quién responde y qué tan cerca está el cierre.',
        'purpose_en': 'Keep every opportunity moving and make the next action, owner, and proximity to closing visible.',
        'problems_solved_es': [
            'Evita que prospectos y conversaciones queden dispersos entre hojas, chats y correos.',
            'Reduce seguimientos olvidados al asignar responsables, fechas y próximos pasos.',
            'Hace visible el estado del embudo y permite proyectar oportunidades con información real.',
        ],
        'problems_solved_en': [
            'Prevents leads and conversations from being scattered across sheets, chats, and email.',
            'Reduces missed follow-ups by assigning owners, dates, and next steps.',
            'Makes pipeline status visible and supports forecasting from real opportunity data.',
        ],
        'integrations_es': [
            'Formularios, correo, WhatsApp, agenda y fuentes publicitarias.',
            'Clientes, propuestas, cotizaciones y tareas de la plataforma.',
            'Analítica comercial y reportes de conversión por etapa y origen.',
        ],
        'integrations_en': [
            'Forms, email, WhatsApp, calendars, and advertising sources.',
            'Platform clients, proposals, quotes, and tasks.',
            'Sales analytics and conversion reports by stage and source.',
        ],
        'implementation_requirements_es': [
            'Etapas, responsables, criterios de avance y tiempos de seguimiento definidos.',
            'Campos obligatorios y fuentes de datos o importación acordados.',
            'Permisos, privacidad y política de conservación del historial comercial.',
        ],
        'implementation_requirements_en': [
            'Defined stages, owners, advancement criteria, and follow-up times.',
            'Agreed required fields and data or import sources.',
            'Permissions, privacy, and a retention policy for sales history.',
        ],
    },
    {
        'category': 'commerce-transactions',
        'slug': 'scheduling-bookings',
        'icon': '📅',
        'name_es': 'Agenda, reservas y disponibilidad',
        'name_en': 'Scheduling, bookings, and availability',
        'summary_es': 'Publica disponibilidad y permite reservar, reprogramar o cancelar sin coordinación manual.',
        'summary_en': 'Publish availability and let people book, reschedule, or cancel without manual coordination.',
        'what_is_es': 'Un módulo de agenda que combina servicios, recursos, horarios y reglas de disponibilidad para confirmar reservas sin cruces.',
        'what_is_en': 'A scheduling module that combines services, resources, working hours, and availability rules to confirm bookings without conflicts.',
        'purpose_es': 'Convertir la coordinación de citas o cupos en un flujo autónomo, medible y conectado con la operación.',
        'purpose_en': 'Turn appointment or capacity coordination into a self-service, measurable flow connected to operations.',
        'problems_solved_es': [
            'Elimina intercambios repetidos para encontrar una hora disponible.',
            'Evita dobles reservas y respeta duración, capacidad y tiempos de preparación.',
            'Reduce ausencias con confirmaciones, recordatorios y reglas de cancelación.',
        ],
        'problems_solved_en': [
            'Removes repeated exchanges to find an available time.',
            'Prevents double bookings and respects duration, capacity, and preparation time.',
            'Reduces no-shows through confirmations, reminders, and cancellation rules.',
        ],
        'integrations_es': [
            'Google Calendar, Outlook, videollamadas o calendarios del equipo.',
            'Clientes, servicios, sedes, recursos y pasarelas de pago.',
            'Correo, WhatsApp y notificaciones para confirmaciones y recordatorios.',
        ],
        'integrations_en': [
            'Google Calendar, Outlook, video calls, or team calendars.',
            'Customers, services, locations, resources, and payment gateways.',
            'Email, WhatsApp, and notifications for confirmations and reminders.',
        ],
        'implementation_requirements_es': [
            'Horarios, zonas horarias, duraciones, capacidad y tiempos de margen definidos.',
            'Políticas de pago, reprogramación, cancelación y ausencia acordadas.',
            'Cuentas y permisos de los calendarios o proveedores que se integrarán.',
        ],
        'implementation_requirements_en': [
            'Defined schedules, time zones, durations, capacity, and buffer times.',
            'Agreed payment, rescheduling, cancellation, and no-show policies.',
            'Accounts and permissions for the calendars or providers to integrate.',
        ],
    },
    {
        'category': 'commerce-transactions',
        'slug': 'memberships-subscriptions',
        'icon': '🔁',
        'name_es': 'Membresías y suscripciones',
        'name_en': 'Memberships and subscriptions',
        'summary_es': 'Administra planes recurrentes, renovaciones y acceso según el estado real de cada suscripción.',
        'summary_en': 'Manage recurring plans, renewals, and access based on each subscription’s real status.',
        'what_is_es': 'Un módulo para vender y operar planes periódicos con ciclos, pruebas, cobros, renovaciones, pausas, cancelaciones y beneficios asociados.',
        'what_is_en': 'A module for selling and operating recurring plans with cycles, trials, charges, renewals, pauses, cancellations, and associated benefits.',
        'purpose_es': 'Sostener ingresos recurrentes y mantener sincronizados el pago, la vigencia y los permisos que recibe cada miembro.',
        'purpose_en': 'Support recurring revenue while keeping payment, validity, and member entitlements synchronized.',
        'problems_solved_es': [
            'Evita controlar renovaciones y vencimientos de forma manual.',
            'Impide que el acceso quede activo cuando el pago falló o la membresía terminó.',
            'Hace visibles cancelaciones, reintentos, retención y motivos de pérdida.',
        ],
        'problems_solved_en': [
            'Avoids manually controlling renewals and expiration dates.',
            'Prevents access from remaining active after a failed payment or ended membership.',
            'Makes cancellations, retries, retention, and churn reasons visible.',
        ],
        'integrations_es': [
            'Pasarelas de pago, facturación y conciliación.',
            'Cuentas, roles, contenido, servicios o beneficios de la plataforma.',
            'Correo, notificaciones y analítica de renovaciones y cancelaciones.',
        ],
        'integrations_en': [
            'Payment gateways, invoicing, and reconciliation.',
            'Platform accounts, roles, content, services, or benefits.',
            'Email, notifications, and renewal and cancellation analytics.',
        ],
        'implementation_requirements_es': [
            'Planes, periodicidades, pruebas, precios y reglas de prorrateo definidos.',
            'Reglas de acceso, pausa, cancelación, cobro fallido y reactivación.',
            'Tratamiento fiscal, cuenta de recaudo y comunicaciones del ciclo acordados.',
        ],
        'implementation_requirements_en': [
            'Defined plans, billing periods, trials, prices, and proration rules.',
            'Rules for access, pauses, cancellation, failed charges, and reactivation.',
            'Agreed tax treatment, collection account, and lifecycle communications.',
        ],
    },
    {
        'category': 'identity-access',
        'slug': 'customer-self-service',
        'icon': '🧑‍💻',
        'name_es': 'Portal de autoservicio para clientes',
        'name_en': 'Customer self-service portal',
        'summary_es': 'Reúne solicitudes, documentos, pagos y estados en un espacio seguro para cada cliente.',
        'summary_en': 'Bring requests, documents, payments, and statuses into one secure space for each customer.',
        'what_is_es': 'Un área autenticada donde cada cliente consulta su información, realiza solicitudes, descarga documentos y sigue procesos sin depender de atención manual.',
        'what_is_en': 'An authenticated area where each customer reviews information, submits requests, downloads documents, and follows processes without relying on manual support.',
        'purpose_es': 'Dar autonomía al cliente y ofrecer una fuente única y segura para la información que necesita durante la relación comercial.',
        'purpose_en': 'Give customers autonomy and provide one secure source for the information they need throughout the relationship.',
        'problems_solved_es': [
            'Evita repartir solicitudes y archivos entre correos, chats y carpetas aisladas.',
            'Reduce preguntas repetidas sobre estados, saldos o próximos pasos.',
            'Entrega documentos y datos sensibles sólo a usuarios autorizados.',
        ],
        'problems_solved_en': [
            'Prevents requests and files from being scattered across email, chats, and isolated folders.',
            'Reduces repeated questions about status, balances, or next steps.',
            'Delivers documents and sensitive data only to authorized users.',
        ],
        'integrations_es': [
            'Identidad, roles, recuperación de acceso y verificación de correo.',
            'CRM, pedidos, soporte, documentos, proyectos y pagos.',
            'Correo, notificaciones y registro de actividad del cliente.',
        ],
        'integrations_en': [
            'Identity, roles, access recovery, and email verification.',
            'CRM, orders, support, documents, projects, and payments.',
            'Email, notifications, and customer activity history.',
        ],
        'implementation_requirements_es': [
            'Audiencias, permisos y responsabilidades de cada tipo de usuario definidos.',
            'Procesos, estados y datos que el cliente podrá consultar o modificar.',
            'Políticas de privacidad, retención, soporte y cierre de cuentas.',
        ],
        'implementation_requirements_en': [
            'Defined audiences, permissions, and responsibilities for each user type.',
            'Processes, statuses, and data customers may view or change.',
            'Privacy, retention, support, and account closure policies.',
        ],
    },
    {
        'category': 'marketing-acquisition',
        'slug': 'loyalty-referrals',
        'icon': '⭐',
        'name_es': 'Fidelización y referidos',
        'name_en': 'Loyalty and referral program',
        'summary_es': 'Reconoce compras y recomendaciones con puntos, niveles o beneficios medibles.',
        'summary_en': 'Reward purchases and recommendations with measurable points, tiers, or benefits.',
        'what_is_es': 'Un programa que registra acciones verificadas, asigna recompensas y relaciona cada referido con su origen, conversión y beneficio.',
        'what_is_en': 'A program that records verified actions, grants rewards, and connects every referral with its source, conversion, and benefit.',
        'purpose_es': 'Aumentar recurrencia y recomendación mediante reglas transparentes que el cliente puede consultar y usar.',
        'purpose_en': 'Increase repeat business and referrals through transparent rules customers can review and use.',
        'problems_solved_es': [
            'Evita que las compras recurrentes no reciban reconocimiento ni incentivo.',
            'Permite atribuir referidos y recompensarlos sin validación manual.',
            'Centraliza saldos, niveles, vencimientos, canjes y resultados de campaña.',
        ],
        'problems_solved_en': [
            'Prevents repeat purchases from going unrecognized or unrewarded.',
            'Attributes referrals and rewards them without manual validation.',
            'Centralizes balances, tiers, expiration, redemption, and campaign results.',
        ],
        'integrations_es': [
            'Clientes, pedidos, pagos y acciones verificadas de la plataforma.',
            'Cupones, campañas, email y notificaciones.',
            'Analítica de recurrencia, referidos, canjes y prevención de fraude.',
        ],
        'integrations_en': [
            'Customers, orders, payments, and verified platform actions.',
            'Coupons, campaigns, email, and notifications.',
            'Repeat-purchase, referral, redemption, and fraud-prevention analytics.',
        ],
        'implementation_requirements_es': [
            'Reglas de acumulación, niveles, canje, vencimiento y exclusiones definidas.',
            'Tratamiento contable y fiscal de puntos, saldos y beneficios.',
            'Controles de abuso, privacidad y responsables de atención de reclamos.',
        ],
        'implementation_requirements_en': [
            'Defined earning, tier, redemption, expiration, and exclusion rules.',
            'Accounting and tax treatment for points, balances, and benefits.',
            'Abuse controls, privacy rules, and ownership of customer claims.',
        ],
    },
]


def seed_catalog_expansion(apps, _schema_editor):
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
            f'Cannot expand additional modules; missing categories: {sorted(missing)}',
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


def unseed_catalog_expansion(apps, _schema_editor):
    Module = apps.get_model('content', 'AdditionalModule')
    Module.objects.filter(slug__in=[row['slug'] for row in MODULES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0228_emaillinksnapshot_url_sha256'),
    ]

    operations = [
        migrations.RunPython(seed_catalog_expansion, unseed_catalog_expansion),
    ]
