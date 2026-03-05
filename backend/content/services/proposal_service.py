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
        'title': '👋 Greeting',
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
        'title': '🧾 Resumen ejecutivo',
        'order': 1,
        'is_wide_panel': False,
        'content_json': {
            'index': '1',
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
        'title': '🧩 Contexto y diagnóstico',
        'order': 2,
        'is_wide_panel': False,
        'content_json': {
            'index': '2',
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
        'title': '🚀 Enfoque propuesto y estrategia de conversión',
        'order': 3,
        'is_wide_panel': False,
        'content_json': {
            'index': '3',
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
        'title': '🎨 Diseño Visual y Experiencia de Usuario',
        'order': 4,
        'is_wide_panel': False,
        'content_json': {
            'index': '4',
            'title': 'Diseño Visual y Experiencia de Usuario',
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
        'title': '🤝 Acompañamiento Creativo Personalizado',
        'order': 5,
        'is_wide_panel': False,
        'content_json': {
            'index': '5',
            'title': 'Acompañamiento Creativo Personalizado',
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
        'title': '📌 Etapas de Contratación y Desarrollo',
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
        'title': '🧩 Requerimientos Funcionales del Proyecto',
        'order': 7,
        'is_wide_panel': True,
        'content_json': {
            'index': '7',
            'title': 'Requerimientos Funcionales del Proyecto',
            'intro': 'A continuación se detallan los requerimientos funcionales del proyecto.',
            'groups': [
                {
                    'id': 'views',
                    'icon': '🖥️',
                    'title': 'Vistas',
                    'description': (
                        'Cada vista es una pantalla o sección del sitio. Su propósito es guiar al visitante '
                        'para conocer la propuesta de valor y facilitar el contacto o la acción deseada.'
                    ),
                    'items': [
                        {'icon': '🏠', 'name': 'Inicio (Página de Aterrizaje)', 'description': 'Es la primera impresión del sitio. Aquí se presenta de forma clara la identidad de la marca, con un mensaje atractivo, llamado a la acción, y acceso rápido a las secciones principales.'},
                        {'icon': 'ℹ️', 'name': 'Acerca de Nosotros', 'description': 'Página dedicada a compartir la historia, misión, visión y valores de la empresa o proyecto. Ideal para generar confianza con el visitante.'},
                        {'icon': '📞', 'name': 'Contacto', 'description': 'Sección con un formulario para que los usuarios puedan enviar mensajes, junto con información de contacto (teléfono, correo, dirección) y un mapa si se desea incluir.'},
                        {'icon': '📜', 'name': 'Términos y Condiciones', 'description': 'Página para informar a los usuarios sobre las políticas del sitio, manejo de datos personales y términos de uso. Incluye un checkbox para aceptación, garantizando el cumplimiento de las normativas vigentes.'},
                        {'icon': '🛒', 'name': 'Categorías', 'description': 'Sección para mostrar las categorías disponibles de productos, permitiendo a los usuarios explorar los diferentes tipos de productos que ofrece el sitio.'},
                        {'icon': '�️', 'name': 'Catálogo por Categoría', 'description': 'Permite a los usuarios explorar los productos dentro de una categoría específica, facilitando la navegación y selección de productos relacionados.'},
                        {'icon': '📦', 'name': 'Vista de Productos', 'description': 'Muestra los detalles de un producto seleccionado, incluyendo imágenes, precio, características, descripciones y opciones para agregar al carrito.'},
                        {'icon': '🛒', 'name': 'Carrito de Compra', 'description': 'Permite a los usuarios ver los productos que han agregado, ajustar cantidades, eliminar artículos y proceder al pago.'},
                        {'icon': '📜', 'name': 'Historial de Compras', 'description': 'Permite a los usuarios revisar las compras realizadas, incluyendo detalles como fecha, monto y productos adquiridos.'},
                        {'icon': '👤', 'name': 'Registro de Usuario', 'description': 'Permite a los usuarios crear una cuenta para acceder a funciones personalizadas, como historial de compras y productos favoritos.'},
                        {'icon': '�', 'name': 'Inicio de Sesión', 'description': 'Proporciona acceso a usuarios registrados para gestionar sus compras y preferencias.'},
                        {'icon': '❤️', 'name': 'Lista de deseos Favoritos', 'description': 'Permite a los usuarios guardar productos para una rápida referencia en futuras visitas.'},
                        {'icon': '📝', 'name': 'Perfil del Usuario', 'description': 'Sección donde los usuarios pueden ver y actualizar su información personal, historial de compras y configuraciones de cuenta.'},
                    ],
                },
                {
                    'id': 'components',
                    'icon': '🧩',
                    'title': 'Componentes',
                    'description': (
                        'Los componentes son elementos visuales o funcionales que se reutilizan en varias '
                        'secciones del sitio. Esto mantiene una experiencia coherente y optimiza el desarrollo.'
                    ),
                    'items': [
                        {'icon': '🔝', 'name': 'Encabezado (Header)', 'description': 'Incluye el logotipo, menú de navegación y acceso rápido a redes sociales o secciones clave del sitio.'},
                        {'icon': '🔚', 'name': 'Pie de página (Footer)', 'description': 'Contiene información adicional como derechos de autor, políticas, enlaces a redes sociales y otros recursos útiles.'},
                        {'icon': '🎯', 'name': 'Carrusel de Productos destacados', 'description': 'Destaca productos seleccionados como promociones, ofertas especiales o productos estacionales para mejorar la visibilidad y el interés de los clientes.'},
                        {'icon': '🎁', 'name': 'Carrusel de lista de deseos destacadas', 'description': 'Destaca listas de deseos seleccionados como promociones, ofertas especiales o productos estacionales para mejorar la visibilidad y el interés de los clientes.'},
                        {'icon': '❓', 'name': 'Preguntas Frecuentes (FAQ)', 'description': 'Sección para responder las preguntas más comunes de los clientes y resolver dudas de manera rápida y eficiente.'},
                    ],
                },
                {
                    'id': 'features',
                    'icon': '⚙️',
                    'title': 'Funcionalidades Específicas',
                    'description': (
                        'Las funcionalidades son acciones o comportamientos interactivos del sitio web. '
                        'Le dan vida y dinamismo a la página, permitiendo que funcione de forma práctica y útil.'
                    ),
                    'items': [
                        {'icon': '🌐', 'name': 'Diseño Responsive', 'description': 'El sitio se adapta perfectamente a celulares, tablets y computadores. Esto es vital en el sector inmobiliario, donde la mayoría de las búsquedas iniciales ocurren desde dispositivos móviles. 📱💻'},
                        {'icon': '�', 'name': 'Registro e Inicio de Sesión con Google', 'description': 'Implementaremos un acceso simplificado que permite a los usuarios registrarse con un solo clic. Esta función es clave para capturar datos reales de los clientes interesados y conocer mejor sus preferencias. 🔐📧'},
                        {'icon': '🔎', 'name': 'Buscador Avanzado con Filtros Dinámicos', 'description': 'Los usuarios podrán filtrar inmuebles por zonas, rango de precios, metros cuadrados y características específicas. Esta navegación intuitiva ahorra tiempo al cliente y califica mejor el interés. 🔍📍'},
                        {'icon': '💬', 'name': 'WhatsApp Directo por Propiedad', 'description': 'En cada ficha de inmueble habrá un botón de contacto inmediato. Al hacer clic, se recibirá un mensaje predeterminado indicando exactamente por qué propiedad está preguntando el cliente. 📲⚡'},
                        {'icon': '🖼️', 'name': 'Visualización Enriquecida y Galerías', 'description': 'Sistema de visualización de alta calidad con zoom interactivo y carga optimizada para que las imágenes de los inmuebles luzcan impecables sin afectar la velocidad del sitio. 📸✨'},
                        {'icon': '�', 'name': 'Notificaciones Automáticas', 'description': 'El sistema enviará correos de confirmación automáticos cuando un usuario se registre o envíe una solicitud de información, manteniendo el contacto activo desde el primer segundo. 📩✅'},
                    ],
                },
                {
                    'id': 'integrations_api',
                    'icon': '🔌',
                    'title': 'Integraciones (API)',
                    'description': (
                        '💳 Integración con una Pasarela de Pago para facilitar las transacciones de los usuarios. '
                        'Se proponen las siguientes opciones por su facilidad de integración, presencia en el mercado colombiano '
                        'y/o reconocimiento internacional.'
                    ),
                    'items': [
                        {'icon': '🌎', 'name': 'Internacionales', 'description': 'Stripe: Ideal para recibir pagos con tarjeta de crédito/débito, muy usada a nivel mundial. PayPal: Plataforma reconocida globalmente, permite pagos con saldo PayPal, tarjeta y cuentas internacionales.'},
                        {'icon': '🇨🇴', 'name': 'Regionales (Colombia)', 'description': 'PayU: Una de las más usadas en Colombia, permite pagos con tarjeta, PSE, Efecty, Baloto, Nequi, Daviplata. Wompi (Bancolombia): Excelente opción local con soporte para PSE, tarjetas, Nequi y botón Bancolombia. ePayco: Alternativa colombiana fácil de integrar, soporta múltiples métodos de pago como PSE, tarjetas y recaudos físicos.'},
                    ],
                },
                {
                    'id': 'admin_module',
                    'icon': '🛠️',
                    'title': 'Módulo Administrativo',
                    'description': (
                        'El módulo administrativo permite gestionar el contenido y la operación del sitio '
                        'sin depender de desarrollo técnico.'
                    ),
                    'items': [
                        {'icon': '📂', 'name': 'Gestor de Productos', 'description': 'Crear, editar y eliminar productos o contenidos principales.'},
                        {'icon': '🗂️', 'name': 'Gestor de Categorías', 'description': 'Organización del catálogo por categorías o colecciones.'},
                        {'icon': '👥', 'name': 'Gestor de Usuarios', 'description': 'Administración de cuentas de usuario.'},
                        {'icon': '📝', 'name': 'Gestor de Blogs', 'description': 'Publicación y gestión de artículos o contenido editorial.'},
                        {'icon': '❤️', 'name': 'Gestor de Favoritos', 'description': 'Gestión de listas de deseos o favoritos de usuarios.'},
                    ],
                },
            ],
            'additionalModules': [],
        },
    },
    {
        'section_type': 'timeline',
        'title': '⏳ Cronograma del Proyecto',
        'order': 8,
        'is_wide_panel': True,
        'content_json': {
            'index': '8',
            'title': 'Cronograma del Proyecto',
            'introText': 'El proyecto se desarrollará en las siguientes fases:',
            'totalDuration': 'Aproximadamente 1 mes',
            'phases': [
                {
                    'title': '🎨 Diseño',
                    'duration': '1 semana',
                    'weeks': 'Semana 1',
                    'circleColor': 'bg-purple-600',
                    'statusColor': 'bg-purple-100 text-purple-700',
                    'description': 'Diseño visual personalizado en Figma, revisiones y ajustes.',
                    'tasks': ['Moodboard y paleta de colores', 'Diseño UI en alta fidelidad', 'Revisiones con el cliente'],
                    'milestone': 'Diseño aprobado',
                },
                {
                    'title': '💻 Desarrollo',
                    'duration': '2 semanas',
                    'weeks': 'Semanas 2-3',
                    'circleColor': 'bg-green-600',
                    'statusColor': 'bg-green-100 text-green-700',
                    'description': 'Codificación nativa, integración de pasarelas y correos.',
                    'tasks': ['Frontend responsivo', 'Backend y base de datos', 'Integraciones'],
                    'milestone': 'MVP funcional',
                },
                {
                    'title': '🚀 QA & Launch',
                    'duration': '3 días',
                    'weeks': 'Semana 4',
                    'circleColor': 'bg-orange-600',
                    'statusColor': 'bg-orange-100 text-orange-700',
                    'description': 'Pruebas finales, ajustes y publicación.',
                    'tasks': ['Testing cross-browser', 'Ajustes finales', 'Deploy a producción'],
                    'milestone': 'Sitio en producción',
                },
                {
                    'title': '📦 Entrega y despliegue',
                    'duration': '3 días',
                    'weeks': 'Semana 4',
                    'circleColor': 'bg-pink-600',
                    'statusColor': 'bg-pink-100 text-pink-700',
                    'description': 'Configuración del dominio, entrega de documentación y cierre.',
                    'tasks': ['Configuración de dominio y SSL', 'Entrega de documentación', 'Capacitación al cliente'],
                    'milestone': 'Entrega final 💫',
                },
            ],
        },
    },
    {
        'section_type': 'investment',
        'title': '💰 Inversión y Formas de Pago',
        'order': 9,
        'is_wide_panel': False,
        'content_json': {
            'index': '9',
            'title': 'Inversión y Formas de Pago',
            'introText': 'La inversión total para este proyecto es:',
            'totalInvestment': '',
            'currency': 'COP',
            'whatsIncluded': [
                {'icon': '🎨', 'title': 'Diseño', 'description': 'UX/UI enfocado en conversión'},
                {'icon': '⚙️', 'title': 'Desarrollo', 'description': 'Implementación completa del proyecto'},
                {'icon': '☁️', 'title': 'Hosting', 'description': 'Plan Cloud 1 disponible'},
            ],
            'paymentOptions': [
                {'label': '40% al firmar el contrato ✍️', 'description': ''},
                {'label': '30% al aprobar el diseño final ✅', 'description': ''},
                {'label': '30% al desplegar el sitio web 🚀', 'description': ''},
            ],
            'hostingPlan': {
                'title': 'Hosting Incluido – Cloud 1',
                'description': 'Infraestructura optimizada para proyectos de alto rendimiento y disponibilidad:',
                'specs': [
                    {'icon': '🧠', 'label': 'vCPU', 'value': '1 núcleo de vCPU'},
                    {'icon': '🧮', 'label': 'RAM', 'value': '1 GB de RAM dedicada'},
                    {'icon': '💾', 'label': 'Almacenamiento', 'value': '2 GB de almacenamiento NVMe'},
                    {'icon': '🌐', 'label': 'Ancho de banda', 'value': '600 GB mensual'},
                    {'icon': '📍', 'label': 'Centros de datos', 'value': 'EE.UU., Brasil, Francia, Lituania e India'},
                    {'icon': '🧬', 'label': 'Compatibilidad', 'value': 'Linux (Ubuntu)'},
                ],
                'monthlyPrice': '$49.999 COP',
                'monthlyLabel': 'por mes',
                'annualPrice': '$599.988 COP',
                'annualLabel': 'pago anual único',
            },
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
        'title': '📝 Nota Final',
        'order': 10,
        'is_wide_panel': False,
        'content_json': {
            'index': '10',
            'title': 'Nota Final',
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
    {
        'section_type': 'next_steps',
        'title': '✅ Cierre y próximos pasos',
        'order': 11,
        'is_wide_panel': False,
        'content_json': {
            'index': '11',
            'title': 'Cierre y próximos pasos',
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

DEFAULT_SECTIONS_EN = [
    {
        'section_type': 'greeting',
        'title': '👋 Greeting',
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
        'title': '🧾 Executive Summary',
        'order': 1,
        'is_wide_panel': False,
        'content_json': {
            'index': '1',
            'title': 'Executive Summary',
            'paragraphs': [
                'Our proposal covers the design and development of a professional website.',
            ],
            'highlightsTitle': 'Includes',
            'highlights': [
                'Custom visual design',
                'Responsive web development',
                'Basic SEO optimization',
            ],
        },
    },
    {
        'section_type': 'context_diagnostic',
        'title': '🧩 Context & Diagnostic',
        'order': 2,
        'is_wide_panel': False,
        'content_json': {
            'index': '2',
            'title': 'Context & Diagnostic',
            'paragraphs': [
                'The client seeks to strengthen their digital presence with a website that reflects their professional identity.',
            ],
            'issuesTitle': 'Identified Challenges',
            'issues': [
                'Lack of professional digital presence',
                'Difficulty capturing clients online',
            ],
            'opportunityTitle': 'Opportunity',
            'opportunity': (
                'Create a digital platform that builds trust and converts visitors into clients.'
            ),
        },
    },
    {
        'section_type': 'conversion_strategy',
        'title': '🚀 Proposed Approach & Conversion Strategy',
        'order': 3,
        'is_wide_panel': False,
        'content_json': {
            'index': '3',
            'title': 'Proposed Approach & Conversion Strategy',
            'intro': (
                'The page will be built as a tool to generate trust '
                'and convert visits into conversations.'
            ),
            'steps': [
                {
                    'title': '👀 Capture attention in the first seconds',
                    'bullets': [
                        'Clear main message: what the client does and who they help',
                        'Professional hero section with call to action',
                    ],
                },
                {
                    'title': '🤝 Build trust and credibility',
                    'bullets': [
                        'Testimonials and success stories',
                        'Credentials and experience',
                    ],
                },
                {
                    'title': '📲 Facilitate immediate contact',
                    'bullets': [
                        'WhatsApp and contact form always visible',
                        'Clear and direct calls to action',
                    ],
                },
            ],
            'resultTitle': '🎯 Expected Result',
            'result': (
                'A page that not only "looks nice" but generates contacts, '
                'conveys professionalism and makes it easy for people to say: "Let me reach out".'
            ),
        },
    },
    {
        'section_type': 'design_ux',
        'title': '🎨 Visual Design & User Experience',
        'order': 4,
        'is_wide_panel': False,
        'content_json': {
            'index': '4',
            'title': 'Visual Design & User Experience',
            'paragraphs': [
                'The web development will be conceived as a professional digital experience.',
                'Each section will be carefully created to generate a fluid journey.',
            ],
            'focusTitle': 'Structure Highlights',
            'focusItems': [
                'Clear service presentation',
                'Social media integration',
                'Space for booking appointments or consultations',
            ],
            'objectiveTitle': 'Visual Objective',
            'objective': (
                'Inspire trust from the first moment, reflecting authenticity '
                'and depth of message.'
            ),
        },
    },
    {
        'section_type': 'creative_support',
        'title': '🤝 Personalized Creative Support',
        'order': 5,
        'is_wide_panel': False,
        'content_json': {
            'index': '5',
            'title': 'Personalized Creative Support',
            'paragraphs': [
                'Throughout the process, the client will have close support from our team.',
                'The process will be collaborative, warm, and empathetic.',
            ],
            'includesTitle': 'Includes',
            'includes': [
                '💡 Design and structure review and feedback sessions.',
                '🎨 Support in selecting color palette, typography, and visual style.',
                '🕊 Adaptations as ideas evolve.',
                '🔗 Ensuring coherence between aesthetics, content, and purpose.',
            ],
            'closing': (
                'Every decision will be a co-creation, where the client can actively participate '
                'so the final result faithfully reflects their message.'
            ),
        },
    },
    {
        'section_type': 'development_stages',
        'title': '📌 Contracting & Development Stages',
        'order': 6,
        'is_wide_panel': True,
        'content_json': {
            'stages': [
                {
                    'icon': '✉️',
                    'title': 'Commercial Proposal',
                    'description': 'Formal presentation of the technical and economic proposal (current stage).',
                    'current': True,
                },
                {
                    'icon': '✍️',
                    'title': 'Contract Signing',
                    'description': 'Agreement on scope, timeline, and conditions.',
                },
                {
                    'icon': '🎨',
                    'title': 'Design & Creative Review',
                    'description': 'Custom visual design in Figma with reviews and adjustments.',
                },
                {
                    'icon': '💻',
                    'title': 'Native Development',
                    'description': 'Custom coding, payment gateway and email integration.',
                },
                {
                    'icon': '🚀',
                    'title': 'Launch & Deployment',
                    'description': 'QA, production deployment, and domain setup.',
                },
                {
                    'icon': '💖',
                    'title': 'Final Delivery',
                    'description': 'Site online and validated, closing the digital transformation cycle.',
                },
            ],
        },
    },
    {
        'section_type': 'functional_requirements',
        'title': '🧩 Functional Requirements',
        'order': 7,
        'is_wide_panel': True,
        'content_json': {
            'index': '7',
            'title': 'Functional Requirements',
            'intro': 'Below are the functional requirements for the project.',
            'groups': [
                {
                    'id': 'views',
                    'icon': '🖥️',
                    'title': 'Views',
                    'description': (
                        'Each view is a screen or section of the website. Its purpose is to guide the visitor '
                        'to understand the value proposition and facilitate contact or the desired action.'
                    ),
                    'items': [
                        {'icon': '🏠', 'name': 'Home (Landing Page)', 'description': 'The first impression of the site. Clearly presents the brand identity with an attractive message, call to action, and quick access to main sections.'},
                        {'icon': 'ℹ️', 'name': 'About Us', 'description': 'Page dedicated to sharing the history, mission, vision, and values of the company or project. Ideal for building trust with visitors.'},
                        {'icon': '📞', 'name': 'Contact', 'description': 'Section with a form for users to send messages, along with contact information (phone, email, address) and an optional map.'},
                        {'icon': '📜', 'name': 'Terms & Conditions', 'description': 'Page informing users about site policies, personal data handling, and terms of use. Includes an acceptance checkbox ensuring compliance with regulations.'},
                        {'icon': '🛒', 'name': 'Categories', 'description': 'Section to display available product categories, allowing users to explore the different types of products offered on the site.'},
                        {'icon': '�️', 'name': 'Catalog by Category', 'description': 'Allows users to explore products within a specific category, facilitating navigation and selection of related products.'},
                        {'icon': '📦', 'name': 'Product View', 'description': 'Shows details of a selected product, including images, price, features, descriptions, and options to add to cart.'},
                        {'icon': '🛒', 'name': 'Shopping Cart', 'description': 'Allows users to view added products, adjust quantities, remove items, and proceed to checkout.'},
                        {'icon': '📜', 'name': 'Purchase History', 'description': 'Allows users to review past purchases, including details such as date, amount, and products acquired.'},
                        {'icon': '👤', 'name': 'User Registration', 'description': 'Allows users to create an account to access personalized features like purchase history and favorite products.'},
                        {'icon': '�', 'name': 'Login', 'description': 'Provides access for registered users to manage their purchases and preferences.'},
                        {'icon': '❤️', 'name': 'Wishlist / Favorites', 'description': 'Allows users to save products for quick reference in future visits.'},
                        {'icon': '📝', 'name': 'User Profile', 'description': 'Section where users can view and update their personal information, purchase history, and account settings.'},
                    ],
                },
                {
                    'id': 'components',
                    'icon': '🧩',
                    'title': 'Components',
                    'description': (
                        'Components are visual or functional elements reused across multiple sections '
                        'of the site. This ensures a coherent experience and optimizes development.'
                    ),
                    'items': [
                        {'icon': '🔝', 'name': 'Header', 'description': 'Includes logo, navigation menu, and quick access to social media or key site sections.'},
                        {'icon': '🔚', 'name': 'Footer', 'description': 'Contains additional information such as copyright, policies, social media links, and other useful resources.'},
                        {'icon': '🎯', 'name': 'Featured Products Carousel', 'description': 'Highlights selected products such as promotions, special offers, or seasonal products to improve visibility and customer interest.'},
                        {'icon': '🎁', 'name': 'Featured Wishlists Carousel', 'description': 'Highlights selected wishlists such as promotions, special offers, or seasonal products to improve visibility and customer interest.'},
                        {'icon': '❓', 'name': 'FAQ (Frequently Asked Questions)', 'description': 'Section to answer the most common customer questions and resolve doubts quickly and efficiently.'},
                    ],
                },
                {
                    'id': 'features',
                    'icon': '⚙️',
                    'title': 'Specific Features',
                    'description': (
                        'Features are interactive actions or behaviors of the website. '
                        'They bring life and dynamism, making the page practical and useful.'
                    ),
                    'items': [
                        {'icon': '🌐', 'name': 'Responsive Design', 'description': 'The site adapts perfectly to phones, tablets, and computers. This is vital as most initial searches occur from mobile devices. 📱💻'},
                        {'icon': '�', 'name': 'Google Sign-In & Registration', 'description': 'Simplified access allowing users to register with a single click. Key for capturing real customer data and understanding their preferences. 🔐📧'},
                        {'icon': '🔎', 'name': 'Advanced Search with Dynamic Filters', 'description': 'Users can filter properties by zones, price range, square meters, and specific features. Intuitive navigation saves time and better qualifies interest. 🔍📍'},
                        {'icon': '💬', 'name': 'Direct WhatsApp per Property', 'description': 'Each property listing includes an instant contact button. One click sends a predefined message indicating exactly which property the client is inquiring about. 📲⚡'},
                        {'icon': '�️', 'name': 'Rich Visualization & Galleries', 'description': 'High-quality visualization system with interactive zoom and optimized loading so property images look impeccable without affecting site speed. 📸✨'},
                        {'icon': '📩', 'name': 'Automatic Notifications', 'description': 'The system sends automatic confirmation emails when a user registers or submits an information request, keeping contact active from the first second. 📩✅'},
                    ],
                },
                {
                    'id': 'integrations_api',
                    'icon': '🔌',
                    'title': 'Integrations (API)',
                    'description': (
                        '💳 Payment Gateway Integration to facilitate user transactions. '
                        'The following options are proposed for their ease of integration, market presence, '
                        'and/or international recognition.'
                    ),
                    'items': [
                        {'icon': '🌎', 'name': 'International', 'description': 'Stripe: Ideal for credit/debit card payments, widely used worldwide. PayPal: Globally recognized platform, allows payments with PayPal balance, cards, and international accounts.'},
                        {'icon': '🇨🇴', 'name': 'Regional (Colombia)', 'description': 'PayU: One of the most used in Colombia, supports card, PSE, Efecty, Baloto, Nequi, Daviplata. Wompi (Bancolombia): Excellent local option with PSE, cards, Nequi, and Bancolombia button support. ePayco: Easy-to-integrate Colombian alternative supporting PSE, cards, and physical collections.'},
                    ],
                },
                {
                    'id': 'admin_module',
                    'icon': '🛠️',
                    'title': 'Admin Module',
                    'description': (
                        'The admin module allows managing the site content and operations '
                        'without depending on technical development.'
                    ),
                    'items': [
                        {'icon': '📂', 'name': 'Product Manager', 'description': 'Create, edit, and delete main products or content.'},
                        {'icon': '🗂️', 'name': 'Category Manager', 'description': 'Catalog organization by categories or collections.'},
                        {'icon': '👥', 'name': 'User Manager', 'description': 'User account administration.'},
                        {'icon': '📝', 'name': 'Blog Manager', 'description': 'Article and editorial content publishing.'},
                        {'icon': '❤️', 'name': 'Favorites Manager', 'description': 'User wishlists and favorites management.'},
                    ],
                },
            ],
            'additionalModules': [],
        },
    },
    {
        'section_type': 'timeline',
        'title': '⏳ Project Timeline',
        'order': 8,
        'is_wide_panel': True,
        'content_json': {
            'index': '8',
            'title': 'Project Timeline',
            'introText': 'The project will be developed in the following phases:',
            'totalDuration': 'Approximately 1 month',
            'phases': [
                {
                    'title': '🎨 Design',
                    'duration': '1 week',
                    'weeks': 'Week 1',
                    'circleColor': 'bg-purple-600',
                    'statusColor': 'bg-purple-100 text-purple-700',
                    'description': 'Custom visual design in Figma, reviews and adjustments.',
                    'tasks': ['Moodboard and color palette', 'High-fidelity UI design', 'Client reviews'],
                    'milestone': 'Design approved',
                },
                {
                    'title': '💻 Development',
                    'duration': '2 weeks',
                    'weeks': 'Weeks 2-3',
                    'circleColor': 'bg-green-600',
                    'statusColor': 'bg-green-100 text-green-700',
                    'description': 'Native coding, payment gateway and email integration.',
                    'tasks': ['Responsive frontend', 'Backend and database', 'Integrations'],
                    'milestone': 'Functional MVP',
                },
                {
                    'title': '🚀 QA & Launch',
                    'duration': '3 days',
                    'weeks': 'Week 4',
                    'circleColor': 'bg-orange-600',
                    'statusColor': 'bg-orange-100 text-orange-700',
                    'description': 'Final testing, adjustments, and publication.',
                    'tasks': ['Cross-browser testing', 'Final adjustments', 'Production deploy'],
                    'milestone': 'Site in production',
                },
                {
                    'title': '📦 Delivery & Deployment',
                    'duration': '3 days',
                    'weeks': 'Week 4',
                    'circleColor': 'bg-pink-600',
                    'statusColor': 'bg-pink-100 text-pink-700',
                    'description': 'Domain setup, documentation delivery, and closure.',
                    'tasks': ['Domain and SSL setup', 'Documentation delivery', 'Client training'],
                    'milestone': 'Final delivery 💫',
                },
            ],
        },
    },
    {
        'section_type': 'investment',
        'title': '💰 Investment & Payment Options',
        'order': 9,
        'is_wide_panel': False,
        'content_json': {
            'index': '9',
            'title': 'Investment & Payment Options',
            'introText': 'The total investment for this project is:',
            'totalInvestment': '',
            'currency': 'USD',
            'whatsIncluded': [
                {'icon': '🎨', 'title': 'Design', 'description': 'UX/UI focused on conversion'},
                {'icon': '⚙️', 'title': 'Development', 'description': 'Full project implementation'},
                {'icon': '☁️', 'title': 'Hosting', 'description': 'Cloud 1 plan available'},
            ],
            'paymentOptions': [
                {'label': '40% upon signing the contract ✍️', 'description': ''},
                {'label': '30% upon final design approval ✅', 'description': ''},
                {'label': '30% upon site deployment 🚀', 'description': ''},
            ],
            'hostingPlan': {
                'title': 'Included Hosting – Cloud 1',
                'description': 'Optimized infrastructure for high-performance and availability:',
                'specs': [
                    {'icon': '🧠', 'label': 'vCPU', 'value': '1 vCPU core'},
                    {'icon': '🧮', 'label': 'RAM', 'value': '1 GB dedicated RAM'},
                    {'icon': '💾', 'label': 'Storage', 'value': '2 GB NVMe storage'},
                    {'icon': '🌐', 'label': 'Bandwidth', 'value': '600 GB monthly'},
                    {'icon': '📍', 'label': 'Data centers', 'value': 'US, Brazil, France, Lithuania & India'},
                    {'icon': '🧬', 'label': 'Compatibility', 'value': 'Linux (Ubuntu)'},
                ],
                'monthlyPrice': '$4.99 USD',
                'monthlyLabel': 'per month',
                'annualPrice': '$59.88 USD',
                'annualLabel': 'annual payment',
            },
            'paymentMethods': [
                'Bank transfer',
                'Credit/Debit card',
            ],
            'valueReasons': [
                'Custom-made design',
                'Optimized code',
                'Post-launch support',
            ],
        },
    },
    {
        'section_type': 'final_note',
        'title': '📝 Final Note',
        'order': 10,
        'is_wide_panel': False,
        'content_json': {
            'index': '10',
            'title': 'Final Note',
            'message': (
                'We firmly believe this proposal represents an exceptional opportunity '
                'to transform your digital presence and achieve your business goals.'
            ),
            'personalNote': (
                'We are excited about the possibility of working with you and helping you '
                'take your business to the next level.'
            ),
            'teamName': 'The Project App Team',
            'teamRole': 'Your partner in digital transformation',
            'contactEmail': 'hello@projectapp.com',
            'commitmentBadges': [
                {
                    'icon': '🤝',
                    'title': 'Total Commitment',
                    'description': 'Complete dedication to your project until exceptional results',
                },
                {
                    'icon': '💯',
                    'title': 'Quality Guarantee',
                    'description': 'Unlimited revisions until your complete satisfaction',
                },
                {
                    'icon': '🎯',
                    'title': 'Results-Focused',
                    'description': 'We measure our success by the impact on your business',
                },
            ],
            'validityMessage': (
                'This proposal is valid for 30 days from the date of issue. '
                'Prices and conditions may be subject to changes after this period.'
            ),
            'thankYouMessage': (
                'We sincerely appreciate the opportunity to present this proposal. '
                'We look forward to the possibility of working with you.'
            ),
        },
    },
    {
        'section_type': 'next_steps',
        'title': '✅ Closing & Next Steps',
        'order': 11,
        'is_wide_panel': False,
        'content_json': {
            'index': '11',
            'title': 'Closing & Next Steps',
            'introMessage': (
                'We are ready to start this journey together. '
                'Here is how to take the next step:'
            ),
            'steps': [
                {
                    'title': 'Review & Questions',
                    'description': 'Review the proposal and send us any questions or adjustments you need.',
                },
                {
                    'title': 'Confirmation Meeting',
                    'description': 'We schedule a call to align final details and sign the contract.',
                },
                {
                    'title': "Let's Begin!",
                    'description': 'We start the project with the kickoff meeting and begin the Discovery phase.',
                },
            ],
            'ctaMessage': (
                'Contact us today and let us start working on your project. '
                'We are just a message away.'
            ),
            'primaryCTA': {
                'text': 'Contact via WhatsApp',
                'link': 'https://wa.me/1234567890',
            },
            'secondaryCTA': {
                'text': 'Schedule Meeting',
                'link': 'https://calendly.com/projectapp',
            },
            'contactMethods': [
                {
                    'icon': '📧',
                    'title': 'Email',
                    'value': 'hello@projectapp.com',
                    'link': 'mailto:hello@projectapp.com',
                },
                {
                    'icon': '📱',
                    'title': 'WhatsApp',
                    'value': '+57 123 456 7890',
                    'link': 'https://wa.me/571234567890',
                },
                {
                    'icon': '🌐',
                    'title': 'Website',
                    'value': 'www.projectapp.co',
                    'link': 'https://projectapp.co',
                },
            ],
            'validityMessage': (
                'This proposal is valid for 30 days from the date of issue. '
                'Prices and conditions may be subject to change after this period.'
            ),
            'thankYouMessage': (
                'We sincerely appreciate the opportunity to present this proposal. '
                'We look forward to the possibility of working with you.'
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
    def get_default_sections(language='es'):
        """
        Return the default section configurations for a new proposal.

        Args:
            language: 'es' for Spanish (default), 'en' for English.

        Returns:
            list[dict]: List of section configs with section_type, title, order,
                        is_wide_panel, and content_json.
        """
        import copy
        source = DEFAULT_SECTIONS_EN if language == 'en' else DEFAULT_SECTIONS
        return copy.deepcopy(source)
