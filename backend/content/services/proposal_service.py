import logging
from copy import deepcopy
from datetime import timedelta

from django.utils import timezone

from content.technical_document_defaults import EMPTY_TECHNICAL_DOCUMENT_JSON

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default section configurations extracted from existing Vue component props.
# Each entry maps to the content_json stored in ProposalSection.
# ---------------------------------------------------------------------------

DEFAULT_SECTIONS = [
    {
        'section_type': 'greeting',
        'title': '👋 Saludo',
        'order': 0,
        'is_wide_panel': False,
        'content_json': {
            'proposalTitle': '',
            'clientName': '',
            'inspirationalQuote': (
                'Design is not just what it looks like and feels like. '
                'Design is how it works.'
            ),
        },
    },
    {
        'section_type': 'executive_summary',
        'title': '🧾 Lo que vas a lograr',
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
        'title': '🧩 Tu situación actual y la oportunidad',
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
        'title': '🚀 Cómo vamos a lograrlo',
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
        'section_type': 'investment',
        'title': '💰 Tu inversión y cómo pagar',
        'order': 4,
        'is_wide_panel': False,
        'content_json': {
            'index': '4',
            'title': 'Inversión y Formas de Pago',
            'introText': 'La inversión total para este proyecto es:',
            'totalInvestment': '',
            'currency': 'COP',
            'whatsIncluded': [
                {'icon': '🎨', 'title': 'Diseño', 'description': 'UX/UI enfocado en conversión'},
                {'icon': '⚙️', 'title': 'Desarrollo', 'description': 'Implementación completa del proyecto'},
                {'icon': '🚀', 'title': 'Despliegue y Entrega', 'description': 'Despliegue en producción y puesta en marcha'},
            ],
            'paymentOptions': [
                {'label': '40% al firmar el contrato ✍️', 'description': ''},
                {'label': '30% al aprobar el diseño final ✅', 'description': ''},
                {'label': '30% al desplegar el sitio web 🚀', 'description': ''},
            ],
            'hostingPlan': {
                'title': 'Hosting, Mantenimiento y Soporte',
                'description': 'Infraestructura optimizada para proyectos de alto rendimiento y disponibilidad:',
                'specs': [
                    {'icon': '🧠', 'label': 'vCPU', 'value': '4 núcleos de vCPU'},
                    {'icon': '🧮', 'label': 'RAM', 'value': '8 GB de RAM dedicada'},
                    {'icon': '💾', 'label': 'Almacenamiento', 'value': '100 GB de almacenamiento NVMe'},
                    {'icon': '🌐', 'label': 'Ancho de banda', 'value': '4 TB mensual'},
                    {'icon': '📍', 'label': 'Centros de datos', 'value': 'EE.UU., Brasil, Francia, Lituania e India'},
                    {'icon': '🧬', 'label': 'Compatibilidad', 'value': 'Linux (Ubuntu)'},
                ],
                'hostingPercent': 30,
                'billingTiers': [
                    {
                        'frequency': 'semiannual',
                        'months': 6,
                        'discountPercent': 20,
                        'label': 'Semestral',
                        'badge': 'Mejor precio',
                    },
                    {
                        'frequency': 'quarterly',
                        'months': 3,
                        'discountPercent': 10,
                        'label': 'Trimestral',
                        'badge': '10% dcto',
                    },
                    {
                        'frequency': 'monthly',
                        'months': 1,
                        'discountPercent': 0,
                        'label': 'Mensual',
                        'badge': '',
                    },
                ],
                'renewalNote': (
                    'Renovaciones a partir del segundo año: el costo se ajusta anualmente '
                    'con base en el SMLMV (Salario Mínimo Legal Mensual Vigente) del año '
                    'de renovación, aplicando la siguiente fórmula:\n\n'
                    'Costo de renovación = Costo del año anterior + '
                    '(6% × SMLMV del año de renovación)\n\n'
                    'Por ejemplo, si el SMLMV del año de renovación fuera $1.300.000 COP, '
                    'el incremento sería de $78.000 COP, llevando el costo a $758.000 COP '
                    'para ese año.'
                ),
                'coverageNote': (
                    'El costo de hosting cubre tres componentes: el mantenimiento técnico '
                    'de la plataforma (actualizaciones de seguridad, parches y optimización '
                    'de base de datos), el soporte ante incidencias o bugs, y los recursos '
                    'computacionales necesarios para que todo funcione (servidor, '
                    'almacenamiento, ancho de banda y certificados SSL).'
                ),
            },
            'paymentMethods': [
                'Transferencia bancaria',
                'Nequi / Daviplata',
            ],
            'modules': [],
            'valueReasons': [
                'Diseño hecho a medida',
                'Código optimizado',
                'Soporte post-lanzamiento',
            ],
        },
    },
    {
        'section_type': 'timeline',
        'title': '⏳ Cuándo lo tendrás listo',
        'order': 6,
        'is_wide_panel': True,
        'content_json': {
            'index': '6',
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
                    'title': '🚀 QA y Lanzamiento',
                    'duration': '3 días',
                    'weeks': 'Semana 4',
                    'circleColor': 'bg-orange-600',
                    'statusColor': 'bg-orange-100 text-orange-700',
                    'description': 'Pruebas finales, ajustes y publicación.',
                    'tasks': ['Pruebas en múltiples navegadores', 'Ajustes finales', 'Despliegue a producción'],
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
        'section_type': 'design_ux',
        'title': '🎨 Una experiencia visual que enamora',
        'order': 7,
        'is_wide_panel': False,
        'content_json': {
            'index': '7',
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
        'title': '🤝 Te acompañamos en cada paso',
        'order': 8,
        'is_wide_panel': False,
        'content_json': {
            'index': '8',
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
        'section_type': 'value_added_modules',
        'title': '🎁 Incluido sin costo adicional',
        'order': 10,
        'is_wide_panel': False,
        'content_json': {
            'index': '10',
            'title': 'Lo que sumamos a tu proyecto sin costo extra',
            'intro': (
                'Estos módulos no se cobran aparte. Se incluyen porque creemos que todo '
                'entregable debería venir con las herramientas mínimas para operarlo, '
                'medirlo y entenderlo desde el día uno.'
            ),
            'module_ids': ['admin_module', 'analytics_dashboard', 'kpi_dashboard_module', 'manual_module'],
            'justifications': {
                'admin_module': 'Para que no dependas de un desarrollador cada vez que necesites cambiar contenido.',
                'analytics_dashboard': 'Para que sepas cómo se comporta tu audiencia sin contratar herramientas externas.',
                'kpi_dashboard_module': 'Para tomar decisiones con datos en tiempo real, no con intuición.',
                'manual_module': 'Para que cualquier persona del equipo entienda el sistema sin sesiones de capacitación.',
            },
            'footer_note': 'Total adicional: $0. Ya está cotizado dentro del precio del proyecto.',
        },
    },
    {
        'section_type': 'functional_requirements',
        'title': '🧩 Todo lo que incluye tu proyecto',
        'order': 9,
        'is_wide_panel': True,
        'content_json': {
            'index': '9',
            'title': 'Requerimientos Funcionales del Proyecto',
            'intro': 'A continuación se detallan los requerimientos funcionales del proyecto.',
            'groups': [
                {
                    'id': 'views',
                    'icon': '🖥️',
                    'title': 'Vistas',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
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
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
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
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
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
                    'id': 'admin_module',
                    'icon': '🛠️',
                    'title': 'Módulo Administrativo',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
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
                {
                    'id': 'analytics_dashboard',
                    'icon': '📊',
                    'title': 'Módulo de Analítica',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
                    'description': (
                        'Dashboard de reportes inteligentes y métricas en tiempo real para entender '
                        'el comportamiento de los visitantes y tomar decisiones basadas en datos.'
                    ),
                    'items': [
                        {
                            'icon': '🔥',
                            'name': 'Páginas y Productos Más Visitados',
                            'description': (
                                'Identifica qué secciones y productos generan más interés. '
                                'Permite priorizar contenido, reorganizar el catálogo y potenciar '
                                'lo que realmente atrae a tus visitantes.'
                            ),
                        },
                        {
                            'icon': '🔄',
                            'name': 'Visitantes Nuevos vs Recurrentes',
                            'description': (
                                'Diferencia entre quienes llegan por primera vez y quienes regresan. '
                                'Te ayuda a medir la fidelización y evaluar si tus estrategias de '
                                'retención están funcionando.'
                            ),
                        },
                        {
                            'icon': '📱',
                            'name': 'Dispositivos de tu Audiencia',
                            'description': (
                                'Conoce desde qué dispositivos navegan tus usuarios: móvil, tablet o escritorio. '
                                'Esto permite optimizar la experiencia para el dispositivo más usado por tu público.'
                            ),
                        },
                        {
                            'icon': '🌍',
                            'name': 'Origen Geográfico',
                            'description': (
                                'Visualiza de qué ciudades o países provienen tus visitantes. '
                                'Ideal para enfocar campañas publicitarias y entender dónde está '
                                'tu mercado real.'
                            ),
                        },
                        {
                            'icon': '🔗',
                            'name': 'Fuentes de Tráfico',
                            'description': (
                                'Descubre cómo llegan los usuarios a tu sitio: búsqueda orgánica, '
                                'redes sociales, enlaces directos o campañas pagadas. Permite invertir '
                                'mejor tu presupuesto de marketing.'
                            ),
                        },
                        {
                            'icon': '📈',
                            'name': 'Tendencia de Visitas',
                            'description': (
                                'Gráfico de evolución de visitas en el tiempo. Permite detectar picos, '
                                'medir el impacto de campañas y entender patrones estacionales de tu audiencia.'
                            ),
                        },
                    ],
                },
                {
                    'id': 'kpi_dashboard_module',
                    'icon': '📊',
                    'title': 'Dashboard de KPIs y Métricas',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
                    'description': (
                        'Panel de control complementario al módulo de analítica, con indicadores '
                        'clave de rendimiento en tiempo real para monitorear la salud de tu '
                        'negocio y tomar decisiones basadas en datos.'
                    ),
                    'items': [
                        {'icon': '📈', 'name': 'KPIs en tiempo real', 'description': 'Visualiza los indicadores más importantes de tu negocio actualizados al instante: ventas, conversiones, tráfico y más.'},
                        {'icon': '📊', 'name': 'Gráficos interactivos', 'description': 'Dashboards visuales con gráficos de línea, barras y torta que permiten filtrar por período, categoría o segmento.'},
                        {'icon': '🔔', 'name': 'Alertas de rendimiento', 'description': 'Notificaciones automáticas cuando un KPI cae por debajo del umbral definido o supera una meta establecida.'},
                        {'icon': '📥', 'name': 'Exportación de reportes', 'description': 'Descarga reportes en CSV para compartir con tu equipo o stakeholders sin necesidad de acceder al sistema.'},
                    ],
                },
                {
                    'id': 'manual_module',
                    'icon': '📘',
                    'title': 'Manual de Usuario Interactivo',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
                    'description': (
                        'Manual/wiki interactivo no técnico, con índice navegable y buscador, '
                        'que describe los procesos, flujos, dependencias, roles y responsabilidades '
                        'de tu aplicación. Pensado para que cualquier persona del equipo pueda '
                        'entender el sistema sin pedir ayuda al desarrollador.'
                    ),
                    'items': [
                        {'icon': '🔎', 'name': 'Buscador y navegación por índice', 'description': 'Encuentra cualquier proceso, vista o rol en segundos.'},
                        {'icon': '🧭', 'name': 'Procesos y flujos paso a paso', 'description': 'Cada flujo del sistema documentado en lenguaje claro, sin tecnicismos.'},
                        {'icon': '👥', 'name': 'Roles y responsabilidades', 'description': 'Quién hace qué dentro de la aplicación y qué permisos tiene cada rol.'},
                        {'icon': '🔗', 'name': 'Dependencias y reglas de negocio', 'description': 'Cómo se relacionan los módulos entre sí y qué reglas aplican.'},
                    ],
                },
            ],
            'additionalModules': [
                {
                    'id': 'integration_electronic_invoicing',
                    'icon': '🧾',
                    'title': 'Facturación Electrónica e Integración DIAN (Integración API)',
                    'is_visible': True,
                    'description': (
                        'Conexión de la plataforma con el sistema de facturación del cliente para generar, '
                        'enviar, consultar y reconciliar comprobantes electrónicos desde los flujos operativos '
                        'del negocio. Incluye sincronización de clientes, productos, impuestos, facturas, '
                        'notas crédito/débito y documentos soporte, con trazabilidad del estado fiscal y '
                        'soporte para automatizaciones vía API.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 60,
                    'is_invite': False,
                    'items': [
                        {'icon': '📄', 'name': 'Generación de comprobantes electrónicos', 'description': 'Creación automática de facturas, notas crédito/débito y documentos soporte desde los flujos operativos del negocio.'},
                        {'icon': '🔄', 'name': 'Sincronización de datos fiscales', 'description': 'Sincronización bidireccional de clientes, productos, impuestos y comprobantes con el sistema de facturación.'},
                        {'icon': '📊', 'name': 'Trazabilidad del estado fiscal', 'description': 'Consulta y seguimiento del estado de cada comprobante: emitido, aceptado, rechazado o en proceso ante la DIAN.'},
                        {'icon': '🔗', 'name': 'Integración con proveedores colombianos', 'description': 'Conexión con Siigo, Alegra u otros proveedores con presencia y API documentada en Colombia.'},
                        {'icon': '⚙️', 'name': 'Automatizaciones vía API', 'description': 'Flujos automáticos para reconciliación de pagos, emisión de facturas al completar pedidos y notificaciones de estado fiscal.'},
                    ],
                },
                {
                    'id': 'integration_regional_payments',
                    'icon': '🇨🇴',
                    'title': 'Pasarela de Pago Regional (Colombia) (Integración API)',
                    'is_visible': True,
                    'description': (
                        'Integración con pasarelas de pago con presencia en el mercado colombiano '
                        'para facilitar transacciones locales con múltiples métodos de pago.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'is_invite': False,
                    'items': [
                        {'icon': '💳', 'name': 'PayU', 'description': 'Una de las más usadas en Colombia, permite pagos con tarjeta, PSE, Efecty, Baloto, Nequi, Daviplata.'},
                        {'icon': '🏦', 'name': 'Wompi (Bancolombia)', 'description': 'Excelente opción local con soporte para PSE, tarjetas, Nequi y botón Bancolombia.'},
                        {'icon': '💰', 'name': 'ePayco', 'description': 'Alternativa colombiana fácil de integrar, soporta múltiples métodos de pago como PSE, tarjetas y recaudos físicos.'},
                    ],
                },
                {
                    'id': 'integration_international_payments',
                    'icon': '🌎',
                    'title': 'Pasarela de Pago Internacional (Integración API)',
                    'is_visible': True,
                    'description': (
                        'Integración con pasarelas de pago internacionales para facilitar '
                        'transacciones globales con tarjeta de crédito/débito y cuentas internacionales.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'is_invite': False,
                    'items': [
                        {'icon': '💳', 'name': 'Stripe', 'description': 'Ideal para recibir pagos con tarjeta de crédito/débito, muy usada a nivel mundial. Soporta suscripciones, pagos únicos y múltiples divisas.'},
                        {'icon': '🅿️', 'name': 'PayPal', 'description': 'Plataforma reconocida globalmente, permite pagos con saldo PayPal, tarjeta y cuentas internacionales.'},
                    ],
                },
                {
                    'id': 'pwa_module',
                    'icon': '📱',
                    'title': 'Aplicación Móvil Instalable (PWA)',
                    'is_visible': True,
                    'description': (
                        'Convierte tu sitio web en una aplicación instalable que funciona '
                        'incluso sin conexión a internet. Ofrece una experiencia nativa '
                        'directamente desde el navegador, sin necesidad de tiendas de aplicaciones.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 40,
                    'items': [
                        {'icon': '📲', 'name': 'Instalación en dispositivo', 'description': 'Los usuarios pueden instalar tu sitio como una app en su celular o computador, con acceso directo desde la pantalla de inicio.'},
                        {'icon': '📡', 'name': 'Funcionamiento offline', 'description': 'El sitio sigue siendo accesible sin conexión a internet, mostrando contenido previamente cargado y sincronizando datos al reconectarse.'},
                        {'icon': '🔔', 'name': 'Notificaciones push', 'description': 'Envía notificaciones directas al dispositivo del usuario para mantenerlo informado sobre novedades, promociones o actualizaciones.'},
                        {'icon': '🎨', 'name': 'Pantalla de carga personalizada', 'description': 'Splash screen con la identidad visual de tu marca al abrir la aplicación, generando una experiencia profesional desde el primer instante.'},
                        {'icon': '🔄', 'name': 'Sincronización en segundo plano', 'description': 'Los datos se sincronizan automáticamente cuando el dispositivo recupera la conexión, garantizando información actualizada sin intervención del usuario.'},
                        {'icon': '⬆️', 'name': 'Actualización automática', 'description': 'La aplicación se actualiza de forma transparente sin que el usuario tenga que hacer nada, siempre con la versión más reciente.'},
                    ],
                },
                {
                    'id': 'corporate_branding_module',
                    'icon': '🎨',
                    'title': 'Identidad Visual e Imagen Corporativa',
                    'is_visible': True,
                    'description': (
                        'Aplicamos tu identidad visual de forma consistente en cada punto de contacto del '
                        'sistema — correos, documentos, redes sociales y pantallas internas — para que tu '
                        'marca se perciba profesional y coherente en todo lugar donde tus clientes interactúan.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 35,
                    'items': [
                        {'icon': '✉️', 'name': 'Correos transaccionales con identidad corporativa', 'description': 'Plantillas HTML con logo, colores, tipografía y firma de marca aplicadas en todos los correos del sistema — bienvenida, confirmaciones, alertas, recuperación de contraseña y notificaciones — en lugar de correos en texto plano o genéricos.'},
                        {'icon': '📄', 'name': 'PDFs y exportables con branding', 'description': 'Facturas, reportes, certificados, recibos y descargas Excel/CSV generados desde el sistema con encabezado con logo, paleta corporativa y pie de marca. Cada documento que sale de la plataforma refuerza la imagen profesional del negocio.'},
                        {'icon': '🔗', 'name': 'Tarjetas de previsualización en redes (Open Graph)', 'description': 'Cuando alguien comparte un link del sitio o una propuesta en WhatsApp, Facebook, LinkedIn o X, aparece una tarjeta con logo, imagen y colores de marca — no un link plano. Impacto directo en percepción y CTR.'},
                        {'icon': '🖥️', 'name': 'Pantallas del sistema con identidad de marca', 'description': 'Páginas de error (404, 500), mantenimiento, login y estados de carga (loading, skeletons) con identidad visual y mensajes en la voz de la marca, en vez de las pantallas genéricas del framework.'},
                        {'icon': '🔎', 'name': 'Metadatos estructurados para buscadores e IA', 'description': 'JSON-LD Organization con logo, colores, redes sociales y datos de contacto — para que Google, Bing y asistentes como ChatGPT o Perplexity muestren correctamente la marca en panel de conocimiento, resultados enriquecidos y citaciones.'},
                    ],
                },
                {
                    'id': 'ai_module',
                    'icon': '🤖',
                    'title': 'Integración y Automatización con IA',
                    'is_visible': True,
                    'description': (
                        'Potencia tu proyecto con inteligencia artificial. Exploramos juntos '
                        'cómo adaptar soluciones de IA a las necesidades específicas de tu negocio.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 0,
                    'is_invite': True,
                    'invite_note': (
                        '🤝 Te invitamos a una llamada personalizada donde exploraremos '
                        'juntos cómo la inteligencia artificial puede transformar tu negocio. '
                        'Conocerás nuestras soluciones, cómo las adaptamos a tu caso particular, '
                        'y los costos asociados — sin compromiso.'
                    ),
                    'items': [
                        {'icon': '⚡', 'name': 'Automatizaciones', 'description': 'Flujos de trabajo inteligentes que ejecutan tareas repetitivas de forma autónoma, liberando tiempo para lo que realmente importa.'},
                        {'icon': '📊', 'name': 'Análisis de datos con lenguaje natural', 'description': 'Consulta tus datos usando preguntas en español o inglés y obtén respuestas claras, gráficos y reportes sin necesidad de conocimientos técnicos.'},
                        {'icon': '✍️', 'name': 'Generación de contenido', 'description': 'Creación asistida de textos, descripciones de productos, artículos de blog y comunicaciones, manteniendo el tono y estilo de tu marca.'},
                        {'icon': '💬', 'name': 'Comunicación inteligente', 'description': 'Chatbots y asistentes virtuales que atienden a tus clientes 24/7, responden preguntas frecuentes y escalan conversaciones cuando es necesario.'},
                        {'icon': '📄', 'name': 'Procesamiento de documentos', 'description': 'Extracción y clasificación automática de información desde facturas, contratos y formularios, reduciendo el trabajo manual y los errores.'},
                        {'icon': '🔍', 'name': 'Búsqueda e investigación', 'description': 'Motor de búsqueda semántico que entiende la intención del usuario y devuelve resultados relevantes, no solo coincidencias de texto.'},
                        {'icon': '🛡️', 'name': 'Seguridad y moderación', 'description': 'Detección automática de contenido inapropiado, spam y actividad sospechosa para mantener tu plataforma segura y confiable.'},
                        {'icon': '⚙️', 'name': 'Optimización de procesos', 'description': 'Análisis inteligente de tus operaciones para identificar cuellos de botella, sugerir mejoras y automatizar decisiones rutinarias.'},
                        {'icon': '🎓', 'name': 'Aprendizaje y capacitación', 'description': 'Sistemas adaptativos que personalizan la experiencia de aprendizaje según el ritmo y nivel de cada usuario.'},
                        {'icon': '🔮', 'name': 'Predicción y forecasting', 'description': 'Modelos predictivos que anticipan tendencias, demanda y comportamiento de clientes para tomar decisiones más informadas.'},
                        {'icon': '🔗', 'name': 'Integración y orquestación', 'description': 'Conexión inteligente entre tus herramientas y servicios existentes, coordinando flujos de datos y acciones entre múltiples plataformas.'},
                    ],
                },
                {
                    'id': 'integration_conversion_tracking',
                    'icon': '📡',
                    'title': 'Conversiones Inteligentes (Meta & Google Ads) (Integración API)',
                    'is_visible': True,
                    'description': (
                        'Maximiza el retorno de tu inversión publicitaria con seguimiento '
                        'de conversiones server-side. Tu sitio web reporta cada acción '
                        'valiosa directamente a Meta y Google, sin depender de cookies '
                        'ni del navegador del visitante.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 0,
                    'is_invite': True,
                    'invite_note': (
                        '🤝 Te invitamos a una llamada donde analizaremos tu estrategia '
                        'publicitaria actual y diseñaremos juntos la integración server-side '
                        'con Meta y Google Ads. Verás cómo maximizar tu ROAS con datos '
                        'de conversión precisos — sin compromiso.'
                    ),
                    'items': [
                        {'icon': '🔗', 'name': 'Conexión directa con Meta Conversions API', 'description': 'Cada conversión se envía desde tu servidor directamente a Meta, permitiendo que Facebook e Instagram identifiquen qué anuncios generaron resultados reales, incluso con bloqueadores de anuncios.'},
                        {'icon': '📊', 'name': 'Conexión directa con Google Enhanced Conversions', 'description': 'Las conversiones se reportan desde el servidor con datos encriptados del cliente. Google asocia cada conversión con el clic original del anuncio y optimiza las pujas automáticas con información real.'},
                        {'icon': '🛡️', 'name': 'Inmune a bloqueadores y restricciones de cookies', 'description': 'A diferencia del tracking tradicional, este módulo funciona desde tu servidor. No lo afectan los bloqueadores de anuncios, las restricciones de iOS 14+ ni la eliminación de cookies de terceros.'},
                        {'icon': '🔄', 'name': 'Deduplicación automática de eventos', 'description': 'El sistema mantiene el tracking del navegador como respaldo y sincroniza ambas fuentes con un identificador único. Meta y Google eliminan duplicados automáticamente.'},
                        {'icon': '🎯', 'name': 'Eventos de conversión personalizados', 'description': 'Se configuran los eventos que importan para tu negocio: formulario enviado, clic en WhatsApp, llamada agendada, propuesta vista, propuesta aceptada. Cada uno con su valor monetario para calcular ROAS real.'},
                        {'icon': '📈', 'name': 'Panel de estado de conversiones', 'description': 'Visualiza desde tu panel administrativo el estado de cada evento enviado: confirmado, pendiente o fallido. Incluye diagnóstico de calidad de matching.'},
                    ],
                },
                {
                    'id': 'reports_alerts_module',
                    'icon': '📬',
                    'title': 'Reportes y Alertas vía Correo, WhatsApp o Telegram',
                    'is_visible': True,
                    'description': (
                        'Mantente informado en todo momento con reportes automáticos y alertas '
                        'personalizadas que llegan directamente a tu correo, WhatsApp o Telegram.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'items': [
                        {'icon': '📧', 'name': 'Reportes automáticos por correo', 'description': 'Recibe resúmenes periódicos con las métricas clave de tu negocio directamente en tu bandeja de entrada, sin tener que entrar al sistema.'},
                        {'icon': '🔔', 'name': 'Alertas personalizadas', 'description': 'Configura notificaciones para eventos importantes: nuevas ventas, registros de usuarios, stock bajo, o cualquier métrica que definas.'},
                        {'icon': '💚', 'name': 'Integración con WhatsApp', 'description': 'Recibe alertas y reportes instantáneos en tu número de WhatsApp a través de la API oficial, ideal para estar al tanto desde el mismo canal donde atiendes a tus clientes.'},
                        {'icon': '✈️', 'name': 'Integración con Telegram', 'description': 'Recibe alertas y reportes instantáneos en tu chat de Telegram, ideal para estar al tanto desde cualquier lugar y en tiempo real.'},
                        {'icon': '⏰', 'name': 'Programación de envíos', 'description': 'Define la frecuencia y horario de tus reportes: diario, semanal, mensual o en tiempo real según tus necesidades.'},
                        {'icon': '📋', 'name': 'Resumen ejecutivo periódico', 'description': 'Informe consolidado con las métricas más relevantes de tu proyecto, diseñado para una lectura rápida y toma de decisiones ágil.'},
                    ],
                },
                {
                    'id': 'email_marketing_module',
                    'icon': '📧',
                    'title': 'Integración de Email Marketing',
                    'is_visible': True,
                    'description': (
                        'Conecta tu sitio web con plataformas de email marketing para '
                        'automatizar campañas, segmentar audiencias y aumentar la '
                        'conversión de visitantes en clientes.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 10,
                    'items': [
                        {'icon': '📬', 'name': 'Captura de leads', 'description': 'Formularios optimizados y pop-ups inteligentes para capturar emails de visitantes interesados en tu contenido o productos.'},
                        {'icon': '🔄', 'name': 'Automatizaciones de email', 'description': 'Secuencias automáticas de bienvenida, carritos abandonados, seguimiento post-compra y re-engagement de usuarios inactivos.'},
                        {'icon': '🎯', 'name': 'Segmentación de audiencia', 'description': 'Clasifica a tus suscriptores por comportamiento, intereses y datos demográficos para enviar mensajes relevantes y personalizados.'},
                        {'icon': '📊', 'name': 'Analítica de campañas', 'description': 'Métricas detalladas de apertura, clics, conversiones y ROI de cada campaña para optimizar tu estrategia de comunicación.'},
                        {'icon': '🔗', 'name': 'Integración con plataformas', 'description': 'Conexión nativa con Mailchimp, SendGrid, Brevo u otras plataformas líderes de email marketing según tus necesidades.'},
                    ],
                },
                {
                    'id': 'i18n_module',
                    'icon': '🌍',
                    'title': 'Multi-idioma y Localización Regional',
                    'is_visible': True,
                    'description': (
                        'Sistema de internacionalización nativo que permite servir tu sitio '
                        'en múltiples idiomas con flujo de traducción integrado, formatos '
                        'de moneda y fecha regionales, y la posibilidad de mostrar catálogos '
                        'o precios diferentes por país.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 15,
                    'items': [
                        {'icon': '🌐', 'name': 'Soporte multi-idioma nativo', 'description': 'Estructura preparada para servir todo el contenido del sitio en dos o más idiomas, con selector de idioma visible y persistencia de preferencia del usuario.'},
                        {'icon': '💱', 'name': 'Formatos regionales de moneda y fecha', 'description': 'Adaptación automática de formatos numéricos, monedas y fechas según la región del visitante o el idioma seleccionado.'},
                        {'icon': '🛒', 'name': 'Catálogos y precios por país', 'description': 'Posibilidad de mostrar productos, precios y disponibilidad diferenciados por región geográfica o mercado objetivo.'},
                        {'icon': '📝', 'name': 'Flujo de traducción integrado', 'description': 'Panel administrativo para gestionar las traducciones de cada sección sin necesidad de intervención técnica, con indicador de contenido pendiente por traducir.'},
                        {'icon': '🔍', 'name': 'Detección automática de idioma', 'description': 'El sitio detecta el idioma preferido del navegador del visitante y lo redirige automáticamente a la versión correspondiente, mejorando la experiencia desde el primer momento.'},
                    ],
                },
                {
                    'id': 'live_chat_module',
                    'icon': '💬',
                    'title': 'Chat en Vivo First-Party',
                    'is_visible': True,
                    'description': (
                        'Sistema de chat en tiempo real completamente alojado en la infraestructura '
                        'del cliente — sin Intercom, Drift ni LiveChat — donde los agentes atienden '
                        'desde el mismo panel administrativo. Los datos son 100% propios, sin costos '
                        'de suscripción crecientes ni riesgo de que la herramienta muestre anuncios '
                        'de competidores.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 40,
                    'items': [
                        {'icon': '🔌', 'name': 'Widget de chat embebido', 'description': 'Componente flotante integrado en el sitio web que permite al visitante iniciar una conversación en tiempo real sin salir de la página que está navegando.'},
                        {'icon': '🖥️', 'name': 'Panel de agente en el admin', 'description': 'Los agentes atienden las conversaciones directamente desde el panel administrativo del sitio, sin necesidad de aplicaciones externas ni cuentas adicionales.'},
                        {'icon': '📡', 'name': 'Comunicación en tiempo real (WebSocket)', 'description': 'Mensajes instantáneos bidireccionales entre visitante y agente mediante conexión persistente, sin retrasos ni necesidad de recargar la página.'},
                        {'icon': '🗄️', 'name': 'Historial de conversaciones propio', 'description': 'Todas las conversaciones se almacenan en la base de datos del cliente, con búsqueda, filtros por fecha y exportación. Los datos son 100% propiedad del cliente.'},
                        {'icon': '🤖', 'name': 'Respuestas automáticas configurables', 'description': 'Mensajes de bienvenida, respuestas fuera de horario y FAQ automatizadas que mantienen la atención activa incluso cuando no hay agentes disponibles.'},
                        {'icon': '🔔', 'name': 'Notificaciones de nuevos chats', 'description': 'Alertas en tiempo real al agente cuando un visitante inicia una conversación o envía un mensaje nuevo, garantizando tiempos de respuesta mínimos.'},
                    ],
                },
                {
                    'id': 'dark_mode_module',
                    'icon': '🌙',
                    'title': 'Motor de Tematización Dinámica (Dark Mode)',
                    'is_visible': True,
                    'description': (
                        'Soporte técnico nativo que respeta las preferencias del sistema operativo '
                        'del usuario, alternando fluidamente entre modo claro y oscuro con persistencia '
                        'de elección. Un requerimiento visual contemporáneo que reduce la fatiga visual '
                        'y proyecta modernidad absoluta.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'items': [
                        {'icon': '🎨', 'name': 'Paleta de colores dual', 'description': 'Diseño de dos sistemas de color completos (claro y oscuro) con variables CSS que se alternan de forma instantánea, manteniendo coherencia visual en ambos modos.'},
                        {'icon': '⚙️', 'name': 'Detección automática de preferencia del sistema', 'description': 'El sitio detecta la preferencia de tema del sistema operativo del usuario (prefers-color-scheme) y aplica el modo correspondiente desde la primera visita.'},
                        {'icon': '💾', 'name': 'Persistencia de elección del usuario', 'description': 'La preferencia manual del usuario se almacena y respeta en futuras visitas, prevaleciendo sobre la configuración del sistema operativo.'},
                        {'icon': '🔄', 'name': 'Transición fluida entre modos', 'description': 'Animación suave y elegante al alternar entre modo claro y oscuro, sin parpadeos ni saltos visuales que interrumpan la experiencia de navegación.'},
                        {'icon': '🖼️', 'name': 'Adaptación de imágenes y multimedia', 'description': 'Las imágenes, íconos y elementos gráficos se ajustan automáticamente al modo activo, optimizando contraste y legibilidad en cada contexto.'},
                    ],
                },
                {
                    'id': 'gift_cards_module',
                    'icon': '🎁',
                    'title': 'Gift Cards y Vouchers Digitales',
                    'is_visible': False,
                    'description': (
                        'Creación, venta y canje de tarjetas de regalo digitales con saldo '
                        'configurable, diseño de marca y código único verificable en checkout. '
                        'Genera ingresos anticipados y captura nuevos clientes a través '
                        'de los compradores existentes.'
                    ),
                    'is_calculator_module': False,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'items': [
                        {'icon': '💳', 'name': 'Creación y venta de gift cards', 'description': 'Los clientes pueden comprar tarjetas de regalo digitales con saldo configurable directamente desde tu sitio web, con proceso de pago integrado.'},
                        {'icon': '✅', 'name': 'Canje en checkout con código único', 'description': 'Cada gift card genera un código único verificable que el destinatario puede aplicar durante el proceso de compra como método de pago parcial o total.'},
                        {'icon': '📊', 'name': 'Historial de saldo y movimientos', 'description': 'Tanto el comprador como el destinatario pueden consultar el saldo disponible, movimientos realizados y fecha de vencimiento de cada tarjeta.'},
                        {'icon': '🎨', 'name': 'Diseño de marca personalizado', 'description': 'Las gift cards se generan con la identidad visual de tu marca, incluyendo logo, colores y mensaje personalizable del comprador para el destinatario.'},
                        {'icon': '⏰', 'name': 'Vencimiento configurable', 'description': 'Define políticas de vencimiento por tipo de tarjeta: sin vencimiento, 6 meses, 1 año, o personalizado. Incluye notificaciones automáticas antes de la expiración.'},
                    ],
                },
            ],
        },
    },
    {
        'section_type': 'development_stages',
        'title': '📌 Así avanzamos juntos',
        'order': 11,
        'is_wide_panel': True,
        'content_json': {
            'index': '11',
            'title': 'Etapas de contratación y desarrollo',
            'intro': 'Nuestro proceso está diseñado para ofrecer claridad, confianza y acompañamiento en cada fase 🧭:',
            'currentLabel': 'Actual',
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
        'section_type': 'process_methodology',
        'title': '⚙️ Proceso y Metodología',
        'order': 5,
        'is_wide_panel': False,
        'content_json': {
            'index': '5',
            'title': 'Proceso y Metodología',
            'intro': 'Trabajamos con un proceso estructurado que garantiza transparencia, calidad y entrega a tiempo en cada etapa del proyecto.',
            'activeStep': 0,
            'steps': [
                {
                    'icon': '🔍',
                    'title': 'Discovery',
                    'description': 'Investigamos tu negocio, competidores y usuarios para definir la estrategia ideal.',
                    'clientAction': 'Tu aporte: briefing inicial',
                },
                {
                    'icon': '🎨',
                    'title': 'Diseño UX/UI',
                    'description': 'Creamos prototipos interactivos en Figma con iteraciones hasta la aprobación visual.',
                    'clientAction': 'Tu aporte: feedback de diseño',
                },
                {
                    'icon': '💻',
                    'title': 'Desarrollo',
                    'description': 'Implementamos con código limpio, arquitectura escalable y las mejores prácticas.',
                    'clientAction': '',
                },
                {
                    'icon': '🧪',
                    'title': 'QA y Testing',
                    'description': 'Pruebas exhaustivas de funcionalidad, rendimiento, seguridad y compatibilidad.',
                    'clientAction': 'Tu aporte: pruebas de aceptación',
                },
                {
                    'icon': '🚀',
                    'title': 'Lanzamiento',
                    'description': 'Despliegue en producción, monitoreo post-lanzamiento y capacitación del equipo.',
                    'clientAction': '',
                },
            ],
        },
    },
    {
        'section_type': 'proposal_summary',
        'title': '📋 Resumen de la Propuesta',
        'order': 12,
        'is_wide_panel': False,
        'content_json': {
            'index': '12',
            'title': 'Resumen de la Propuesta',
            'subtitle': 'Los datos clave de esta propuesta en un vistazo:',
            'kpis': [
                {'value': '+40%', 'label': 'Incremento esperado en conversión web', 'source': 'HubSpot 2024'},
                {'value': '3x', 'label': 'Retorno estimado de inversión a 12 meses', 'source': 'Análisis interno'},
                {'value': '-60%', 'label': 'Reducción en tiempo de gestión manual', 'source': 'McKinsey Digital 2023'},
            ],
            '_kpi_note': (
                'Los KPIs son personalizables por cliente. Incluye métricas relevantes '
                'para el sector del cliente con fuentes verificables. Estos aparecerán '
                'como tarjetas destacadas al inicio del resumen.'
            ),
            'cards': [
                {
                    'icon': '💰',
                    'title': 'Inversión',
                    'description': 'Monto total del proyecto según la propuesta económica.',
                    'source': 'total_investment',
                },
                {
                    'icon': '⏱️',
                    'title': 'Tiempo Estimado',
                    'description': 'Duración aproximada del proyecto desde el kickoff hasta la entrega.',
                    'source': 'timeline_duration',
                },
                {
                    'icon': '🛡️',
                    'title': 'Garantía',
                    'description': '1 año de garantía incluida sobre el desarrollo entregado.',
                    'source': 'static',
                },
                {
                    'icon': '🧑‍💻',
                    'title': 'Soporte',
                    'description': 'Equipo dedicado de diseño, desarrollo y soporte post-lanzamiento.',
                    'source': 'static',
                },
                {
                    'icon': '📅',
                    'title': 'Vigencia',
                    'description': 'Vigencia de la propuesta a partir de su envío.',
                    'source': 'expires_at',
                },
            ],
        },
    },
    {
        'section_type': 'final_note',
        'title': '📝 Nuestro compromiso contigo',
        'order': 13,
        'is_wide_panel': False,
        'content_json': {
            'index': '13',
            'title': 'Nota Final y Próximos Pasos',
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
            'contactEmail': 'team@projectapp.co',
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
        'title': '✅ ¿Listo para empezar?',
        'order': 13,
        'is_wide_panel': False,
        'content_json': {
            'index': '13',
            'title': 'Próximos pasos',
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
                    'value': 'team@projectapp.co',
                    'link': 'mailto:team@projectapp.co',
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
    {
        'section_type': 'technical_document',
        'title': '🔧 Detalle técnico',
        'order': 14,
        'is_wide_panel': True,
        'content_json': deepcopy(EMPTY_TECHNICAL_DOCUMENT_JSON),
    },
]

DEFAULT_SECTIONS_EN = [
    {
        'section_type': 'greeting',
        'title': '👋 Greeting',
        'order': 0,
        'is_wide_panel': False,
        'content_json': {
            'proposalTitle': '',
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
        'section_type': 'investment',
        'title': '� Investment & Payment Options',
        'order': 4,
        'is_wide_panel': False,
        'content_json': {
            'index': '4',
            'title': 'Investment & Payment Options',
            'introText': 'The total investment for this project is:',
            'totalInvestment': '',
            'currency': 'USD',
            'whatsIncluded': [
                {'icon': '🎨', 'title': 'Design', 'description': 'UX/UI focused on conversion'},
                {'icon': '⚙️', 'title': 'Development', 'description': 'Full project implementation'},
                {'icon': '🚀', 'title': 'Deployment & Delivery', 'description': 'Production deployment and launch'},
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
                    {'icon': '🧠', 'label': 'vCPU', 'value': '4 vCPU cores'},
                    {'icon': '🧮', 'label': 'RAM', 'value': '8 GB dedicated RAM'},
                    {'icon': '💾', 'label': 'Storage', 'value': '100 GB NVMe storage'},
                    {'icon': '🌐', 'label': 'Bandwidth', 'value': '4 TB monthly'},
                    {'icon': '📍', 'label': 'Data centers', 'value': 'US, Brazil, France, Lithuania & India'},
                    {'icon': '🧬', 'label': 'Compatibility', 'value': 'Linux (Ubuntu)'},
                ],
                'hostingPercent': 30,
                'monthlyLabel': 'per month',
                'annualLabel': 'annual payment',
                'billingTiers': [
                    {
                        'frequency': 'semiannual',
                        'months': 6,
                        'discountPercent': 20,
                        'label': 'Semiannual',
                        'badge': 'Best price',
                    },
                    {
                        'frequency': 'quarterly',
                        'months': 3,
                        'discountPercent': 10,
                        'label': 'Quarterly',
                        'badge': '10% off',
                    },
                    {
                        'frequency': 'monthly',
                        'months': 1,
                        'discountPercent': 0,
                        'label': 'Monthly',
                        'badge': '',
                    },
                ],
            },
            'paymentMethods': [
                'Bank transfer',
                'Credit/Debit card',
            ],
            'modules': [],
            'valueReasons': [
                'Custom-made design',
                'Optimized code',
                'Post-launch support',
            ],
        },
    },
    {
        'section_type': 'timeline',
        'title': '⏳ Project Timeline',
        'order': 6,
        'is_wide_panel': True,
        'content_json': {
            'index': '6',
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
        'section_type': 'design_ux',
        'title': '🎨 Visual Design & User Experience',
        'order': 7,
        'is_wide_panel': False,
        'content_json': {
            'index': '7',
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
        'order': 8,
        'is_wide_panel': False,
        'content_json': {
            'index': '8',
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
        'section_type': 'value_added_modules',
        'title': '🎁 Included at no extra cost',
        'order': 10,
        'is_wide_panel': False,
        'content_json': {
            'index': '10',
            'title': 'What we add to your project at no extra cost',
            'intro': (
                'These modules are not billed separately. They are included because we believe '
                'every deliverable should ship with the minimum tools to operate, measure and '
                'understand it from day one.'
            ),
            'module_ids': ['admin_module', 'analytics_dashboard', 'kpi_dashboard_module', 'manual_module'],
            'justifications': {
                'admin_module': 'So you don\'t depend on a developer every time you need to change content.',
                'analytics_dashboard': 'So you know how your audience behaves without paying for external tools.',
                'kpi_dashboard_module': 'To make decisions with real-time data, not intuition.',
                'manual_module': 'So anyone on your team can understand the system without training sessions.',
            },
            'footer_note': 'Additional total: $0. Already priced inside the project budget.',
        },
    },
    {
        'section_type': 'functional_requirements',
        'title': '🧩 Functional Requirements',
        'order': 9,
        'is_wide_panel': True,
        'content_json': {
            'index': '9',
            'title': 'Functional Requirements',
            'intro': 'Below are the functional requirements for the project.',
            'groups': [
                {
                    'id': 'views',
                    'icon': '🖥️',
                    'title': 'Views',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
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
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
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
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
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
                    'id': 'admin_module',
                    'icon': '🛠️',
                    'title': 'Admin Module',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
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
                {
                    'id': 'analytics_dashboard',
                    'icon': '📊',
                    'title': 'Analytics Module',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
                    'description': (
                        'Smart reporting dashboard with real-time metrics to understand '
                        'visitor behavior and make data-driven decisions.'
                    ),
                    'items': [
                        {
                            'icon': '🔥',
                            'name': 'Most Visited Pages & Products',
                            'description': (
                                'Identify which sections and products generate the most interest. '
                                'Prioritize content, reorganize your catalog, and boost '
                                'what truly attracts your visitors.'
                            ),
                        },
                        {
                            'icon': '🔄',
                            'name': 'New vs Returning Visitors',
                            'description': (
                                'Distinguish between first-time visitors and returning ones. '
                                'Helps measure loyalty and evaluate whether your retention '
                                'strategies are working.'
                            ),
                        },
                        {
                            'icon': '📱',
                            'name': 'Audience Devices',
                            'description': (
                                'Know which devices your users browse from: mobile, tablet, or desktop. '
                                'Optimize the experience for the device most used by your audience.'
                            ),
                        },
                        {
                            'icon': '🌍',
                            'name': 'Geographic Origin',
                            'description': (
                                'See which cities or countries your visitors come from. '
                                'Ideal for focusing ad campaigns and understanding where '
                                'your real market is.'
                            ),
                        },
                        {
                            'icon': '🔗',
                            'name': 'Traffic Sources',
                            'description': (
                                'Discover how users reach your site: organic search, '
                                'social media, direct links, or paid campaigns. Invest '
                                'your marketing budget more wisely.'
                            ),
                        },
                        {
                            'icon': '📈',
                            'name': 'Visit Trends',
                            'description': (
                                'Visit evolution chart over time. Detect peaks, '
                                'measure campaign impact, and understand seasonal patterns '
                                'in your audience.'
                            ),
                        },
                    ],
                },
                {
                    'id': 'kpi_dashboard_module',
                    'icon': '📊',
                    'title': 'KPI Dashboard & Metrics',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
                    'description': (
                        'Control panel complementary to the analytics module, with real-time '
                        'key performance indicators to monitor the health of your business '
                        'and make data-driven decisions.'
                    ),
                    'items': [
                        {'icon': '📈', 'name': 'Real-time KPIs', 'description': 'Visualize the most important indicators of your business updated instantly: sales, conversions, traffic and more.'},
                        {'icon': '📊', 'name': 'Interactive Charts', 'description': 'Visual dashboards with line, bar and pie charts that allow filtering by period, category or segment.'},
                        {'icon': '🔔', 'name': 'Performance Alerts', 'description': 'Automatic notifications when a KPI falls below the defined threshold or exceeds a set goal.'},
                        {'icon': '📥', 'name': 'Report Export', 'description': 'Download reports in CSV to share with your team or stakeholders without needing to access the system.'},
                    ],
                },
                {
                    'id': 'manual_module',
                    'icon': '📘',
                    'title': 'Interactive User Manual',
                    'is_visible': True,
                    'selected': True,
                    'price_percent': 0,
                    'description': (
                        'A non-technical interactive manual/wiki, with a navigable index and search, '
                        'that describes the processes, flows, dependencies, roles and responsibilities '
                        'of your application. Designed so anyone on the team can understand the '
                        'system without asking the developer for help.'
                    ),
                    'items': [
                        {'icon': '🔎', 'name': 'Search and index navigation', 'description': 'Find any process, view or role in seconds.'},
                        {'icon': '🧭', 'name': 'Step-by-step processes and flows', 'description': 'Every system flow documented in plain language, no jargon.'},
                        {'icon': '👥', 'name': 'Roles and responsibilities', 'description': 'Who does what inside the application and what permissions each role has.'},
                        {'icon': '🔗', 'name': 'Dependencies and business rules', 'description': 'How modules relate to each other and which rules apply.'},
                    ],
                },
            ],
            'additionalModules': [
                {
                    'id': 'integration_electronic_invoicing',
                    'icon': '🧾',
                    'title': 'Electronic Invoicing & DIAN Integration (API Integration)',
                    'is_visible': True,
                    'description': (
                        'Platform connection with the client\'s invoicing system to generate, '
                        'send, query, and reconcile electronic receipts from business operational flows. '
                        'Includes synchronization of clients, products, taxes, invoices, '
                        'credit/debit notes and support documents, with fiscal status traceability '
                        'and support for API automations.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 60,
                    'is_invite': False,
                    'items': [
                        {'icon': '📄', 'name': 'Electronic Receipt Generation', 'description': 'Automatic creation of invoices, credit/debit notes, and support documents from business operational flows.'},
                        {'icon': '🔄', 'name': 'Fiscal Data Synchronization', 'description': 'Bidirectional synchronization of clients, products, taxes, and receipts with the invoicing system.'},
                        {'icon': '📊', 'name': 'Fiscal Status Traceability', 'description': 'Query and track the status of each receipt: issued, accepted, rejected, or in process with DIAN.'},
                        {'icon': '🔗', 'name': 'Colombian Provider Integration', 'description': 'Connection with Siigo, Alegra, or other providers with presence and documented API in Colombia.'},
                        {'icon': '⚙️', 'name': 'API Automations', 'description': 'Automatic flows for payment reconciliation, invoice issuance upon order completion, and fiscal status notifications.'},
                    ],
                },
                {
                    'id': 'integration_regional_payments',
                    'icon': '🇨🇴',
                    'title': 'Regional Payment Gateway (Colombia) (API Integration)',
                    'is_visible': True,
                    'description': (
                        'Integration with payment gateways present in the Colombian market '
                        'to facilitate local transactions with multiple payment methods.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'is_invite': False,
                    'items': [
                        {'icon': '💳', 'name': 'PayU', 'description': 'One of the most used in Colombia, supports card, PSE, Efecty, Baloto, Nequi, Daviplata.'},
                        {'icon': '🏦', 'name': 'Wompi (Bancolombia)', 'description': 'Excellent local option with PSE, cards, Nequi, and Bancolombia button support.'},
                        {'icon': '💰', 'name': 'ePayco', 'description': 'Easy-to-integrate Colombian alternative supporting PSE, cards, and physical collections.'},
                    ],
                },
                {
                    'id': 'integration_international_payments',
                    'icon': '🌎',
                    'title': 'International Payment Gateway (API Integration)',
                    'is_visible': True,
                    'description': (
                        'Integration with international payment gateways to facilitate '
                        'global transactions with credit/debit cards and international accounts.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'is_invite': False,
                    'items': [
                        {'icon': '💳', 'name': 'Stripe', 'description': 'Ideal for credit/debit card payments, widely used worldwide. Supports subscriptions, one-time payments, and multiple currencies.'},
                        {'icon': '🅿️', 'name': 'PayPal', 'description': 'Globally recognized platform, allows payments with PayPal balance, cards, and international accounts.'},
                    ],
                },
                {
                    'id': 'pwa_module',
                    'icon': '📱',
                    'title': 'Installable Mobile App (PWA)',
                    'is_visible': True,
                    'description': (
                        'Turn your website into an installable application that works '
                        'even without an internet connection. Deliver a native-like experience '
                        'directly from the browser, no app stores required.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 40,
                    'items': [
                        {'icon': '📲', 'name': 'Device Installation', 'description': 'Users can install your site as an app on their phone or computer, with direct access from the home screen.'},
                        {'icon': '📡', 'name': 'Offline Functionality', 'description': 'The site remains accessible without an internet connection, showing previously loaded content and syncing data upon reconnection.'},
                        {'icon': '🔔', 'name': 'Push Notifications', 'description': 'Send direct notifications to user devices to keep them informed about news, promotions, or updates.'},
                        {'icon': '🎨', 'name': 'Custom Splash Screen', 'description': 'Branded splash screen with your visual identity when opening the app, creating a professional experience from the first moment.'},
                        {'icon': '🔄', 'name': 'Background Sync', 'description': 'Data syncs automatically when the device reconnects, ensuring up-to-date information without user intervention.'},
                        {'icon': '⬆️', 'name': 'Automatic Updates', 'description': 'The application updates transparently without requiring any user action, always running the latest version.'},
                    ],
                },
                {
                    'id': 'corporate_branding_module',
                    'icon': '🎨',
                    'title': 'Visual Identity & Corporate Branding',
                    'is_visible': True,
                    'description': (
                        'We apply your visual identity consistently across every system touchpoint — emails, '
                        'documents, social previews and internal screens — so your brand feels professional and '
                        'coherent everywhere your customers interact with it.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 35,
                    'items': [
                        {'icon': '✉️', 'name': 'Branded Transactional Emails', 'description': 'HTML templates with logo, colors, typography and brand signature applied across all system emails — welcome, confirmations, alerts, password recovery and notifications — instead of plain-text or generic messages.'},
                        {'icon': '📄', 'name': 'PDFs & Exports with Branding', 'description': 'Invoices, reports, certificates, receipts and Excel/CSV downloads generated from the system with branded headers, corporate color palette and brand footers. Every document that leaves the platform reinforces the business\'s professional image.'},
                        {'icon': '🔗', 'name': 'Social Link Preview Cards (Open Graph)', 'description': 'When someone shares a link to the site or a proposal on WhatsApp, Facebook, LinkedIn or X, a card with logo, image and brand colors appears — not a plain link. Direct impact on perception and CTR.'},
                        {'icon': '🖥️', 'name': 'System Screens with Brand Identity', 'description': 'Error pages (404, 500), maintenance, login and loading states (skeletons, spinners) with visual identity and messaging in the brand\'s voice, instead of the framework\'s generic screens.'},
                        {'icon': '🔎', 'name': 'Structured Metadata for Search & AI', 'description': 'JSON-LD Organization with logo, colors, social profiles and contact data — so Google, Bing and assistants like ChatGPT or Perplexity correctly display the brand in knowledge panels, enriched results and citations.'},
                    ],
                },
                {
                    'id': 'ai_module',
                    'icon': '🤖',
                    'title': 'AI Integration & Automation',
                    'is_visible': True,
                    'description': (
                        'Supercharge your project with artificial intelligence. '
                        'We explore together how to tailor AI solutions to your specific business needs.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 0,
                    'is_invite': True,
                    'invite_note': (
                        '🤝 We invite you to a personalized call where we\'ll explore together '
                        'how artificial intelligence can transform your business. You\'ll learn '
                        'about our solutions, how we tailor them to your specific case, '
                        'and associated costs \u2014 no commitment required.'
                    ),
                    'items': [
                        {'icon': '⚡', 'name': 'Automations', 'description': 'Intelligent workflows that execute repetitive tasks autonomously, freeing up time for what truly matters.'},
                        {'icon': '📊', 'name': 'Natural Language Data Analysis', 'description': 'Query your data using plain language questions and get clear answers, charts, and reports without technical expertise.'},
                        {'icon': '✍️', 'name': 'Content Generation', 'description': 'AI-assisted creation of texts, product descriptions, blog articles, and communications, maintaining your brand tone and style.'},
                        {'icon': '💬', 'name': 'Intelligent Communication', 'description': 'Chatbots and virtual assistants that serve your customers 24/7, answer FAQs, and escalate conversations when needed.'},
                        {'icon': '📄', 'name': 'Document Processing', 'description': 'Automatic extraction and classification of information from invoices, contracts, and forms, reducing manual work and errors.'},
                        {'icon': '🔍', 'name': 'Search & Research', 'description': 'Semantic search engine that understands user intent and returns relevant results, not just text matches.'},
                        {'icon': '🛡️', 'name': 'Security & Moderation', 'description': 'Automatic detection of inappropriate content, spam, and suspicious activity to keep your platform safe and trustworthy.'},
                        {'icon': '⚙️', 'name': 'Process Optimization', 'description': 'Intelligent analysis of your operations to identify bottlenecks, suggest improvements, and automate routine decisions.'},
                        {'icon': '🎓', 'name': 'Learning & Training', 'description': 'Adaptive systems that personalize the learning experience according to each user\'s pace and level.'},
                        {'icon': '🔮', 'name': 'Prediction & Forecasting', 'description': 'Predictive models that anticipate trends, demand, and customer behavior for more informed decision-making.'},
                        {'icon': '🔗', 'name': 'Integration & Orchestration', 'description': 'Intelligent connection between your existing tools and services, coordinating data flows and actions across multiple platforms.'},
                    ],
                },
                {
                    'id': 'integration_conversion_tracking',
                    'icon': '📡',
                    'title': 'Smart Conversions (Meta & Google Ads) (API Integration)',
                    'is_visible': True,
                    'description': (
                        'Maximize your advertising ROI with server-side conversion tracking. '
                        'Your website reports every valuable action directly to Meta and Google, '
                        'without relying on cookies or the visitor\'s browser.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 0,
                    'is_invite': True,
                    'invite_note': (
                        '🤝 We invite you to a call where we\'ll analyze your current '
                        'advertising strategy and design together the server-side integration '
                        'with Meta and Google Ads. See how to maximize your ROAS with '
                        'accurate conversion data \u2014 no commitment required.'
                    ),
                    'items': [
                        {'icon': '🔗', 'name': 'Direct Meta Conversions API Connection', 'description': 'Every conversion is sent from your server directly to Meta, allowing Facebook and Instagram to identify which ads generated real results, even with ad blockers.'},
                        {'icon': '📊', 'name': 'Direct Google Enhanced Conversions Connection', 'description': 'Conversions are reported from the server with encrypted client data. Google matches each conversion to the original ad click and optimizes automated bids with real information.'},
                        {'icon': '🛡️', 'name': 'Immune to Blockers & Cookie Restrictions', 'description': 'Unlike traditional tracking, this module works from your server. It is not affected by ad blockers, iOS 14+ restrictions, or third-party cookie deprecation.'},
                        {'icon': '🔄', 'name': 'Automatic Event Deduplication', 'description': 'The system keeps browser tracking as a backup and syncs both sources with a unique identifier. Meta and Google automatically remove duplicates.'},
                        {'icon': '🎯', 'name': 'Custom Conversion Events', 'description': 'Configure the events that matter to your business: form submitted, WhatsApp click, call booked, proposal viewed, proposal accepted. Each with its monetary value to calculate real ROAS.'},
                        {'icon': '📈', 'name': 'Conversion Status Panel', 'description': 'View from your admin panel the status of each event sent: confirmed, pending, or failed. Includes matching quality diagnostics.'},
                    ],
                },
                {
                    'id': 'reports_alerts_module',
                    'icon': '📬',
                    'title': 'Reports & Alerts via Email, WhatsApp or Telegram',
                    'is_visible': True,
                    'description': (
                        'Stay informed at all times with automated reports and customized alerts '
                        'delivered directly to your email, WhatsApp or Telegram.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'items': [
                        {'icon': '📧', 'name': 'Automated Email Reports', 'description': 'Receive periodic summaries with key business metrics directly in your inbox, without having to log into the system.'},
                        {'icon': '🔔', 'name': 'Custom Alerts', 'description': 'Set up notifications for important events: new sales, user registrations, low stock, or any metric you define.'},
                        {'icon': '💚', 'name': 'WhatsApp Integration', 'description': 'Receive instant alerts and reports on your WhatsApp number through the official API, perfect for staying informed from the same channel where you serve your customers.'},
                        {'icon': '✈️', 'name': 'Telegram Integration', 'description': 'Receive instant alerts and reports in your Telegram chat, perfect for staying informed from anywhere in real time.'},
                        {'icon': '⏰', 'name': 'Scheduled Delivery', 'description': 'Define the frequency and timing of your reports: daily, weekly, monthly, or real-time based on your needs.'},
                        {'icon': '📋', 'name': 'Periodic Executive Summary', 'description': 'Consolidated report with the most relevant metrics of your project, designed for quick reading and agile decision-making.'},
                    ],
                },
                {
                    'id': 'email_marketing_module',
                    'icon': '📧',
                    'title': 'Email Marketing Integration',
                    'is_visible': True,
                    'description': (
                        'Connect your website with email marketing platforms to '
                        'automate campaigns, segment audiences and increase '
                        'visitor-to-customer conversion.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 10,
                    'items': [
                        {'icon': '📬', 'name': 'Lead Capture', 'description': 'Optimized forms and smart pop-ups to capture emails from visitors interested in your content or products.'},
                        {'icon': '🔄', 'name': 'Email Automations', 'description': 'Automatic welcome sequences, abandoned carts, post-purchase follow-up and re-engagement of inactive users.'},
                        {'icon': '🎯', 'name': 'Audience Segmentation', 'description': 'Classify your subscribers by behavior, interests and demographics to send relevant, personalized messages.'},
                        {'icon': '📊', 'name': 'Campaign Analytics', 'description': 'Detailed metrics on opens, clicks, conversions and ROI of each campaign to optimize your communication strategy.'},
                        {'icon': '🔗', 'name': 'Platform Integration', 'description': 'Native connection with Mailchimp, SendGrid, Brevo or other leading email marketing platforms based on your needs.'},
                    ],
                },
                {
                    'id': 'i18n_module',
                    'icon': '🌍',
                    'title': 'Multi-language & Regional Localization',
                    'is_visible': True,
                    'description': (
                        'Native internationalization system that serves your site '
                        'in multiple languages with an integrated translation workflow, '
                        'regional currency and date formats, and the ability to display '
                        'different catalogs or prices by country.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 15,
                    'items': [
                        {'icon': '🌐', 'name': 'Native Multi-language Support', 'description': 'Structure ready to serve all site content in two or more languages, with a visible language selector and user preference persistence.'},
                        {'icon': '💱', 'name': 'Regional Currency & Date Formats', 'description': 'Automatic adaptation of numeric formats, currencies, and dates based on the visitor\'s region or selected language.'},
                        {'icon': '🛒', 'name': 'Catalogs & Pricing by Country', 'description': 'Ability to display products, prices, and availability differentiated by geographic region or target market.'},
                        {'icon': '📝', 'name': 'Integrated Translation Workflow', 'description': 'Admin panel to manage translations for each section without technical intervention, with an indicator for content pending translation.'},
                        {'icon': '🔍', 'name': 'Automatic Language Detection', 'description': 'The site detects the visitor\'s preferred browser language and automatically redirects to the corresponding version, improving the experience from the first moment.'},
                    ],
                },
                {
                    'id': 'live_chat_module',
                    'icon': '💬',
                    'title': 'First-Party Live Chat',
                    'is_visible': True,
                    'description': (
                        'Real-time chat system fully hosted on the client\'s infrastructure '
                        '— no Intercom, Drift, or LiveChat — where agents respond '
                        'from the same admin panel. Data is 100% owned, with no growing '
                        'subscription costs or risk of the tool displaying competitor ads.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 40,
                    'items': [
                        {'icon': '🔌', 'name': 'Embedded Chat Widget', 'description': 'Floating component integrated into the website that allows the visitor to start a real-time conversation without leaving the page they are browsing.'},
                        {'icon': '🖥️', 'name': 'Agent Panel in Admin', 'description': 'Agents handle conversations directly from the site\'s admin panel, without needing external applications or additional accounts.'},
                        {'icon': '📡', 'name': 'Real-time Communication (WebSocket)', 'description': 'Instant bidirectional messages between visitor and agent via persistent connection, with no delays or page reloads needed.'},
                        {'icon': '🗄️', 'name': 'Owned Conversation History', 'description': 'All conversations are stored in the client\'s database, with search, date filters, and export. Data is 100% client-owned.'},
                        {'icon': '🤖', 'name': 'Configurable Auto-responses', 'description': 'Welcome messages, after-hours responses, and automated FAQs that keep support active even when no agents are available.'},
                        {'icon': '🔔', 'name': 'New Chat Notifications', 'description': 'Real-time alerts to the agent when a visitor starts a conversation or sends a new message, ensuring minimal response times.'},
                    ],
                },                {
                    'id': 'dark_mode_module',
                    'icon': '🌙',
                    'title': 'Dynamic Theming Engine (Dark Mode)',
                    'is_visible': True,
                    'description': (
                        'Native technical support that respects the user\'s operating system preferences, '
                        'seamlessly switching between light and dark mode with choice persistence. '
                        'A contemporary visual requirement that reduces eye strain '
                        'and projects absolute modernity.'
                    ),
                    'is_calculator_module': True,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'items': [
                        {'icon': '🎨', 'name': 'Dual Color Palette', 'description': 'Design of two complete color systems (light and dark) with CSS variables that switch instantly, maintaining visual coherence in both modes.'},
                        {'icon': '⚙️', 'name': 'Automatic System Preference Detection', 'description': 'The site detects the user\'s OS theme preference (prefers-color-scheme) and applies the corresponding mode from the first visit.'},
                        {'icon': '💾', 'name': 'User Choice Persistence', 'description': 'The user\'s manual preference is stored and respected on future visits, taking precedence over the operating system configuration.'},
                        {'icon': '🔄', 'name': 'Smooth Mode Transition', 'description': 'Elegant and smooth animation when switching between light and dark mode, without flashes or visual jumps that interrupt the browsing experience.'},
                        {'icon': '🖼️', 'name': 'Image & Media Adaptation', 'description': 'Images, icons, and graphic elements automatically adjust to the active mode, optimizing contrast and readability in each context.'},
                    ],
                },
                {
                    'id': 'gift_cards_module',
                    'icon': '🎁',
                    'title': 'Gift Cards & Digital Vouchers',
                    'is_visible': False,
                    'description': (
                        'Create, sell, and redeem digital gift cards with configurable balance, '
                        'branded design, and a unique verifiable code at checkout. '
                        'Generate upfront revenue and capture new customers through '
                        'existing buyers.'
                    ),
                    'is_calculator_module': False,
                    'default_selected': False,
                    'selected': False,
                    'price_percent': 20,
                    'items': [
                        {'icon': '💳', 'name': 'Gift Card Creation & Sales', 'description': 'Customers can purchase digital gift cards with configurable balance directly from your website, with an integrated payment process.'},
                        {'icon': '✅', 'name': 'Checkout Redemption with Unique Code', 'description': 'Each gift card generates a unique verifiable code that the recipient can apply during checkout as a partial or full payment method.'},
                        {'icon': '📊', 'name': 'Balance & Transaction History', 'description': 'Both the buyer and recipient can check the available balance, transactions made, and expiration date for each card.'},
                        {'icon': '🎨', 'name': 'Custom Branded Design', 'description': 'Gift cards are generated with your brand\'s visual identity, including logo, colors, and a customizable message from the buyer to the recipient.'},
                        {'icon': '⏰', 'name': 'Configurable Expiration', 'description': 'Define expiration policies per card type: no expiration, 6 months, 1 year, or custom. Includes automatic notifications before expiration.'},
                    ],
                },

            ],
        },
    },
    {
        'section_type': 'development_stages',
        'title': '📌 Contracting & Development Stages',
        'order': 11,
        'is_wide_panel': True,
        'content_json': {
            'index': '11',
            'title': 'Contracting & Development Stages',
            'intro': 'Our process is designed to offer clarity, trust, and support at every stage 🧭:',
            'currentLabel': 'Current',
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
                    'icon': '�',
                    'title': 'Native Development',
                    'description': 'Custom coding, payment gateway and email integration.',
                },
                {
                    'icon': '🚀',
                    'title': 'Launch & Deployment',
                    'description': 'QA, production deployment, and domain setup.',
                },
                {
                    'icon': '�',
                    'title': 'Final Delivery',
                    'description': 'Site online and validated, closing the digital transformation cycle.',
                },
            ],
        },
    },
    {
        'section_type': 'process_methodology',
        'title': '⚙️ Process & Methodology',
        'order': 5,
        'is_wide_panel': False,
        'content_json': {
            'index': '5',
            'title': 'Process & Methodology',
            'intro': 'We work with a structured process that ensures transparency, quality, and on-time delivery at every stage.',
            'activeStep': 0,
            'steps': [
                {
                    'icon': '🔍',
                    'title': 'Discovery',
                    'description': 'We research your business, competitors, and users to define the ideal strategy.',
                    'clientAction': 'Your input: initial briefing',
                },
                {
                    'icon': '🎨',
                    'title': 'UX/UI Design',
                    'description': 'We create interactive prototypes in Figma with iterations until visual approval.',
                    'clientAction': 'Your input: design feedback',
                },
                {
                    'icon': '💻',
                    'title': 'Development',
                    'description': 'We implement with clean code, scalable architecture, and best practices.',
                    'clientAction': '',
                },
                {
                    'icon': '🧪',
                    'title': 'QA & Testing',
                    'description': 'Thorough testing of functionality, performance, security, and compatibility.',
                    'clientAction': 'Your input: acceptance testing',
                },
                {
                    'icon': '🚀',
                    'title': 'Launch',
                    'description': 'Production deployment, post-launch monitoring, and team training.',
                    'clientAction': '',
                },
            ],
        },
    },
    {
        'section_type': 'proposal_summary',
        'title': '📋 Proposal Summary',
        'order': 12,
        'is_wide_panel': False,
        'content_json': {
            'index': '12',
            'title': 'Proposal Summary',
            'subtitle': 'Key details of this proposal at a glance:',
            'kpis': [
                {'value': '+40%', 'label': 'Expected increase in web conversion', 'source': 'HubSpot 2024'},
                {'value': '3x', 'label': 'Estimated ROI within 12 months', 'source': 'Internal analysis'},
                {'value': '-60%', 'label': 'Reduction in manual management time', 'source': 'McKinsey Digital 2023'},
            ],
            '_kpi_note': (
                'KPIs are customizable per client. Include metrics relevant '
                'to the client\'s industry with verifiable sources. These will appear '
                'as highlighted cards at the top of the summary.'
            ),
            'cards': [
                {
                    'icon': '💰',
                    'title': 'Investment',
                    'description': 'Total project amount as per the economic proposal.',
                    'source': 'total_investment',
                },
                {
                    'icon': '⏱️',
                    'title': 'Estimated Time',
                    'description': 'Approximate project duration from kickoff to delivery.',
                    'source': 'timeline_duration',
                },
                {
                    'icon': '🛡️',
                    'title': 'Warranty',
                    'description': '1-year warranty included on the delivered development.',
                    'source': 'static',
                },
                {
                    'icon': '🧑‍💻',
                    'title': 'Support',
                    'description': 'Dedicated team for design, development, and post-launch support.',
                    'source': 'static',
                },
                {
                    'icon': '📅',
                    'title': 'Validity',
                    'description': 'Proposal validity from the date it was sent.',
                    'source': 'expires_at',
                },
            ],
        },
    },
    {
        'section_type': 'final_note',
        'title': '📝 Final Note & Next Steps',
        'order': 13,
        'is_wide_panel': False,
        'content_json': {
            'index': '13',
            'title': 'Final Note & Next Steps',
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
            'contactEmail': 'team@projectapp.co',
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
        'order': 13,
        'is_wide_panel': False,
        'content_json': {
            'index': '13',
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
                    'value': 'team@projectapp.co',
                    'link': 'mailto:team@projectapp.co',
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
    {
        'section_type': 'technical_document',
        'title': '🔧 Technical document',
        'order': 14,
        'is_wide_panel': True,
        'content_json': deepcopy(EMPTY_TECHNICAL_DOCUMENT_JSON),
    },
]


class ProposalService:
    """
    Business logic for proposal lifecycle management.
    """
    DEFAULT_EXPIRATION_DAYS = 21

    @staticmethod
    def _require_valid_client_email(proposal):
        """Raise ValueError if proposal lacks a deliverable client_email."""
        if not proposal.client_email:
            raise ValueError('Client email is required to send a proposal.')
        from content.utils import validate_email_domain_mx
        if not validate_email_domain_mx(proposal.client_email):
            raise ValueError(
                'El dominio del correo del cliente no puede recibir emails.'
            )

    @staticmethod
    def get_default_expiration_days(language='es'):
        """
        Return the configured default expiration period (in days) for a language.

        Falls back to 21 days when no DB config exists.
        """
        from content.models import ProposalDefaultConfig

        config = ProposalDefaultConfig.objects.filter(language=language).first()
        if config and config.expiration_days:
            return int(config.expiration_days)
        return ProposalService.DEFAULT_EXPIRATION_DAYS

    @staticmethod
    def compute_default_expires_at(language='es'):
        """Return a timezone-aware datetime for the default expiration."""
        from django.utils import timezone
        from datetime import timedelta

        return timezone.now() + timedelta(
            days=ProposalService.get_default_expiration_days(language),
        )

    @staticmethod
    def send_proposal(proposal):
        """
        Mark proposal as sent and schedule the Huey reminder tasks.

        Sets status=SENT, sent_at=now(), auto-sets expires_at using the
        configured default expiration days (21 by default) if not already
        set, and schedules reminder (day 10) and urgency
        (day 15) emails.

        Args:
            proposal: BusinessProposal instance.

        Raises:
            ValueError: If client_email is not set.
        """
        ProposalService._require_valid_client_email(proposal)

        now = timezone.now()
        proposal.status = 'sent'
        proposal.sent_at = now
        update_fields = ['status', 'sent_at']

        if not proposal.expires_at:
            proposal.expires_at = now + timedelta(
                days=ProposalService.get_default_expiration_days(proposal.language),
            )
            update_fields.append('expires_at')

        proposal.save(update_fields=update_fields)

        ProposalService._send_initial_email(proposal)
        ProposalService._schedule_email_tasks(proposal)

    @staticmethod
    def resend_proposal(proposal):
        """
        Re-send a proposal keeping the existing expires_at.

        Resets sent_at, status, reminder_sent_at, urgency_email_sent_at
        and re-schedules email tasks based on remaining time.

        Args:
            proposal: BusinessProposal instance.

        Raises:
            ValueError: If client_email is not set.
        """
        ProposalService._require_valid_client_email(proposal)

        now = timezone.now()
        proposal.status = 'sent'
        proposal.sent_at = now
        proposal.reminder_sent_at = None
        proposal.urgency_email_sent_at = None
        proposal.save(update_fields=[
            'status', 'sent_at', 'reminder_sent_at', 'urgency_email_sent_at',
        ])

        ProposalService._send_initial_email(proposal)
        ProposalService._schedule_email_tasks(proposal)

    @staticmethod
    def _send_initial_email(proposal):
        """Send the proposal link email to the client."""
        try:
            from content.services.proposal_email_service import (
                ProposalEmailService,
            )
            ProposalEmailService.send_proposal_to_client(proposal)
        except Exception:
            logger.exception(
                'Failed to send initial email for proposal %s',
                proposal.uuid,
            )

    @staticmethod
    def _schedule_email_tasks(proposal):
        """
        Schedule reminder (day N) and urgency (day M) Huey tasks.

        Skips scheduling if the target day has already passed or if
        it would fire after the proposal's expiration date.
        """
        try:
            from content.tasks import send_proposal_reminder, send_urgency_reminder

            now = timezone.now()
            expires = proposal.expires_at

            # Schedule reminder at reminder_days (default 10)
            reminder_target = proposal.sent_at + timedelta(days=proposal.reminder_days)
            if reminder_target > now and (not expires or reminder_target < expires):
                delay_seconds = int((reminder_target - now).total_seconds())
                send_proposal_reminder.schedule(
                    args=(proposal.id,), delay=delay_seconds
                )
                logger.info(
                    'Scheduled reminder for proposal %s in %d days',
                    proposal.uuid, proposal.reminder_days,
                )

            # Schedule urgency at urgency_reminder_days (default 15)
            urgency_target = proposal.sent_at + timedelta(
                days=proposal.urgency_reminder_days
            )
            if urgency_target > now and (not expires or urgency_target < expires):
                delay_seconds = int((urgency_target - now).total_seconds())
                send_urgency_reminder.schedule(
                    args=(proposal.id,), delay=delay_seconds
                )
                logger.info(
                    'Scheduled urgency reminder for proposal %s in %d days',
                    proposal.uuid, proposal.urgency_reminder_days,
                )
        except Exception:
            logger.exception(
                'Failed to schedule email tasks for proposal %s', proposal.uuid
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
    def get_hardcoded_defaults(language='es'):
        """
        Return a deep copy of the hardcoded default sections (no DB lookup).

        Args:
            language: 'es' for Spanish (default), 'en' for English.

        Returns:
            list[dict]: Deep copy of DEFAULT_SECTIONS or DEFAULT_SECTIONS_EN.
        """
        import copy
        source = DEFAULT_SECTIONS_EN if language == 'en' else DEFAULT_SECTIONS
        return copy.deepcopy(source)

    @staticmethod
    def get_default_sections(language='es'):
        """
        Return the default section configurations for a new proposal.

        Checks the DB-backed ProposalDefaultConfig first; falls back to
        the hardcoded DEFAULT_SECTIONS / DEFAULT_SECTIONS_EN.

        Args:
            language: 'es' for Spanish (default), 'en' for English.

        Returns:
            list[dict]: List of section configs with section_type, title, order,
                        is_wide_panel, and content_json.
        """
        import copy
        from content.models import ProposalDefaultConfig

        config = ProposalDefaultConfig.objects.filter(language=language).first()
        if config and config.sections_json:
            return copy.deepcopy(config.sections_json)

        source = DEFAULT_SECTIONS_EN if language == 'en' else DEFAULT_SECTIONS
        return copy.deepcopy(source)

    @staticmethod
    def get_default_section(language, section_type):
        """Return the default config for a single section_type, or None."""
        for cfg in ProposalService.get_default_sections(language=language):
            if cfg['section_type'] == section_type:
                return cfg
        return None
