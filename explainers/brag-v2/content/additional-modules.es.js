window.EXPLAINER_CONTENT = {
  "language": "es",
  "total_modules": 24,
  "categories": [
    {
      "slug": "commerce-transactions",
      "name": "Comercio y transacciones",
      "modules": [
        {
          "slug": "electronic-invoicing",
          "icon": "🧾",
          "name": "Facturación electrónica e integración DIAN",
          "summary": "Emite y sigue comprobantes fiscales desde los mismos flujos donde ocurre la venta.",
          "what_is": "Una conexión entre la plataforma y un proveedor de facturación electrónica autorizado para generar facturas, notas crédito, notas débito y documentos soporte sin volver a registrar la operación.",
          "purpose": "Mantener la operación comercial y el cumplimiento fiscal sincronizados, con trazabilidad del estado de cada comprobante ante la DIAN.",
          "problems_solved": [
            "Evita digitar la misma venta en dos sistemas.",
            "Reduce errores de impuestos, clientes y productos.",
            "Hace visible si un comprobante fue aceptado, rechazado o sigue en proceso."
          ],
          "integrations": [
            "Siigo, Alegra u otro proveedor con API documentada.",
            "Pedidos, pagos, clientes, productos e impuestos de la plataforma.",
            "Correo y alertas internas para estados fiscales."
          ],
          "implementation_requirements": [
            "Cuenta activa con el proveedor de facturación.",
            "Resoluciones, numeración, impuestos y datos fiscales definidos.",
            "Reglas claras sobre cuándo facturar, anular o emitir una nota."
          ]
        },
        {
          "slug": "regional-payment-gateways",
          "icon": "🇨🇴",
          "name": "Pasarelas de pago regionales",
          "summary": "Recibe pagos en Colombia con los medios que tus clientes ya usan.",
          "what_is": "Una integración de checkout y confirmación de pagos con proveedores colombianos como Wompi, PayU o ePayco, incluyendo tarjetas, PSE y medios alternativos según el proveedor.",
          "purpose": "Cobrar dentro del flujo digital y actualizar automáticamente pedidos, reservas, suscripciones o cuentas cuando el dinero se confirma.",
          "problems_solved": [
            "Elimina confirmaciones manuales por comprobante o captura.",
            "Mantiene pagos pendientes, aprobados y rechazados en un solo estado confiable.",
            "Evita dobles cobros o dobles confirmaciones por reintentos del proveedor."
          ],
          "integrations": [
            "Wompi, PayU o ePayco.",
            "Carrito, reservas, facturación, inventario o membresías.",
            "Webhooks, conciliación y notificaciones de pago."
          ],
          "implementation_requirements": [
            "Cuenta comercial aprobada en la pasarela.",
            "Métodos de pago y monedas del alcance definidos.",
            "Reglas para pendientes, vencimientos, reembolsos y conciliación."
          ]
        },
        {
          "slug": "international-payment-gateways",
          "icon": "🌎",
          "name": "Pasarelas de pago internacionales",
          "summary": "Cobra a clientes de otros países con tarjetas, divisas y métodos globales.",
          "what_is": "Una integración con Stripe, PayPal u otro proveedor global para pagos únicos o recurrentes, autenticación bancaria y confirmación segura del lado del servidor.",
          "purpose": "Abrir la venta a otros mercados sin construir infraestructura financiera propia y conservar el estado del cobro dentro de la plataforma.",
          "problems_solved": [
            "Permite cobrar en mercados y monedas diferentes.",
            "Maneja autenticación 3D Secure y pagos que requieren pasos adicionales.",
            "Centraliza reembolsos, disputas y suscripciones."
          ],
          "integrations": [
            "Stripe, PayPal u otra pasarela global con API.",
            "Checkout, planes, suscripciones y acceso a servicios.",
            "Facturación, correo y analítica de conversión."
          ],
          "implementation_requirements": [
            "Cuenta habilitada en los países y monedas objetivo.",
            "Política comercial de cobros, devoluciones y contracargos.",
            "Definición de impuestos, precios y conversión de moneda fuera de la pasarela."
          ]
        },
        {
          "slug": "gift-cards",
          "icon": "🎁",
          "name": "Tarjetas de regalo y saldos",
          "summary": "Vende crédito canjeable y conviértelo en una nueva vía de compra y recomendación.",
          "what_is": "Un módulo para emitir códigos o tarjetas con saldo, fecha de vigencia y reglas de uso, que el destinatario puede aplicar total o parcialmente en una compra.",
          "purpose": "Facilitar regalos, campañas, compensaciones y crédito comercial sin depender de cupones de un solo uso.",
          "problems_solved": [
            "Permite que una persona compre para otra sin elegir el producto final.",
            "Controla saldos parciales y evita canjes duplicados.",
            "Da trazabilidad a emisión, entrega, uso, vencimiento y anulación."
          ],
          "integrations": [
            "Checkout, catálogo, pedidos y cuentas de cliente.",
            "Pasarelas de pago y correo de entrega.",
            "Reportes de saldos emitidos, usados y pendientes."
          ],
          "implementation_requirements": [
            "Reglas de vigencia, acumulación, devolución y transferibilidad.",
            "Diseño y mensaje de la tarjeta.",
            "Tratamiento contable y fiscal del saldo pendiente."
          ]
        },
        {
          "slug": "scheduling-bookings",
          "icon": "📅",
          "name": "Agenda, reservas y disponibilidad",
          "summary": "Publica disponibilidad y permite reservar, reprogramar o cancelar sin coordinación manual.",
          "what_is": "Un módulo de agenda que combina servicios, recursos, horarios y reglas de disponibilidad para confirmar reservas sin cruces.",
          "purpose": "Convertir la coordinación de citas o cupos en un flujo autónomo, medible y conectado con la operación.",
          "problems_solved": [
            "Elimina intercambios repetidos para encontrar una hora disponible.",
            "Evita dobles reservas y respeta duración, capacidad y tiempos de preparación.",
            "Reduce ausencias con confirmaciones, recordatorios y reglas de cancelación."
          ],
          "integrations": [
            "Google Calendar, Outlook, videollamadas o calendarios del equipo.",
            "Clientes, servicios, sedes, recursos y pasarelas de pago.",
            "Correo, WhatsApp y notificaciones para confirmaciones y recordatorios."
          ],
          "implementation_requirements": [
            "Horarios, zonas horarias, duraciones, capacidad y tiempos de margen definidos.",
            "Políticas de pago, reprogramación, cancelación y ausencia acordadas.",
            "Cuentas y permisos de los calendarios o proveedores que se integrarán."
          ]
        },
        {
          "slug": "memberships-subscriptions",
          "icon": "🔁",
          "name": "Membresías y suscripciones",
          "summary": "Administra planes recurrentes, renovaciones y acceso según el estado real de cada suscripción.",
          "what_is": "Un módulo para vender y operar planes periódicos con ciclos, pruebas, cobros, renovaciones, pausas, cancelaciones y beneficios asociados.",
          "purpose": "Sostener ingresos recurrentes y mantener sincronizados el pago, la vigencia y los permisos que recibe cada miembro.",
          "problems_solved": [
            "Evita controlar renovaciones y vencimientos de forma manual.",
            "Impide que el acceso quede activo cuando el pago falló o la membresía terminó.",
            "Hace visibles cancelaciones, reintentos, retención y motivos de pérdida."
          ],
          "integrations": [
            "Pasarelas de pago, facturación y conciliación.",
            "Cuentas, roles, contenido, servicios o beneficios de la plataforma.",
            "Correo, notificaciones y analítica de renovaciones y cancelaciones."
          ],
          "implementation_requirements": [
            "Planes, periodicidades, pruebas, precios y reglas de prorrateo definidos.",
            "Reglas de acceso, pausa, cancelación, cobro fallido y reactivación.",
            "Tratamiento fiscal, cuenta de recaudo y comunicaciones del ciclo acordados."
          ]
        }
      ]
    },
    {
      "slug": "identity-access",
      "name": "Identidad y acceso",
      "modules": [
        {
          "slug": "biometric-verification",
          "icon": "🪪",
          "name": "Verificación y validación biométrica",
          "summary": "Confirma que la persona y su documento coinciden antes de habilitar una operación sensible.",
          "what_is": "Una integración KYC con un proveedor especializado que combina lectura del documento, comparación facial y prueba de vida para devolver una decisión verificable.",
          "purpose": "Reducir suplantación y fraude en registros, firmas, desembolsos, accesos o cambios críticos sin convertir el proceso en una revisión manual.",
          "problems_solved": [
            "Detecta documentos inconsistentes o rostros que no coinciden.",
            "Distingue una persona presente de una foto o grabación.",
            "Conserva evidencia y resultado para auditoría según la política acordada."
          ],
          "integrations": [
            "Proveedor biométrico/KYC elegido por el cliente.",
            "Registro, login reforzado, firma o aprobación de operaciones.",
            "Alertas y revisión manual para casos inconclusos."
          ],
          "implementation_requirements": [
            "Contrato y cuenta con el proveedor, facturados por éste al cliente.",
            "Base legal, consentimiento y política de retención de datos biométricos.",
            "Criterios de aprobación, rechazo y revisión manual."
          ]
        },
        {
          "slug": "customer-self-service",
          "icon": "🧑‍💻",
          "name": "Portal de autoservicio para clientes",
          "summary": "Reúne solicitudes, documentos, pagos y estados en un espacio seguro para cada cliente.",
          "what_is": "Un área autenticada donde cada cliente consulta su información, realiza solicitudes, descarga documentos y sigue procesos sin depender de atención manual.",
          "purpose": "Dar autonomía al cliente y ofrecer una fuente única y segura para la información que necesita durante la relación comercial.",
          "problems_solved": [
            "Evita repartir solicitudes y archivos entre correos, chats y carpetas aisladas.",
            "Reduce preguntas repetidas sobre estados, saldos o próximos pasos.",
            "Entrega documentos y datos sensibles sólo a usuarios autorizados."
          ],
          "integrations": [
            "Identidad, roles, recuperación de acceso y verificación de correo.",
            "CRM, pedidos, soporte, documentos, proyectos y pagos.",
            "Correo, notificaciones y registro de actividad del cliente."
          ],
          "implementation_requirements": [
            "Audiencias, permisos y responsabilidades de cada tipo de usuario definidos.",
            "Procesos, estados y datos que el cliente podrá consultar o modificar.",
            "Políticas de privacidad, retención, soporte y cierre de cuentas."
          ]
        }
      ]
    },
    {
      "slug": "marketing-acquisition",
      "name": "Marketing y adquisición",
      "modules": [
        {
          "slug": "landing-page",
          "icon": "🚀",
          "name": "Landing page",
          "summary": "Dale a campañas y visitantes un punto de llegada claro, medible y orientado a una acción.",
          "what_is": "Una página pública enfocada en una oferta, audiencia y llamado a la acción. Presenta el valor esencial, responde objeciones y conduce al visitante hacia contacto, registro, compra o agenda.",
          "purpose": "Crear el punto de partida que una plataforma necesita para recibir usuarios, explicar por qué entrar y medir de dónde vienen las oportunidades.",
          "problems_solved": [
            "Evita enviar campañas a una página genérica o sin contexto.",
            "Concentra el mensaje y la acción sin distraer al visitante.",
            "Permite medir visitas, fuentes, formularios y conversiones."
          ],
          "integrations": [
            "Formularios, CRM, agenda, WhatsApp o checkout.",
            "Analítica, píxeles publicitarios y seguimiento de conversiones.",
            "Chat, correo transaccional y dominio de la marca."
          ],
          "implementation_requirements": [
            "Identidad visual, textos, oferta y llamado a la acción definidos.",
            "Dominio o subdominio y destino de los datos del formulario.",
            "Objetivo de conversión, fuentes de tráfico y medición acordados."
          ]
        },
        {
          "slug": "corporate-branding",
          "icon": "🎨",
          "name": "Identidad visual e imagen corporativa",
          "summary": "Haz que pantallas, correos y documentos se reconozcan como una sola marca.",
          "what_is": "La aplicación consistente de logo, color, tipografía, tono y recursos visuales en el sistema y en cada pieza que éste genera o comparte.",
          "purpose": "Construir confianza y continuidad de marca desde el primer acceso hasta un correo, PDF, error o enlace compartido.",
          "problems_solved": [
            "Reemplaza pantallas y mensajes genéricos.",
            "Evita que cada canal use estilos diferentes.",
            "Mejora reconocimiento y percepción profesional."
          ],
          "integrations": [
            "Interfaz, login, estados vacíos y páginas de error.",
            "Correos, PDFs, exportaciones y tarjetas de redes sociales.",
            "Metadatos de buscadores y asistentes de IA."
          ],
          "implementation_requirements": [
            "Logo en formatos útiles, paleta y tipografías licenciadas.",
            "Guía de tono y ejemplos aprobados.",
            "Responsable de marca para validar aplicaciones."
          ]
        },
        {
          "slug": "conversion-tracking",
          "icon": "📡",
          "name": "Seguimiento de conversiones para Meta y Google Ads",
          "summary": "Devuelve a las campañas señales confiables sobre las acciones que sí producen negocio.",
          "what_is": "Una medición server-side que reporta eventos valiosos a Meta Conversions API y Google Enhanced Conversions, complementando el seguimiento del navegador.",
          "purpose": "Mejorar atribución y optimización publicitaria aun cuando cookies, bloqueadores o restricciones del dispositivo reducen la señal del navegador.",
          "problems_solved": [
            "Recupera conversiones que el píxel no observa.",
            "Evita contar dos veces el mismo evento.",
            "Relaciona cada evento con valor y resultado operativo."
          ],
          "integrations": [
            "Meta Conversions API y Google Ads.",
            "Formularios, checkout, agenda, propuestas o eventos propios.",
            "Panel de diagnóstico y analítica."
          ],
          "implementation_requirements": [
            "Cuentas publicitarias y permisos técnicos.",
            "Mapa de eventos, valores y consentimientos.",
            "Política de privacidad y datos de matching permitidos."
          ]
        },
        {
          "slug": "email-marketing",
          "icon": "✉️",
          "name": "Email marketing y automatizaciones",
          "summary": "Acompaña cada oportunidad con mensajes oportunos según su comportamiento y etapa.",
          "what_is": "Un conjunto de listas, segmentos, campañas y secuencias automáticas conectado con los eventos reales de la plataforma.",
          "purpose": "Mantener conversaciones relevantes a escala sin depender de envíos manuales ni tratar igual a todos los contactos.",
          "problems_solved": [
            "Evita seguimientos olvidados o enviados fuera de contexto.",
            "Segmenta por interés, etapa y actividad.",
            "Mide entregas, aperturas, clics y bajas."
          ],
          "integrations": [
            "Brevo, Mailchimp, SendGrid u otro proveedor.",
            "CRM, formularios, compras y actividad del producto.",
            "Plantillas, dominio de envío y analítica."
          ],
          "implementation_requirements": [
            "Base de contactos con consentimiento y origen trazable.",
            "Dominio autenticado y proveedor configurado.",
            "Segmentos, frecuencia, contenido y reglas de baja."
          ]
        },
        {
          "slug": "qr-generator",
          "icon": "▦",
          "name": "Generador y gestión de códigos QR",
          "summary": "Conecta piezas físicas con destinos digitales medibles y actualizables.",
          "what_is": "Un módulo para crear, personalizar, organizar y seguir códigos QR estáticos o dinámicos desde el panel.",
          "purpose": "Llevar usuarios desde impresos, espacios o productos a una acción digital sin perder control del destino.",
          "problems_solved": [
            "Permite cambiar el destino sin reimprimir un QR dinámico.",
            "Evita códigos dispersos sin dueño ni contexto.",
            "Mide escaneos y campañas."
          ],
          "integrations": [
            "Landing pages, perfiles, formularios, documentos o pagos.",
            "Analítica y parámetros de campaña.",
            "Descarga PNG/SVG para piezas impresas."
          ],
          "implementation_requirements": [
            "Inventario de usos y destinos.",
            "Reglas de marca, tamaño y contraste de impresión.",
            "Dominio estable para enlaces dinámicos."
          ]
        },
        {
          "slug": "content-generator",
          "icon": "✍️",
          "name": "Generación y calendario de contenido",
          "summary": "Planea, redacta y coordina publicaciones sin perder la voz de la marca.",
          "what_is": "Un espacio asistido para producir borradores, organizar ideas y gestionar un calendario editorial mensual o semanal con estados de aprobación.",
          "purpose": "Convertir objetivos de comunicación en una cadencia visible de contenidos listos para revisar y publicar.",
          "problems_solved": [
            "Reduce el tiempo de pasar de una idea al primer borrador.",
            "Evita duplicar temas o perder fechas.",
            "Mantiene tono, formato y llamados a la acción consistentes."
          ],
          "integrations": [
            "Blog, LinkedIn, email o redes mediante proveedor.",
            "Banco de temas, productos y guía de marca.",
            "Flujo de revisión, aprobación y programación."
          ],
          "implementation_requirements": [
            "Objetivos, audiencias y pilares de contenido.",
            "Guía de tono y ejemplos permitidos/prohibidos.",
            "Responsables de revisión y canales de publicación."
          ]
        },
        {
          "slug": "sales-crm-pipeline",
          "icon": "🎯",
          "name": "CRM y embudo comercial",
          "summary": "Centraliza prospectos, oportunidades y próximos pasos desde el primer contacto hasta el cierre.",
          "what_is": "Un espacio comercial que organiza contactos, oportunidades, etapas, responsables, actividad y tareas de seguimiento en un solo embudo.",
          "purpose": "Dar continuidad a cada oportunidad y hacer visible qué debe ocurrir después, quién responde y qué tan cerca está el cierre.",
          "problems_solved": [
            "Evita que prospectos y conversaciones queden dispersos entre hojas, chats y correos.",
            "Reduce seguimientos olvidados al asignar responsables, fechas y próximos pasos.",
            "Hace visible el estado del embudo y permite proyectar oportunidades con información real."
          ],
          "integrations": [
            "Formularios, correo, WhatsApp, agenda y fuentes publicitarias.",
            "Clientes, propuestas, cotizaciones y tareas de la plataforma.",
            "Analítica comercial y reportes de conversión por etapa y origen."
          ],
          "implementation_requirements": [
            "Etapas, responsables, criterios de avance y tiempos de seguimiento definidos.",
            "Campos obligatorios y fuentes de datos o importación acordados.",
            "Permisos, privacidad y política de conservación del historial comercial."
          ]
        },
        {
          "slug": "loyalty-referrals",
          "icon": "⭐",
          "name": "Fidelización y referidos",
          "summary": "Reconoce compras y recomendaciones con puntos, niveles o beneficios medibles.",
          "what_is": "Un programa que registra acciones verificadas, asigna recompensas y relaciona cada referido con su origen, conversión y beneficio.",
          "purpose": "Aumentar recurrencia y recomendación mediante reglas transparentes que el cliente puede consultar y usar.",
          "problems_solved": [
            "Evita que las compras recurrentes no reciban reconocimiento ni incentivo.",
            "Permite atribuir referidos y recompensarlos sin validación manual.",
            "Centraliza saldos, niveles, vencimientos, canjes y resultados de campaña."
          ],
          "integrations": [
            "Clientes, pedidos, pagos y acciones verificadas de la plataforma.",
            "Cupones, campañas, email y notificaciones.",
            "Analítica de recurrencia, referidos, canjes y prevención de fraude."
          ],
          "implementation_requirements": [
            "Reglas de acumulación, niveles, canje, vencimiento y exclusiones definidas.",
            "Tratamiento contable y fiscal de puntos, saldos y beneficios.",
            "Controles de abuso, privacidad y responsables de atención de reclamos."
          ]
        },
        {
          "slug": "audiovisual-experiences",
          "icon": "🎬",
          "name": "Experiencias audiovisuales",
          "summary": "Convierte lo que cuesta explicar en una pieza audiovisual breve que se entiende en una sola pasada.",
          "what_is": "Una producción de piezas audiovisuales cortas, hechas a la medida de la marca, que muestran en movimiento una vista, una funcionalidad o un mensaje que en texto queda largo o pasa desapercibido. Es un trabajo colaborativo que se arma con recursos propios de la marca.",
          "purpose": "Lograr que quien entra entienda de un vistazo de qué trata lo que está viendo, sin leer todo ni pedir explicaciones, y se lleve una impresión de marca cuidada.",
          "problems_solved": [
            "Evita que una vista con mucho contenido se abandone antes de entender qué ofrece.",
            "Reduce las explicaciones repetidas sobre qué hace cada parte de la plataforma.",
            "Convierte una funcionalidad difícil de contar por escrito en algo que se entiende viéndolo."
          ],
          "integrations": [
            "Vistas públicas, propuestas, landing pages y páginas de producto.",
            "Redes sociales, campañas publicitarias, correo y WhatsApp.",
            "Presentaciones comerciales y material de bienvenida para nuevos usuarios."
          ],
          "implementation_requirements": [
            "Identidad de marca disponible: logo, paleta de colores y tipografías.",
            "Material propio existente: fotos, videos, capturas o piezas anteriores.",
            "Mensajes clave definidos: qué resaltar, en qué tono y con qué textos base.",
            "Acceso a la plataforma o a un entorno de demostración para grabar el producto real.",
            "Paquete de trabajo elegido: los paquetes iniciales son de 4, 8 y 16 recursos audiovisuales.",
            "Paquetes disponibles consultados con el representante comercial antes de empezar."
          ]
        }
      ]
    },
    {
      "slug": "user-experience",
      "name": "Experiencia de usuario",
      "modules": [
        {
          "slug": "progressive-web-app",
          "icon": "📱",
          "name": "Aplicación móvil instalable (PWA)",
          "summary": "Permite instalar la plataforma desde el navegador y conservar funciones útiles con conexión limitada.",
          "what_is": "Una evolución de la web con manifiesto, service worker, iconos y estrategias de caché para comportarse como una aplicación instalada.",
          "purpose": "Mejorar recurrencia, acceso rápido y resiliencia sin publicar aplicaciones separadas en cada tienda.",
          "problems_solved": [
            "Da acceso desde la pantalla de inicio.",
            "Mantiene una experiencia clara cuando la red falla.",
            "Actualiza la aplicación sin intervención del usuario."
          ],
          "integrations": [
            "Autenticación y rutas principales de la plataforma.",
            "Caché, sincronización en segundo plano y notificaciones push.",
            "Analítica de instalación y uso."
          ],
          "implementation_requirements": [
            "Definir qué funciona offline y qué no.",
            "Iconos, nombre corto y colores de instalación.",
            "Política de actualizaciones, permisos y notificaciones."
          ]
        },
        {
          "slug": "internationalization",
          "icon": "🌐",
          "name": "Plataforma multiidioma",
          "summary": "Entrega interfaz y contenido en el idioma adecuado para cada audiencia.",
          "what_is": "Una arquitectura de internacionalización para traducir interfaz, contenido, correos, fechas, números y rutas sin duplicar la aplicación.",
          "purpose": "Atender mercados y equipos diversos con una experiencia coherente y preparada para sumar idiomas.",
          "problems_solved": [
            "Evita textos mezclados o traducciones incrustadas en código.",
            "Presenta fechas, monedas y formatos locales correctamente.",
            "Permite administrar traducciones del contenido."
          ],
          "integrations": [
            "Navegación, contenido, formularios, PDFs y correo.",
            "SEO con rutas y alternates por idioma.",
            "Proveedor o flujo humano de traducción."
          ],
          "implementation_requirements": [
            "Idiomas, regiones y contenido traducible del alcance.",
            "Responsable de traducción y aprobación.",
            "Reglas para idioma por usuario, URL y fallback."
          ]
        },
        {
          "slug": "live-chat",
          "icon": "💬",
          "name": "Chat en vivo y atención",
          "summary": "Permite resolver dudas dentro de la experiencia sin obligar al usuario a cambiar de canal.",
          "what_is": "Un canal de conversación integrado con disponibilidad, historial, datos de contexto y escalamiento a una persona o equipo.",
          "purpose": "Acompañar decisiones, soporte y ventas en el momento en que aparece una duda.",
          "problems_solved": [
            "Reduce abandono por preguntas sin respuesta.",
            "Conserva contexto de página, usuario y conversación.",
            "Ordena horarios, responsables y seguimiento."
          ],
          "integrations": [
            "Intercom, Crisp, Zendesk u otra solución.",
            "CRM, usuarios, tickets y base de conocimiento.",
            "Notificaciones por correo o mensajería."
          ],
          "implementation_requirements": [
            "Herramienta o modelo de atención seleccionado.",
            "Horarios, mensajes de ausencia y responsables.",
            "Política de datos y tiempos de respuesta."
          ]
        },
        {
          "slug": "dark-mode",
          "icon": "🌙",
          "name": "Modo oscuro",
          "summary": "Ofrece una apariencia alternativa legible y consistente para ambientes de poca luz.",
          "what_is": "Un tema completo que adapta superficies, texto, bordes, gráficos, imágenes y estados a una paleta oscura accesible.",
          "purpose": "Dar control visual al usuario y mantener comodidad en sesiones largas o entornos oscuros.",
          "problems_solved": [
            "Evita invertir colores de forma incompleta o ilegible.",
            "Conserva contraste y jerarquía visual.",
            "Recuerda la preferencia por usuario o dispositivo."
          ],
          "integrations": [
            "Sistema de diseño, gráficos, editor y contenido multimedia.",
            "Preferencia del sistema operativo y perfil de usuario.",
            "Correos o PDFs sólo cuando el formato lo admite."
          ],
          "implementation_requirements": [
            "Paleta oscura y contraste validados.",
            "Inventario de componentes, gráficos e imágenes.",
            "Regla de preferencia automática o manual."
          ]
        }
      ]
    },
    {
      "slug": "intelligence-tracking",
      "name": "Inteligencia y seguimiento",
      "modules": [
        {
          "slug": "artificial-intelligence",
          "icon": "🤖",
          "name": "Integración y automatización con IA",
          "summary": "Aplica modelos de IA a una tarea concreta con datos, límites y revisión definidos.",
          "what_is": "Una capacidad conectada a modelos de lenguaje, visión o clasificación para asistir, generar, extraer, buscar o ejecutar pasos dentro de un proceso real.",
          "purpose": "Reducir trabajo repetitivo o ampliar la capacidad de decisión sin presentar la IA como una función aislada del negocio.",
          "problems_solved": [
            "Acelera borradores, clasificación y extracción.",
            "Permite consultar información con lenguaje natural.",
            "Automatiza pasos con aprobación humana donde importa."
          ],
          "integrations": [
            "Claude, OpenAI u otro proveedor adecuado al caso.",
            "Datos, documentos, búsqueda y flujos internos.",
            "Auditoría, límites de costo y revisión humana."
          ],
          "implementation_requirements": [
            "Un caso de uso y criterio de éxito concretos.",
            "Fuentes de datos autorizadas y ejemplos de calidad.",
            "Política de privacidad, revisión, errores y costos del proveedor."
          ]
        },
        {
          "slug": "behavior-tracking",
          "icon": "🧭",
          "name": "Seguimiento de comportamiento y producto",
          "summary": "Entiende qué hacen los usuarios, dónde abandonan y qué caminos sí completan.",
          "what_is": "Una instrumentación de eventos, embudos y recorridos que observa interacciones relevantes sin depender únicamente de visitas de página.",
          "purpose": "Convertir el uso real del producto en evidencia para priorizar mejoras, onboarding y conversión.",
          "problems_solved": [
            "Detecta pasos con abandono o fricción.",
            "Compara adopción de funciones y cohortes.",
            "Separa opiniones aisladas de patrones de uso."
          ],
          "integrations": [
            "PostHog, Mixpanel, GA4 u otra plataforma.",
            "Eventos del frontend y resultados del backend.",
            "Dashboards, experimentos y alertas."
          ],
          "implementation_requirements": [
            "Mapa de eventos, propiedades y embudos.",
            "Consentimiento, anonimización y retención.",
            "Responsables de lectura y decisiones periódicas."
          ]
        },
        {
          "slug": "reports-alerts",
          "icon": "📊",
          "name": "Reportes, indicadores y alertas",
          "summary": "Convierte datos operativos en indicadores consultables y señales que llegan a tiempo.",
          "what_is": "Un módulo de tableros, reportes exportables y alertas basadas en condiciones del negocio, con alcance por rol y período.",
          "purpose": "Ayudar a cada responsable a observar resultados, excepciones y tendencias sin revisar registros uno por uno.",
          "problems_solved": [
            "Reduce consolidación manual en hojas de cálculo.",
            "Avisa vencimientos, caídas o umbrales antes de que escalen.",
            "Entrega una definición compartida de cada indicador."
          ],
          "integrations": [
            "Base transaccional y eventos de la plataforma.",
            "Correo, mensajería o notificaciones internas.",
            "PDF, Excel/CSV y herramientas BI cuando aplica."
          ],
          "implementation_requirements": [
            "Indicadores, fórmulas, fuentes y responsables definidos.",
            "Frecuencia, destinatarios y umbrales de alerta.",
            "Permisos y política de exportación de datos."
          ]
        }
      ]
    }
  ],
  "is_shared": false,
  "show_explainer_video": false,
  "canonical_path": "/es-co/additional-modules"
};
