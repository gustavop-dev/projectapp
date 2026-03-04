import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default section configurations extracted from existing Vue component props.
# Each entry maps to the content_json stored in ProposalSection.
# ---------------------------------------------------------------------------

DEFAULT_SECTIONS = [
    {
        'section_type': 'greeting',
        'title': 'Greeting',
        'order': 0,
        'is_wide_panel': False,
        'content_json': {
            'clientName': '',
            'inspirationalQuote': (
                'Design is not just what it looks like and feels like. '
                'Design is how it works.'
            ),
        },
    },
    {
        'section_type': 'executive_summary',
        'title': 'Executive Summary',
        'order': 1,
        'is_wide_panel': False,
        'content_json': {
            'index': '01',
            'title': 'Resumen ejecutivo',
            'paragraphs': [
                'Nuestra propuesta contempla el diseño y desarrollo de un sitio web profesional.',
            ],
            'highlightsTitle': 'Incluye',
            'highlights': [
                'Diseño visual personalizado',
                'Desarrollo web responsivo',
                'Optimización SEO básica',
            ],
        },
    },
    {
        'section_type': 'context_diagnostic',
        'title': 'Context & Diagnostic',
        'order': 2,
        'is_wide_panel': False,
        'content_json': {
            'index': '02',
            'title': 'Contexto y diagnóstico',
            'paragraphs': [
                'El cliente busca fortalecer su presencia digital con un sitio web que refleje su identidad profesional.',
            ],
            'issuesTitle': 'Desafíos identificados',
            'issues': [
                'Ausencia de presencia digital profesional',
                'Dificultad para captar clientes en línea',
            ],
            'opportunityTitle': 'Oportunidad',
            'opportunity': (
                'Crear una plataforma digital que genere confianza y convierta visitantes en clientes.'
            ),
        },
    },
    {
        'section_type': 'conversion_strategy',
        'title': 'Conversion Strategy',
        'order': 3,
        'is_wide_panel': False,
        'content_json': {
            'index': '03',
            'title': 'Enfoque propuesto y estrategia de conversión',
            'intro': (
                'La página se construirá como una herramienta para generar confianza '
                'y convertir visitas en conversaciones.'
            ),
            'steps': [
                {
                    'title': '👀 Captar atención en los primeros segundos',
                    'bullets': [
                        'Mensaje principal claro: qué hace el cliente y a quién ayuda',
                        'Beneficio directo visible',
                        'Botón visible de contacto',
                    ],
                },
                {
                    'title': '🤝 Construir confianza rápidamente',
                    'bullets': [
                        'Sección breve de "Quién soy"',
                        'Señales de credibilidad',
                        'Lenguaje simple, centrado en resolver problemas reales',
                    ],
                },
                {
                    'title': '🧾 Presentar servicios como "soluciones"',
                    'bullets': [
                        'Servicios organizados por necesidades',
                        'Para cada servicio: qué incluye / para quién es',
                        'Contenido corto y escaneable',
                    ],
                },
                {
                    'title': '🖼️ Mantener contenido fresco',
                    'bullets': [
                        'Autogestión para actualizar imágenes y/o videos',
                        'Ideal para renovar material sin ayuda técnica',
                    ],
                },
            ],
            'resultTitle': '🎯 Resultado esperado',
            'result': (
                'Una página que no solo "se vea bonita", sino que genere contactos, '
                'transmita profesionalismo y haga fácil que la gente diga: "Listo, le escribo".'
            ),
        },
    },
    {
        'section_type': 'design_ux',
        'title': 'Design & UX',
        'order': 4,
        'is_wide_panel': False,
        'content_json': {
            'index': '04',
            'title': 'Diseño visual y experiencia de usuario',
            'paragraphs': [
                'El desarrollo web será concebido como una experiencia digital profesional.',
                'Cada sección será creada cuidadosamente para generar un recorrido fluido.',
            ],
            'focusTitle': 'Estructura que resalta',
            'focusItems': [
                'Presentación clara del servicio',
                'Integración con redes sociales',
                'Espacio para agendar citas o consultas',
            ],
            'objectiveTitle': 'Objetivo',
            'objective': (
                'Inspirar confianza desde el primer momento, reflejando autenticidad '
                'y la profundidad del mensaje.'
            ),
        },
    },
    {
        'section_type': 'creative_support',
        'title': 'Creative Support',
        'order': 5,
        'is_wide_panel': False,
        'content_json': {
            'index': '05',
            'title': 'Acompañamiento creativo personalizado',
            'paragraphs': [
                'Durante todo el proceso, el cliente contará con el acompañamiento cercano de nuestro equipo.',
                'El proceso será colaborativo, cálido y empático.',
            ],
            'includesTitle': 'Incluye',
            'includes': [
                '💡 Sesiones de revisión y retroalimentación sobre diseño y estructura.',
                '🎨 Apoyo en la selección de paleta de colores, tipografía y estilo visual.',
                '🕊 Adaptaciones según la evolución de las ideas.',
                '🔗 Aseguramiento de coherencia entre estética, contenido y propósito.',
            ],
            'closing': (
                'Cada decisión será una co-creación, en la que el cliente podrá participar '
                'activamente para que el resultado final refleje fielmente su mensaje.'
            ),
        },
    },
    {
        'section_type': 'development_stages',
        'title': 'Development Stages',
        'order': 6,
        'is_wide_panel': True,
        'content_json': {
            'stages': [
                {
                    'icon': '✉️',
                    'title': 'Propuesta Comercial',
                    'description': 'Presentación formal de la propuesta técnica y económica (etapa actual).',
                    'current': True,
                },
                {
                    'icon': '🧾',
                    'title': 'Borrador de Contrato',
                    'description': 'Envío del documento que establece los términos, condiciones y compromisos.',
                },
                {
                    'icon': '✍️',
                    'title': 'Formalización del Contrato',
                    'description': 'Firma del acuerdo y confirmación del inicio oficial del proyecto.',
                },
                {
                    'icon': '🎨',
                    'title': 'Etapa de Diseño',
                    'description': 'Creación del prototipo visual en Figma con reuniones de revisión.',
                },
                {
                    'icon': '💻',
                    'title': 'Etapa de Desarrollo',
                    'description': 'Implementación del diseño en código nativo, optimizado para la mejor experiencia.',
                },
                {
                    'icon': '🚀',
                    'title': 'Despliegue del Proyecto',
                    'description': 'Publicación del sitio web en producción y revisión final.',
                },
                {
                    'icon': '💖',
                    'title': 'Entrega Final',
                    'description': 'Sitio en línea y validado, cierre del ciclo de transformación digital.',
                },
            ],
        },
    },
    {
        'section_type': 'functional_requirements',
        'title': 'Functional Requirements',
        'order': 7,
        'is_wide_panel': True,
        'content_json': {
            'index': '07',
            'title': 'Requerimientos funcionales',
            'intro': 'A continuación se detallan los requerimientos funcionales del proyecto.',
            'technicalSpecs': [],
            'integrations': [],
        },
    },
    {
        'section_type': 'timeline',
        'title': 'Timeline',
        'order': 8,
        'is_wide_panel': True,
        'content_json': {
            'introText': 'El proyecto se desarrollará en las siguientes fases:',
            'totalDuration': '8 semanas',
            'phases': [
                {
                    'title': 'Discovery & Diseño',
                    'duration': '2 semanas',
                    'weeks': [1, 2],
                    'circleColor': '#059669',
                    'statusColor': '#d1fae5',
                    'description': 'Investigación, wireframes y diseño visual.',
                    'tasks': ['Kickoff', 'Wireframes', 'Diseño UI'],
                    'milestone': 'Diseño aprobado',
                },
                {
                    'title': 'Desarrollo',
                    'duration': '4 semanas',
                    'weeks': [3, 4, 5, 6],
                    'circleColor': '#0284c7',
                    'statusColor': '#dbeafe',
                    'description': 'Implementación frontend y backend.',
                    'tasks': ['Frontend', 'Backend', 'Integraciones'],
                    'milestone': 'MVP funcional',
                },
                {
                    'title': 'QA & Launch',
                    'duration': '2 semanas',
                    'weeks': [7, 8],
                    'circleColor': '#7c3aed',
                    'statusColor': '#ede9fe',
                    'description': 'Testing, ajustes finales y despliegue.',
                    'tasks': ['QA', 'Ajustes', 'Deploy'],
                    'milestone': 'Sitio en producción',
                },
            ],
            'calendarWeeks': [],
        },
    },
    {
        'section_type': 'investment',
        'title': 'Investment',
        'order': 9,
        'is_wide_panel': False,
        'content_json': {
            'introText': 'La inversión total para este proyecto es:',
            'totalInvestment': '',
            'currency': 'COP',
            'whatsIncluded': [
                'Diseño personalizado',
                'Desarrollo responsivo',
                'Hosting primer año',
            ],
            'paymentOptions': [
                {'label': '50% al iniciar', 'description': 'Al firmar el contrato'},
                {'label': '50% al entregar', 'description': 'Al aprobar el sitio'},
            ],
            'hostingPlan': {},
            'paymentMethods': [
                'Transferencia bancaria',
                'Nequi / Daviplata',
            ],
            'valueReasons': [
                'Diseño hecho a medida',
                'Código optimizado',
                'Soporte post-lanzamiento',
            ],
        },
    },
    {
        'section_type': 'final_note',
        'title': 'Final Note',
        'order': 10,
        'is_wide_panel': False,
        'content_json': {
            'message': (
                'Creemos firmemente que esta propuesta representa una oportunidad excepcional '
                'para transformar tu presencia digital y alcanzar tus objetivos de negocio.'
            ),
            'personalNote': (
                'Estamos emocionados por la posibilidad de trabajar contigo y ayudarte '
                'a llevar tu negocio al siguiente nivel.'
            ),
            'teamName': 'El equipo de Project App',
            'teamRole': 'Tu socio en transformación digital',
            'contactEmail': 'hello@projectapp.co',
            'commitmentBadges': [
                {
                    'icon': '🤝',
                    'title': 'Compromiso Total',
                    'description': 'Dedicación completa a tu proyecto hasta lograr resultados excepcionales',
                },
                {
                    'icon': '💯',
                    'title': 'Garantía de Calidad',
                    'description': 'Revisiones ilimitadas hasta tu completa satisfacción',
                },
                {
                    'icon': '🎯',
                    'title': 'Enfoque en Resultados',
                    'description': 'Medimos nuestro éxito por el impacto en tu negocio',
                },
            ],
        },
    },
    {
        'section_type': 'next_steps',
        'title': 'Next Steps',
        'order': 11,
        'is_wide_panel': False,
        'content_json': {
            'introMessage': (
                'Estamos listos para comenzar este viaje juntos. '
                'Aquí te explicamos cómo dar el siguiente paso:'
            ),
            'steps': [
                {
                    'title': 'Revisión y Preguntas',
                    'description': 'Revisa la propuesta y envíanos cualquier pregunta o ajuste que necesites.',
                },
                {
                    'title': 'Reunión de Confirmación',
                    'description': 'Agendamos una llamada para alinear detalles finales y firmar el contrato.',
                },
                {
                    'title': '¡Comenzamos!',
                    'description': 'Iniciamos el proyecto con la reunión de kickoff.',
                },
            ],
            'ctaMessage': (
                'Contáctanos hoy mismo y comencemos a trabajar en tu proyecto. '
                'Estamos a solo un mensaje de distancia.'
            ),
            'primaryCTA': {
                'text': 'Contactar por WhatsApp',
                'link': 'https://wa.me/573238122373',
            },
            'secondaryCTA': {
                'text': 'Agendar Reunión',
                'link': 'https://calendly.com/projectapp',
            },
            'contactMethods': [
                {
                    'icon': '📧',
                    'title': 'Email',
                    'value': 'hello@projectapp.co',
                    'link': 'mailto:hello@projectapp.co',
                },
                {
                    'icon': '📱',
                    'title': 'WhatsApp',
                    'value': '+57 323 812 2373',
                    'link': 'https://wa.me/573238122373',
                },
                {
                    'icon': '🌐',
                    'title': 'Website',
                    'value': 'www.projectapp.co',
                    'link': 'https://projectapp.co',
                },
            ],
            'validityMessage': (
                'Esta propuesta es válida por 30 días a partir de la fecha de emisión. '
                'Los precios y condiciones pueden estar sujetos a cambios después de este período.'
            ),
            'thankYouMessage': (
                'Apreciamos sinceramente la oportunidad de presentarte esta propuesta. '
                'Esperamos con entusiasmo la posibilidad de trabajar contigo.'
            ),
        },
    },
]


class ProposalService:
    """
    Business logic for proposal lifecycle management.
    """

    @staticmethod
    def send_proposal(proposal):
        """
        Mark proposal as sent and schedule the Huey reminder task.

        Sets status=SENT, sent_at=now(), and schedules the reminder email
        for reminder_days days later.

        Args:
            proposal: BusinessProposal instance.

        Raises:
            ValueError: If client_email is not set.
        """
        if not proposal.client_email:
            raise ValueError('Client email is required to send a proposal.')

        proposal.status = 'sent'
        proposal.sent_at = timezone.now()
        proposal.save(update_fields=['status', 'sent_at'])

        # Schedule the reminder email via Huey
        try:
            from content.tasks import send_proposal_reminder
            delay_seconds = int(
                timedelta(days=proposal.reminder_days).total_seconds()
            )
            send_proposal_reminder.schedule(
                args=(proposal.id,), delay=delay_seconds
            )
            logger.info(
                'Scheduled reminder for proposal %s in %d days',
                proposal.uuid, proposal.reminder_days,
            )
        except Exception:
            logger.exception(
                'Failed to schedule reminder for proposal %s', proposal.uuid
            )

    @staticmethod
    def record_view(proposal):
        """
        Record a client viewing the proposal.

        Increments view_count, sets first_viewed_at on first visit,
        updates status to VIEWED if currently SENT.
        """
        proposal.view_count += 1
        update_fields = ['view_count']

        if proposal.first_viewed_at is None:
            proposal.first_viewed_at = timezone.now()
            update_fields.append('first_viewed_at')

        if proposal.status == 'sent':
            proposal.status = 'viewed'
            update_fields.append('status')

        proposal.save(update_fields=update_fields)

    @staticmethod
    def check_expiration(proposal):
        """
        Check if a proposal is expired.

        Returns:
            bool: True if expired.
        """
        return proposal.is_expired

    @staticmethod
    def get_default_sections():
        """
        Return the default section configurations for a new proposal.

        Returns:
            list[dict]: List of section configs with section_type, title, order,
                        is_wide_panel, and content_json.
        """
        import copy
        return copy.deepcopy(DEFAULT_SECTIONS)
