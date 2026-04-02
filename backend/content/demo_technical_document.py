"""
Rich technical_document content_json for dev/demo seeds (fake proposals, seed_platform_data).

Keys must stay aligned with EMPTY_TECHNICAL_DOCUMENT_JSON; see tests for parity checks.
"""

from copy import deepcopy

from content.technical_document_defaults import EMPTY_TECHNICAL_DOCUMENT_JSON


def _build_demo_technical_document_json():
    d = deepcopy(EMPTY_TECHNICAL_DOCUMENT_JSON)

    d['purpose'] = (
        'Este detalle técnico describe la arquitectura, el stack, los entornos y los requisitos '
        'del e-commerce acordado en la propuesta comercial. Sirve de referencia para '
        'equipo técnico, auditorías y alineación con el tablero de entregas.'
    )

    d['stack'] = [
        {
            'layer': 'Cliente / SSR',
            'technology': 'Nuxt 3, Vue 3, Tailwind',
            'rationale': 'SSR y buen SEO para catálogo y checkout; ecosistema alineado con el panel admin.',
        },
        {
            'layer': 'API',
            'technology': 'Django 5 + DRF',
            'rationale': 'ORM maduro, permisos, integración con pasarelas y tareas asíncronas (Huey).',
        },
        {
            'layer': 'Datos',
            'technology': 'MySQL 8, Redis',
            'rationale': 'Transacciones ACID para pedidos; caché de sesión y colas.',
        },
        {
            'layer': 'Infra',
            'technology': 'VPS + Nginx + Gunicorn',
            'rationale': 'Despliegue controlado; mismos patrones que el resto de productos ProjectApp.',
        },
    ]

    d['architecture'] = {
        'summary': (
            'Monolito modular en Django para dominio de negocio (pedidos, catálogo, usuarios) '
            'y frontend desacoplado que consume API REST. Pasarela Wompi en servidor; webhooks '
            'idempotentes para confirmación de pago.'
        ),
        'patterns': [
            {
                'component': 'Checkout',
                'pattern': 'Saga ligera + outbox',
                'description': 'Orden en estado pendiente hasta confirmación de pago; reintentos seguros.',
            },
            {
                'component': 'Catálogo',
                'pattern': 'CQRS liviano',
                'description': 'Lecturas optimizadas con índices; escrituras en transacción corta.',
            },
            {
                'component': 'Admin',
                'pattern': 'RBAC por rol',
                'description': 'Staff vs operador de tienda; permisos a nivel de vista y acción.',
            },
        ],
        'diagramNote': 'Diagrama C4 contenedor disponible en Confluence del proyecto (enlace interno).',
    }

    d['dataModel'] = {
        'summary': 'Entidades centrales: usuarios, productos, variantes, pedidos, líneas de pedido, pagos.',
        'relationships': (
            'Usuario 1—N Pedidos. Pedido 1—N Líneas. Producto 1—N Variantes. '
            'Pedido 1—1 Pago (referencia Wompi).'
        ),
        'entities': [
            {
                'name': 'Product',
                'description': 'SKU, precio base, impuestos, stock lógico.',
                'keyFields': 'id, slug, base_price_cents, is_active',
            },
            {
                'name': 'Order',
                'description': 'Estado de flujo checkout → pagado → enviado.',
                'keyFields': 'id, user_id, status, total_cents, wompi_tx_id',
            },
        ],
    }

    d['growthReadiness'] = {
        'summary': (
            'La solución se plantea para crecer en tráfico, catálogo y operación sin rediseño completo: '
            'capas desacopladas, datos indexados y despliegue que admite réplicas y colas cuando el negocio lo exija.'
        ),
        'strategies': [
            {
                'dimension': 'Tráfico y frontend',
                'preparation': 'SSR y assets estáticos cacheables; CDN preparado para el mismo origen.',
                'evolution': 'Aumentar workers Gunicorn y cache Redis; escalar VPS o pasar a balanceador cuando supere ~5k visitas/día sostenidas.',
            },
            {
                'dimension': 'Datos y pedidos',
                'preparation': 'Índices en consultas calientes; pedidos y líneas en tablas particionables por fecha si el volumen crece.',
                'evolution': 'Read replicas MySQL o extracción de reportes a réplica; revisión de retención de logs.',
            },
            {
                'dimension': 'Integraciones y colas',
                'preparation': 'Webhooks idempotentes y reintentos en cola (Huey); límites de tasa documentados.',
                'evolution': 'Añadir workers dedicados o broker externo si la cola supera umbral acordado con el cliente.',
            },
        ],
    }

    d['epics'] = [
        {
            'epicKey': 'storefront',
            'title': 'Tienda pública',
            'description': 'Todo lo que el cliente final ve y usa para explorar productos y completar su compra en línea.',
            'requirements': [
                {
                    'flowKey': 'flow-catalog-filters',
                    'title': 'Explorar productos con filtros',
                    'description': 'El visitante puede buscar y filtrar productos por categoría, rango de precio y disponibilidad.',
                    'configuration': 'Índices en category_id y price_cents.',
                    'usageFlow': 'Usuario abre catálogo → aplica filtros → ve resultados.',
                    'priority': 'high',
                },
                {
                    'flowKey': 'flow-checkout-wompi',
                    'title': 'Pago en línea con tarjeta o PSE',
                    'description': 'El comprador puede pagar su pedido de forma segura con tarjeta de crédito, débito o transferencia PSE.',
                    'configuration': 'Claves sandbox/prod por entorno; firma de webhook verificada.',
                    'usageFlow': 'Carrito → datos envío → pasarela de pago → confirmación del pedido.',
                    'priority': 'critical',
                },
            ],
        },
        {
            'epicKey': 'admin-ops',
            'title': 'Panel administrativo',
            'description': 'Herramientas internas para que el equipo gestione productos, pedidos y usuarios del negocio.',
            'requirements': [
                {
                    'flowKey': 'flow-order-management',
                    'title': 'Administrar pedidos',
                    'description': 'El operador puede ver todos los pedidos, revisar su detalle, actualizar el estado y agregar notas internas.',
                    'configuration': 'Roles: staff_full, store_operator.',
                    'usageFlow': 'Operador abre pedido → actualiza estado → cliente recibe email de notificación.',
                    'priority': 'medium',
                },
            ],
        },
    ]

    d['apiSummary'] = (
        'API REST versionada bajo /api/v1/. Autenticación JWT para panel; sesión/CSRF para flujos '
        'admin legacy. Rate limiting en login y checkout.'
    )
    d['apiDomains'] = [
        {'domain': 'Catalog', 'summary': 'GET productos, categorías, búsqueda.'},
        {'domain': 'Orders', 'summary': 'Creación de pedido, consulta de estado, webhooks internos.'},
        {'domain': 'Auth', 'summary': 'Registro, login, refresh token.'},
    ]

    d['integrations'] = {
        'included': [
            {
                'service': 'Pasarela de pagos',
                'provider': 'Wompi',
                'connection': 'REST + webhooks HTTPS',
                'dataExchange': 'Monto, referencia, estado de transacción',
                'accountOwner': 'Cliente (cuenta Wompi propia)',
            },
            {
                'service': 'Email transaccional',
                'provider': 'SMTP / proveedor configurado',
                'connection': 'Envío asíncrono vía cola',
                'dataExchange': 'Plantillas de pedido confirmado, recuperación de contraseña',
                'accountOwner': 'ProjectApp ops',
            },
        ],
        'excluded': [
            {
                'service': 'ERP SAP',
                'reason': 'Fuera de alcance MVP',
                'availability': 'Fase 2 vía API genérica o CSV',
            },
        ],
        'notes': (
            'Las integraciones incluidas están alineadas con la calculadora de la propuesta.\n'
            'Cualquier nueva pasarela requiere spike de 2–3 días.\n'
            'Webhooks deben usar secret rotado por entorno.'
        ),
    }

    d['environments'] = [
        {
            'name': 'Development',
            'purpose': 'Desarrollo local y pruebas de integración',
            'url': 'https://dev.techstartup.example',
            'database': 'MySQL (dump anonimizado)',
            'whoAccesses': 'Equipo ProjectApp',
        },
        {
            'name': 'Staging',
            'purpose': 'UAT y demos con cliente',
            'url': 'https://staging.techstartup.example',
            'database': 'MySQL (datos de prueba)',
            'whoAccesses': 'Cliente + ProjectApp',
        },
        {
            'name': 'Production',
            'purpose': 'Tráfico real',
            'url': 'https://tienda.techstartup.example',
            'database': 'MySQL managed + backups diarios',
            'whoAccesses': 'Solo despliegue automatizado + break-glass',
        },
    ]
    d['environmentsNote'] = 'Promoción dev → staging → prod con pipeline CI; sin cambios directos en prod. Servidor estándar: VPS con 4 CPUs y 8 GB RAM.'

    d['security'] = [
        {
            'aspect': 'Transporte',
            'implementation': 'TLS 1.2+ en todos los entornos públicos; HSTS en producción.',
        },
        {
            'aspect': 'Datos sensibles',
            'implementation': 'Sin PAN en logs; tokens de pago solo en proveedor; PII minimizada en analytics.',
        },
        {
            'aspect': 'Autenticación',
            'implementation': 'JWT de corta vida + refresh rotado; bloqueo progresivo tras intentos fallidos.',
        },
    ]

    d['performanceQuality'] = {
        'metrics': [
            {
                'metric': 'TTFB catálogo',
                'target': '< 400 ms p95',
                'howMeasured': 'APM + pruebas k6 en staging',
            },
            {
                'metric': 'Conversión checkout',
                'target': 'Sin regresión > 5% vs baseline',
                'howMeasured': 'Eventos analíticos agregados semanalmente',
            },
        ],
        'practices': [
            {
                'strategy': 'Caching',
                'description': 'Cache de lectura para taxonomías y listados calientes; invalidación por tag.',
            },
            {
                'strategy': 'Observabilidad',
                'description': 'Logs estructurados, trazas en errores 5xx, alertas en tasa de fallo de pago.',
            },
        ],
    }

    d['backupsNote'] = (
        'Backup semanal automatizado de base de datos y archivos multimedia, '
        'con retención de 4 semanas. Restore probado trimestralmente. '
        'Sin almacenamiento externo.'
    )

    d['quality'] = {
        'dimensions': [
            {
                'dimension': 'Funcional',
                'evaluates': 'Flujos críticos de compra y admin',
                'standard': 'Criterios de aceptación por historia + pruebas manuales en staging',
            },
            {
                'dimension': 'Regresión',
                'evaluates': 'Módulos tocados en cada release',
                'standard': 'Suite automatizada en CI + smoke post-deploy',
            },
        ],
        'testTypes': [
            {
                'type': 'API',
                'validates': 'Contratos y códigos HTTP',
                'tool': 'pytest + DRF client',
                'whenRun': 'Cada push en rama principal',
            },
            {
                'type': 'E2E',
                'validates': 'Checkout feliz y cancelación',
                'tool': 'Playwright',
                'whenRun': 'Nightly en staging',
            },
        ],
        'criticalFlowsNote': 'Checkout, webhook de pago y creación de pedido son flujos bloqueantes para release.',
    }

    d['decisions'] = [
        {
            'decision': 'Monolito Django vs microservicios',
            'alternative': 'Microservicios desde día 1',
            'reason': 'Menor costo operativo y tiempo al mercado para el tamaño del MVP acordado.',
        },
        {
            'decision': 'Nuxt SSR',
            'alternative': 'SPA pura',
            'reason': 'Mejor SEO y primera carga para catálogo e-commerce B2C.',
        },
    ]

    return d


DEMO_TECHNICAL_DOCUMENT_JSON = _build_demo_technical_document_json()
