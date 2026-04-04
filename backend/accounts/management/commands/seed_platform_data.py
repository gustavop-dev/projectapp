"""
Seed the platform with demo data for development.

Creates:
  - 1 admin user (admin@projectapp.dev / Admin1234!)
  - 1 onboarded client (maria@techstartup.co / Client1234!)
  - 1 full demo BusinessProposal (all default sections + populated technical_document) for TechStartup
  - 2 demo projects for the client
  - Kanban, change requests, bugs, deliverables, hosting + extra payments (pending / overdue / failed)
  - Collection accounts (titles prefixed [Demo]) for platform QA
  - In-app notifications + requirement/bug comments (titles/content prefixed [Seed])
  - Markdown panel documents (titles prefixed [Seed]) for PDF pipeline tests

Usage:
  python manage.py seed_platform_data
  python manage.py seed_platform_data --flush   # removes previous seed data first
"""

import os
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from accounts.models import (
    BugComment,
    BugReport,
    ChangeRequest,
    ChangeRequestComment,
    DataModelEntity,
    Deliverable,
    HostingSubscription,
    Notification,
    Payment,
    Project,
    ProjectDataModelEntity,
    Requirement,
    RequirementComment,
    UserProfile,
)

User = get_user_model()

ADMIN_EMAIL = 'admin@projectapp.dev'
CLIENT_EMAIL = 'maria@techstartup.co'

# Synthetic notifications / markdown docs; removed on --flush.
SEED_PREFIX = '[Seed]'

ADMIN_PASSWORD = os.environ.get('SEED_ADMIN_PASSWORD', 'Admin1234!')
CLIENT_PASSWORD = os.environ.get('SEED_CLIENT_PASSWORD', 'Client1234!')

EPICS_ECOMMERCE = {
    'AUTH':          'Autenticación y Cuenta',
    'CATALOG':       'Catálogo y Productos',
    'CART':          'Carrito y Checkout',
    'PAYMENTS':      'Pagos y Pedidos',
    'ADMIN':         'Panel de Administración',
    'NOTIFICATIONS': 'Notificaciones',
    'SEO':           'SEO y Performance',
}

EPICS_INVENTORY = {
    'AUTH':      'Autenticación y Roles',
    'INVENTORY': 'Gestión de Inventario',
    'BARCODE':   'Lector de Código de Barras',
    'SYNC':      'Sincronización con ERP',
    'REPORTS':   'Reportes y Analítica',
}

# fmt: off
REQUIREMENTS_ECOMMERCE = [
    # ── DONE (6) ───────────────────────────────────────────────────────────
    {"title": "Diseño de la página principal (landing)", "description": "Hero section con propuesta de valor, carrusel de productos destacados, CTA de registro y sección de categorías.", "configuration": "Visible para todos los usuarios (guests y autenticados).", "flow": "Usuario abre / → ve hero con tagline y CTA → navega carrusel de productos → ve categorías → puede ir a /catalog.", "priority": "high", "status": "done", "epic": "CATALOG"},
    {"title": "Catálogo de productos con filtros", "description": "Grid paginado de productos con filtros por categoría, precio, disponibilidad y ordenamiento.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario navega a /catalog → ve grid de productos → aplica filtros → resultados se actualizan sin recargar → click en producto navega a detalle.", "priority": "high", "status": "done", "epic": "CATALOG"},
    {"title": "Registro de usuario con email y contraseña", "description": "Formulario de registro con nombre, email, contraseña y confirmación. Envía email de bienvenida al registrarse.", "configuration": "Solo usuarios no autenticados.", "flow": "Usuario en /register → completa formulario → el sistema valida → crea cuenta → envía email de bienvenida → redirige a /catalog.", "priority": "critical", "status": "done", "epic": "AUTH"},
    {"title": "Inicio de sesión con email y contraseña", "description": "Formulario de login con email y contraseña, opción de recordar sesión y enlace a recuperación.", "configuration": "Solo usuarios no autenticados.", "flow": "Usuario en /login → ingresa credenciales → el sistema valida → emite sesión/JWT → redirige al catálogo.", "priority": "critical", "status": "done", "epic": "AUTH"},
    {"title": "Vista de detalle de producto", "description": "Página con galería de imágenes, descripción completa, precio, variantes (talla/color), stock disponible y botón Agregar al carrito.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario click en producto → navega a /product/{id} → ve galería, precio, variantes → click 'Agregar al carrito' → producto agregado al estado del carrito.", "priority": "high", "status": "done", "epic": "CATALOG"},
    {"title": "Header con navegación y estado del carrito", "description": "Barra de navegación con logo, enlaces a secciones, ícono de carrito con contador de ítems y menú de usuario.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario ve header → links: Inicio, Catálogo, Nosotros → ícono de carrito con badge numérico → click carrito → abre sidebar/modal.", "priority": "high", "status": "done", "epic": "CATALOG"},

    # ── IN REVIEW (4) ──────────────────────────────────────────────────────
    {"title": "Carrito de compras con persistencia", "description": "Carrito persistente en localStorage con lista de productos, cantidades, subtotales y botón de ir al checkout.", "configuration": "Todos los usuarios (carrito anónimo persistido; al autenticarse se fusiona).", "flow": "Usuario agrega productos → click en ícono carrito → ve lista de ítems con cantidades → puede editar cantidades o eliminar → ve total → click 'Ir al checkout'.", "priority": "critical", "status": "in_review", "epic": "CART"},
    {"title": "Panel de administración de productos (CRUD)", "description": "Panel para crear, editar y archivar productos con imágenes, variantes, precio y categoría.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/products → ve listado → click 'Nuevo' → completa formulario → guarda → producto visible en catálogo.", "priority": "medium", "status": "in_review", "epic": "ADMIN"},
    {"title": "Inicio de sesión con Google OAuth", "description": "Autenticación alternativa con Google. Si el usuario no existe, se crea automáticamente.", "configuration": "Solo usuarios no autenticados.", "flow": "Usuario en /login → click 'Continuar con Google' → flujo OAuth → sistema crea o vincula cuenta → redirige al catálogo.", "priority": "high", "status": "in_review", "epic": "AUTH"},
    {"title": "Búsqueda de productos con autocompletado", "description": "Barra de búsqueda global con sugerencias en tiempo real mientras el usuario escribe.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario escribe en barra de búsqueda → el sistema sugiere productos en dropdown → usuario selecciona → navega a /product/{id}.", "priority": "medium", "status": "in_review", "epic": "CATALOG"},

    # ── IN PROGRESS (6) ────────────────────────────────────────────────────
    {"title": "Integración pasarela de pagos Wompi", "description": "Checkout con Wompi: tarjeta de crédito, PSE y Nequi. Webhooks para confirmar pagos asíncronos.", "configuration": "Solo usuarios autenticados. Requiere API keys de Wompi.", "flow": "Usuario en checkout → selecciona método de pago → sistema crea transacción Wompi → usuario completa pago → webhook confirma → pedido marcado como pagado.", "priority": "critical", "status": "in_progress", "epic": "PAYMENTS"},
    {"title": "Flujo de checkout en 3 pasos", "description": "Proceso de compra: Paso 1 — datos de envío. Paso 2 — método de pago. Paso 3 — resumen y confirmación.", "configuration": "Solo usuarios autenticados.", "flow": "Usuario en carrito → click 'Ir al checkout' → Paso 1: dirección → Paso 2: pago → Paso 3: resumen → confirma → pedido creado → redirige a /order/{id}/confirmation.", "priority": "critical", "status": "in_progress", "epic": "CART"},
    {"title": "Sistema de autenticación con JWT", "description": "Tokens de acceso y refresh para mantener sesiones seguras. Renovación automática sin re-autenticación.", "configuration": "Todos los usuarios autenticados.", "flow": "Token de acceso expira → interceptor Axios detecta 401 → envía refresh token → sistema emite nuevos tokens → solicitud original reintentada.", "priority": "high", "status": "in_progress", "epic": "AUTH"},
    {"title": "Gestión de pedidos del cliente", "description": "Historial de pedidos con estado, productos, monto y opción de ver detalle.", "configuration": "Solo usuarios autenticados.", "flow": "Usuario navega a /my-orders → ve lista de pedidos (fecha, monto, estado) → click en pedido → ve detalle con productos y tracking.", "priority": "high", "status": "in_progress", "epic": "PAYMENTS"},
    {"title": "Confirmación de pedido por email", "description": "Email transaccional con resumen del pedido: productos, cantidades, total y datos de envío.", "configuration": "Se dispara automáticamente al confirmar un pago exitoso.", "flow": "Webhook Wompi confirma pago → sistema crea pedido → dispara tarea async → envía email con resumen al cliente.", "priority": "medium", "status": "in_progress", "epic": "NOTIFICATIONS"},
    {"title": "Gestión de categorías de productos", "description": "CRUD de categorías con nombre, descripción, imagen y estado. Las categorías organizan el catálogo.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/categories → ve árbol de categorías → crea/edita → categoría disponible para asignar a productos.", "priority": "medium", "status": "in_progress", "epic": "ADMIN"},

    # ── TODO (10) ──────────────────────────────────────────────────────────
    {"title": "Sistema de cupones y descuentos", "description": "Códigos de descuento porcentuales o fijos, con fecha de vencimiento y límite de usos.", "configuration": "Admin crea los cupones. Cliente los aplica en el checkout.", "flow": "Admin crea cupón en /admin/coupons → cliente en checkout escribe código → sistema valida y aplica descuento → refleja en total.", "priority": "low", "status": "todo", "epic": "PAYMENTS"},
    {"title": "Recuperación de contraseña por email", "description": "Flujo de restablecimiento enviando código de verificación al email del usuario.", "configuration": "Solo usuarios no autenticados.", "flow": "Usuario en /forgot-password → ingresa email → sistema envía código → usuario ingresa código → establece nueva contraseña.", "priority": "high", "status": "todo", "epic": "AUTH"},
    {"title": "Gestión de inventario por producto", "description": "Control de stock por producto y variante, con alertas cuando el stock cae por debajo del mínimo configurado.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/inventory → ve stock actual por variante → actualiza cantidades → al llegar al mínimo, sistema genera alerta.", "priority": "medium", "status": "todo", "epic": "ADMIN"},
    {"title": "Dashboard de reportes de ventas", "description": "Panel con métricas: ventas totales del mes, pedidos por estado, productos más vendidos y ticket promedio.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/reports → ve KPIs con filtro por período → gráfico de ventas → tabla de top productos.", "priority": "low", "status": "todo", "epic": "ADMIN"},
    {"title": "Página de confirmación de pedido", "description": "Pantalla de éxito post-pago con resumen del pedido, número de referencia y CTAs (volver al catálogo, ver mis pedidos).", "configuration": "Solo usuarios autenticados que acaban de pagar.", "flow": "Usuario completa pago → redirigido a /order/{id}/confirmation → ve mensaje de éxito, productos, total y referencia.", "priority": "high", "status": "todo", "epic": "PAYMENTS"},
    {"title": "Notificaciones por email de estado de pedido", "description": "Emails automáticos cuando el estado del pedido cambia: confirmado, en preparación, enviado, entregado.", "configuration": "Se disparan automáticamente por cambios de estado. Solo usuarios autenticados.", "flow": "Admin cambia estado de pedido → sistema detecta cambio → envía email al cliente con nuevo estado y detalles.", "priority": "medium", "status": "todo", "epic": "NOTIFICATIONS"},
    {"title": "Optimización SEO del catálogo y productos", "description": "Meta titles, descriptions y Open Graph para cada página de producto y categoría. URLs amigables.", "configuration": "Configurado a nivel de producto/categoría por el admin.", "flow": "Admin edita producto → rellena campos SEO (meta title, meta description) → sistema genera metatags en el HTML.", "priority": "low", "status": "todo", "epic": "SEO"},
    {"title": "Gestión de pedidos en el panel admin", "description": "Lista de todos los pedidos con filtros por estado, fecha y cliente. Permite cambiar estado y agregar notas internas.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/orders → ve tabla de pedidos → filtra por estado → click en pedido → cambia estado → guarda nota interna.", "priority": "high", "status": "todo", "epic": "ADMIN"},
    {"title": "Lista de deseos (wishlist)", "description": "Permite a usuarios autenticados guardar productos en su lista de deseos para comprar después.", "configuration": "Solo usuarios autenticados.", "flow": "Usuario click en ícono corazón en producto → guardado en wishlist → accede desde /my-wishlist → puede mover al carrito.", "priority": "medium", "status": "todo", "epic": "CATALOG"},
    {"title": "Reseñas y calificaciones de productos", "description": "Usuarios que han comprado un producto pueden dejar reseña con calificación 1-5 y comentario.", "configuration": "Solo usuarios que han comprado el producto. Admin puede moderar.", "flow": "Usuario en /product/{id} → ve sección reseñas → click 'Escribir reseña' → ingresa calificación y texto → publica.", "priority": "low", "status": "todo", "epic": "CATALOG"},

    # ── BACKLOG (14) ───────────────────────────────────────────────────────
    {"title": "Sitemap XML automático", "description": "Generación automática del sitemap.xml con todas las páginas públicas para indexación por motores de búsqueda.", "configuration": "Generado automáticamente. Accesible en /sitemap.xml.", "flow": "Motor de búsqueda accede a /sitemap.xml → ve todas las URLs de productos y categorías con fecha de modificación.", "priority": "low", "status": "backlog", "epic": "SEO"},
    {"title": "Integración Google Tag Manager", "description": "Instalación de GTM para tracking de eventos: vistas de producto, agregar al carrito, iniciar checkout y compra completada.", "configuration": "Configurado con ID de container de GTM. Eventos mapeados al estándar GA4 e-commerce.", "flow": "Usuario navega por la tienda → eventos disparados a la capa de datos → GTM los envía a GA4 y Facebook Pixel.", "priority": "medium", "status": "backlog", "epic": "SEO"},
    {"title": "Perfil de usuario — datos personales y direcciones", "description": "Pantalla donde el usuario gestiona su nombre, teléfono y carnet de identidad, y guarda múltiples direcciones de envío.", "configuration": "Solo usuarios autenticados.", "flow": "Usuario en /my-profile → edita datos personales → agrega o edita direcciones de envío → guarda.", "priority": "medium", "status": "backlog", "epic": "AUTH"},
    {"title": "Métodos de pago guardados", "description": "Permite al usuario tokenizar una tarjeta via Wompi para reutilizarla en compras futuras sin re-ingresar datos.", "configuration": "Solo usuarios autenticados con al menos una compra previa.", "flow": "Usuario en checkout → activa 'Recordar tarjeta' → Wompi tokeniza → en próximas compras aparece tarjeta guardada con últimos 4 dígitos.", "priority": "medium", "status": "backlog", "epic": "PAYMENTS"},
    {"title": "Descuentos por volumen de compra", "description": "Reglas automáticas de descuento basadas en el monto total del carrito (ej: compras > $200.000 obtienen 10%).", "configuration": "Admin configura umbrales y porcentajes. Se aplica automáticamente al cumplir la condición.", "flow": "Usuario agrega productos → carrito supera umbral → sistema aplica descuento automático → se muestra en resumen del carrito.", "priority": "low", "status": "backlog", "epic": "PAYMENTS"},
    {"title": "Módulo de envíos y logística", "description": "Integración con operadores logísticos (Servientrega, Coordinadora) para calcular costo de envío y generar guías.", "configuration": "Requiere API keys de operadores logísticos. Configurable por zona y peso.", "flow": "Usuario en checkout → ingresa dirección → sistema calcula opciones de envío con costo → usuario elige → costo sumado al total.", "priority": "medium", "status": "backlog", "epic": "PAYMENTS"},
    {"title": "Notificación WhatsApp de pedido nuevo", "description": "Mensaje de WhatsApp al admin cuando entra un pedido nuevo, con resumen de productos y datos del cliente.", "configuration": "Requiere API de WhatsApp Business. Configurable el número receptor.", "flow": "Pago confirmado → sistema dispara webhook a WhatsApp API → admin recibe mensaje con resumen del pedido.", "priority": "high", "status": "backlog", "epic": "NOTIFICATIONS"},
    {"title": "Productos relacionados en detalle", "description": "'También te puede interesar' — sección en la ficha del producto mostrando 4 productos de la misma categoría.", "configuration": "Basado en misma categoría y precio similar. No requiere motor de ML.", "flow": "Usuario en /product/{id} → ve sección 'También te puede interesar' → tarjetas de 4 productos relacionados → puede navegar a ellos.", "priority": "medium", "status": "backlog", "epic": "CATALOG"},
    {"title": "Carrusel de productos en promoción", "description": "Sección en la landing con productos marcados como 'en oferta', mostrando precio original y precio con descuento.", "configuration": "Admin marca productos como 'en oferta' y configura precio de oferta.", "flow": "Usuario en home → ve carrusel de ofertas → precio original tachado + precio oferta → click navega a detalle.", "priority": "medium", "status": "backlog", "epic": "CATALOG"},
    {"title": "Comparación de productos", "description": "Permite al usuario seleccionar hasta 3 productos para compararlos lado a lado por especificaciones técnicas.", "configuration": "Solo disponible para categorías con atributos comparables.", "flow": "Usuario en catálogo → checkbox 'Comparar' en máx 3 productos → click 'Comparar seleccionados' → tabla comparativa.", "priority": "low", "status": "backlog", "epic": "CATALOG"},
    {"title": "Facturación electrónica DIAN", "description": "Generación de factura electrónica para los pedidos con pago confirmado, cumpliendo la normativa DIAN.", "configuration": "Integración con proveedor de FE (Siigo o Alegra). Configuración del NIT y responsabilidades.", "flow": "Pago confirmado → sistema genera factura → la envía al proveedor FE → proveedor valida con DIAN → factura enviada al cliente por email.", "priority": "high", "status": "backlog", "epic": "PAYMENTS"},
    {"title": "Política de devoluciones y reembolsos", "description": "Flujo para que el cliente solicite devolución de un pedido entregado. Admin aprueba y gestiona el reembolso.", "configuration": "Solo pedidos con estado 'entregado' dentro de los 30 días.", "flow": "Cliente en /my-orders → click 'Solicitar devolución' → selecciona motivo → admin revisa → aprueba → Wompi procesa reembolso.", "priority": "medium", "status": "backlog", "epic": "PAYMENTS"},
    {"title": "Blog corporativo con SEO", "description": "Sección de blog con artículos optimizados para SEO, categorías y buscador interno.", "configuration": "Admin crea artículos desde panel. Publicación programada.", "flow": "Admin navega a /admin/blog → crea artículo con contenido, imágenes y metadatos SEO → publica → visible en /blog.", "priority": "low", "status": "backlog", "epic": "SEO"},
    {"title": "Exportación de reportes a Excel", "description": "Permite al admin descargar reportes de ventas, pedidos e inventario en formato Excel.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin en /admin/reports → click 'Exportar Excel' → descarga archivo .xlsx con datos del período seleccionado.", "priority": "low", "status": "backlog", "epic": "ADMIN"},
]

REQUIREMENTS_INVENTORY = [
    # ── DONE (3) ───────────────────────────────────────────────────────────
    {"title": "Autenticación con email y contraseña (app móvil)", "description": "Login con email/contraseña para acceder a la app. JWT almacenado en Secure Storage del dispositivo.", "configuration": "Todos los usuarios de la app.", "flow": "Usuario abre app → ingresa email y contraseña → sistema valida → emite JWT → redirige al dashboard principal.", "priority": "critical", "status": "done", "epic": "AUTH"},
    {"title": "Pantalla de inicio con resumen de inventario", "description": "Dashboard principal con KPIs: artículos totales, artículos con stock bajo, últimas entradas y últimas salidas.", "configuration": "Todos los usuarios autenticados.", "flow": "Usuario autenticado → ve dashboard con 4 tarjetas KPI → puede navegar a cada módulo desde los botones de acceso rápido.", "priority": "high", "status": "done", "epic": "INVENTORY"},
    {"title": "Listado de productos/artículos del inventario", "description": "Pantalla con todos los artículos del inventario, filtrable por categoría y con buscador por nombre o código.", "configuration": "Todos los usuarios autenticados.", "flow": "Usuario navega a Inventario → ve lista de artículos con nombre, código, stock actual → puede buscar o filtrar → click en artículo ve detalle.", "priority": "high", "status": "done", "epic": "INVENTORY"},

    # ── IN REVIEW (3) ──────────────────────────────────────────────────────
    {"title": "Lectura de código de barras con cámara", "description": "Usar la cámara del dispositivo para escanear códigos de barras (EAN-13, Code 128) y buscar el artículo en el inventario.", "configuration": "Requiere permiso de cámara en el dispositivo. Todos los usuarios autenticados.", "flow": "Usuario en cualquier pantalla → toca ícono de cámara → activa escáner → apunta a código de barras → el sistema identifica el artículo → navega a su detalle.", "priority": "critical", "status": "in_review", "epic": "BARCODE"},
    {"title": "Registro de entradas de inventario", "description": "Formulario para registrar una entrada de stock: artículo, cantidad, proveedor y fecha.", "configuration": "Usuarios con rol almacenista o admin.", "flow": "Usuario en app → navega a Entradas → click 'Nueva entrada' → escanea código o busca artículo → ingresa cantidad y proveedor → guarda → stock actualizado.", "priority": "high", "status": "in_review", "epic": "INVENTORY"},
    {"title": "Registro de salidas de inventario", "description": "Formulario para registrar salidas: artículo, cantidad, destino o área, y referencia de orden.", "configuration": "Usuarios con rol almacenista o admin.", "flow": "Usuario en app → navega a Salidas → click 'Nueva salida' → selecciona artículo → ingresa cantidad y destino → guarda → stock descontado.", "priority": "high", "status": "in_review", "epic": "INVENTORY"},

    # ── IN PROGRESS (4) ────────────────────────────────────────────────────
    {"title": "Sincronización bidireccional con ERP (SAP B1)", "description": "Sync de productos, stock y movimientos entre la app y SAP Business One vía API REST.", "configuration": "Requiere credenciales SAP B1. Sincronización automática cada 15 minutos y manual bajo demanda.", "flow": "App detecta cambio en inventario → envía delta a la API del ERP → SAP actualiza maestro → próxima sync trae datos actualizados a la app.", "priority": "critical", "status": "in_progress", "epic": "SYNC"},
    {"title": "Alerta de stock mínimo", "description": "Notificación push cuando el stock de un artículo cae por debajo del umbral mínimo configurado.", "configuration": "Umbral configurable por artículo. Notificación a usuarios con rol admin o almacenista.", "flow": "Sistema detecta stock < mínimo → genera notificación push → usuario ve alerta en la app → puede crear orden de compra desde la alerta.", "priority": "high", "status": "in_progress", "epic": "INVENTORY"},
    {"title": "Historial de movimientos por artículo", "description": "Línea de tiempo con todas las entradas y salidas de un artículo, con fecha, cantidad, usuario y referencia.", "configuration": "Todos los usuarios autenticados.", "flow": "Usuario en detalle de artículo → tap 'Ver historial' → ve lista cronológica de movimientos → puede filtrar por rango de fechas.", "priority": "medium", "status": "in_progress", "epic": "INVENTORY"},
    {"title": "Roles y permisos de usuario", "description": "Gestión de roles: admin (acceso completo), almacenista (entradas/salidas), viewer (solo lectura).", "configuration": "Solo el admin puede asignar roles.", "flow": "Admin en ajustes → navega a Usuarios → invita usuario o edita existente → asigna rol → usuario tiene los permisos correspondientes.", "priority": "high", "status": "in_progress", "epic": "AUTH"},

    # ── TODO (5) ───────────────────────────────────────────────────────────
    {"title": "Inventario físico (conteo cíclico)", "description": "Módulo para realizar conteos físicos de inventario: crear sesión de conteo, escanear artículos y comparar con stock teórico.", "configuration": "Solo usuarios con rol admin. Bloquea movimientos del área durante el conteo.", "flow": "Admin crea sesión de conteo → asigna área → almacenistas escanean artículos y registran cantidad física → sistema compara con stock teórico → genera reporte de diferencias.", "priority": "high", "status": "todo", "epic": "INVENTORY"},
    {"title": "Generación de QR/código de barras para artículos", "description": "Generar e imprimir etiquetas con código de barras o QR para artículos que no tienen código propio.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin en detalle de artículo → click 'Generar etiqueta' → selecciona formato (QR o barcode) → descarga PDF → imprime desde dispositivo Bluetooth.", "priority": "medium", "status": "todo", "epic": "BARCODE"},
    {"title": "Reporte de inventario valorizado", "description": "Reporte con el valor total del inventario calculado como stock × costo unitario por artículo.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a Reportes → Inventario valorizado → selecciona fecha de corte → ve tabla con artículo, stock, costo y valor total → puede exportar a Excel.", "priority": "medium", "status": "todo", "epic": "REPORTS"},
    {"title": "Modo offline con cola de sincronización", "description": "La app funciona sin conexión registrando movimientos localmente. Al recuperar conexión, sincroniza automáticamente con el servidor.", "configuration": "Todos los usuarios. Requiere SQLite local en el dispositivo.", "flow": "Usuario sin internet registra entrada/salida → guardado en SQLite local → al recuperar conexión → sistema sincroniza delta → conflictos resueltos por timestamp.", "priority": "high", "status": "todo", "epic": "SYNC"},
    {"title": "Integración con impresora Bluetooth para etiquetas", "description": "Impresión directa de etiquetas de código de barras desde la app a impresoras Zebra vía Bluetooth.", "configuration": "Requiere permiso Bluetooth. Compatible con Zebra ZQ series.", "flow": "Usuario genera etiqueta → selecciona impresora Bluetooth desde la lista → confirma impresión → etiqueta impresa.", "priority": "low", "status": "todo", "epic": "BARCODE"},

    # ── BACKLOG (5) ────────────────────────────────────────────────────────
    {"title": "Transferencias entre bodegas", "description": "Módulo para registrar transferencias de stock entre distintas ubicaciones o bodegas de la empresa.", "configuration": "Usuarios con rol admin o almacenista con acceso a múltiples bodegas.", "flow": "Usuario navega a Transferencias → selecciona bodega origen y destino → elige artículos y cantidades → confirma → stocks ajustados en ambas bodegas.", "priority": "medium", "status": "backlog", "epic": "INVENTORY"},
    {"title": "Dashboard analítico de movimientos", "description": "Gráficos de barras y líneas mostrando rotación de inventario, entradas vs salidas por período y artículos de mayor movimiento.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin en Reportes → Analítica → selecciona período → ve gráficos de rotación y tendencias → puede exportar datos.", "priority": "low", "status": "backlog", "epic": "REPORTS"},
    {"title": "Gestión de proveedores", "description": "CRUD de proveedores con nombre, NIT, contacto y catálogo de productos que suministran.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a Proveedores → crea proveedor con datos → asigna artículos que provee → al registrar entradas puede seleccionar proveedor del listado.", "priority": "medium", "status": "backlog", "epic": "INVENTORY"},
    {"title": "Órdenes de compra desde alertas de stock bajo", "description": "Desde la alerta de stock mínimo, el admin puede crear una orden de compra al proveedor con la cantidad sugerida.", "configuration": "Solo usuarios con rol admin. Requiere proveedores configurados.", "flow": "Admin ve alerta stock bajo → click 'Crear orden de compra' → sistema pre-llena artículo, cantidad sugerida y proveedor → admin confirma → orden enviada.", "priority": "high", "status": "backlog", "epic": "SYNC"},
    {"title": "Notificaciones push de sync completada", "description": "Notificación push confirmando que la sincronización con el ERP se completó exitosamente, o alertando si falló.", "configuration": "Solo usuarios con rol admin.", "flow": "Sistema completa sync → envía push al admin → 'Sincronización completada: X artículos actualizados' o 'Error de sync: verificar conexión ERP'.", "priority": "low", "status": "backlog", "epic": "SYNC"},
]
# fmt: on


class Command(BaseCommand):
    help = 'Seed platform with one admin and one onboarded client for development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Remove existing seed users before creating new ones.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        admin_user = self._create_admin()
        client_user = self._create_client(created_by=admin_user)
        self._create_projects(client_user, admin_user)

        self.stdout.write(self.style.SUCCESS('\nSeed data created successfully:'))
        self.stdout.write(f'  Admin  → {ADMIN_EMAIL} / (env SEED_ADMIN_PASSWORD or Admin1234!)')
        self.stdout.write(f'  Client → {CLIENT_EMAIL} / (env SEED_CLIENT_PASSWORD or Client1234!)')
        self.stdout.write('')

    def _flush(self):
        from content.models import Document
        from content.services.document_type_codes import COLLECTION_ACCOUNT

        seed_docs = Document.objects.filter(title__startswith=SEED_PREFIX).delete()
        if seed_docs[0]:
            self.stdout.write(f'  Deleted {seed_docs[0]} documents titled {SEED_PREFIX!r}')

        n_del, _ = Notification.objects.filter(title__startswith=SEED_PREFIX).delete()
        if n_del:
            self.stdout.write(f'  Deleted {n_del} seed-titled notifications')

        for email in [ADMIN_EMAIL, CLIENT_EMAIL]:
            user = User.objects.filter(email=email).first()
            if user:
                Document.objects.filter(document_type__code=COLLECTION_ACCOUNT).filter(
                    Q(project__client=user) | Q(client_user=user),
                ).delete()
                for project in Project.objects.filter(client=user):
                    for sub in HostingSubscription.objects.filter(project=project):
                        Payment.objects.filter(subscription=sub).delete()
                    HostingSubscription.objects.filter(project=project).delete()
                Project.objects.filter(client=user).delete()
                user.delete()
                self.stdout.write(f'  Deleted existing user: {email}')

    def _create_admin(self):
        if User.objects.filter(email=ADMIN_EMAIL).exists():
            self.stdout.write(f'  Admin already exists: {ADMIN_EMAIL}')
            return User.objects.get(email=ADMIN_EMAIL)

        user = User.objects.create_user(
            username=ADMIN_EMAIL,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            first_name='Gustavo',
            last_name='Pérez',
            is_staff=True,
        )
        UserProfile.objects.create(
            user=user,
            role=UserProfile.ROLE_ADMIN,
            is_onboarded=True,
            profile_completed=True,
            company_name='ProjectApp',
            phone='+57 310 555 0001',
        )
        self.stdout.write(self.style.SUCCESS(f'  Created admin: {ADMIN_EMAIL}'))
        return user

    def _create_client(self, created_by=None):
        if User.objects.filter(email=CLIENT_EMAIL).exists():
            self.stdout.write(f'  Client already exists: {CLIENT_EMAIL}')
            return User.objects.get(email=CLIENT_EMAIL)

        user = User.objects.create_user(
            username=CLIENT_EMAIL,
            email=CLIENT_EMAIL,
            password=CLIENT_PASSWORD,
            first_name='María',
            last_name='Torres',
        )
        UserProfile.objects.create(
            user=user,
            role=UserProfile.ROLE_CLIENT,
            is_onboarded=True,
            profile_completed=True,
            company_name='TechStartup Co.',
            phone='+57 300 123 4567',
            cedula='1020304050',
            date_of_birth='1992-06-15',
            gender=UserProfile.GENDER_FEMALE,
            education_level=UserProfile.EDUCATION_UNIVERSITY,
            created_by=created_by,
        )
        self.stdout.write(self.style.SUCCESS(f'  Created client: {CLIENT_EMAIL}'))
        return user

    def _create_projects(self, client_user, admin_user):
        if Project.objects.filter(client=client_user).exists():
            self.stdout.write(f'  Projects already exist for {client_user.email}')
            ecommerce_project = Project.objects.filter(client=client_user, name='Plataforma E-commerce').first()
            inventory_project = Project.objects.filter(client=client_user, name='App Móvil Inventarios').first()
            if ecommerce_project:
                self._create_deliverables(ecommerce_project, admin_user)
                self._create_requirements(ecommerce_project)
                self._create_change_requests(ecommerce_project, client_user, admin_user)
                self._create_bug_reports(ecommerce_project, client_user, admin_user)
                self._create_subscription(ecommerce_project)
            if inventory_project:
                self._create_inventory_deliverables(inventory_project, admin_user)
                self._create_inventory_requirements(inventory_project)
                self._create_inventory_change_requests(inventory_project, client_user, admin_user)
                self._create_inventory_bug_reports(inventory_project, client_user, admin_user)
            self._create_collection_accounts(
                ecommerce_project, inventory_project, client_user, admin_user,
            )
            if ecommerce_project:
                self._create_extended_seed_data(admin_user, client_user, ecommerce_project)
            return

        proposal = self._create_demo_proposal(client_user)

        today = date.today()

        ecommerce_project = Project.objects.create(
            name='Plataforma E-commerce',
            description='Desarrollo de tienda en línea con catálogo de productos, carrito de compras, pasarela de pagos y panel de administración.',
            client=client_user,
            status=Project.STATUS_ACTIVE,
            progress=18,
            start_date=today - timedelta(days=30),
            estimated_end_date=today + timedelta(days=60),
        )

        prop_deliverable = Deliverable.objects.create(
            project=ecommerce_project,
            category=Deliverable.CATEGORY_DOCUMENTS,
            title=(proposal.title or 'Propuesta comercial')[:300],
            description='',
            file=None,
            uploaded_by=admin_user,
        )
        proposal.deliverable = prop_deliverable
        proposal.save(update_fields=['deliverable_id'])

        Project.objects.create(
            name='App Móvil Inventarios',
            description='Aplicación móvil para gestión de inventario en tiempo real con lector de códigos de barras y sincronización con ERP.',
            client=client_user,
            status=Project.STATUS_PAUSED,
            progress=15,
            start_date=today - timedelta(days=10),
            estimated_end_date=today + timedelta(days=120),
        )

        self.stdout.write(self.style.SUCCESS(f'  Created 2 demo projects for {client_user.email}'))

        self._create_deliverables(ecommerce_project, admin_user)
        self._create_requirements(ecommerce_project)
        self._create_change_requests(ecommerce_project, client_user, admin_user)
        self._create_bug_reports(ecommerce_project, client_user, admin_user)
        self._create_subscription(ecommerce_project)

        inventory_project = Project.objects.filter(client=client_user, name='App Móvil Inventarios').first()
        if inventory_project:
            self._create_inventory_deliverables(inventory_project, admin_user)
            self._create_inventory_requirements(inventory_project)
            self._create_inventory_change_requests(inventory_project, client_user, admin_user)
            self._create_inventory_bug_reports(inventory_project, client_user, admin_user)

        self._create_collection_accounts(
            ecommerce_project, inventory_project, client_user, admin_user,
        )
        self._create_extended_seed_data(admin_user, client_user, ecommerce_project)

    def _create_extended_seed_data(self, admin_user, client_user, ecommerce_project):
        """Extra rows for payments UI, notifications, comments, markdown docs (idempotent)."""
        self._extend_subscription_payments(ecommerce_project)
        self._create_seed_notifications(admin_user, client_user, ecommerce_project)
        self._create_seed_comments(ecommerce_project, admin_user, client_user)
        self._create_seed_markdown_documents(admin_user, client_user, ecommerce_project)
        self._create_data_model_entities(ecommerce_project)

    def _extend_subscription_payments(self, project):
        sub = HostingSubscription.objects.filter(project=project).first()
        if not sub:
            return
        marker = 'seed payment diversity'
        if Payment.objects.filter(subscription=sub, description__icontains=marker).exists():
            return
        today = date.today()
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting {sub.get_plan_display()} — next cycle ({marker})',
            billing_period_start=today + timedelta(days=90),
            billing_period_end=today + timedelta(days=179),
            due_date=today + timedelta(days=14),
            status=Payment.STATUS_PENDING,
        )
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting {sub.get_plan_display()} — overdue ({marker})',
            billing_period_start=today - timedelta(days=180),
            billing_period_end=today - timedelta(days=91),
            due_date=today - timedelta(days=30),
            status=Payment.STATUS_OVERDUE,
        )
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting {sub.get_plan_display()} — failed card ({marker})',
            billing_period_start=today - timedelta(days=270),
            billing_period_end=today - timedelta(days=181),
            due_date=today - timedelta(days=120),
            status=Payment.STATUS_FAILED,
        )
        self.stdout.write(self.style.SUCCESS(f'  Added subscription payment diversity rows ({project.name})'))

    def _create_seed_notifications(self, admin_user, client_user, project):
        if Notification.objects.filter(title__startswith=SEED_PREFIX, user=client_user).exists():
            self.stdout.write('  Seed notifications already present')
            return

        deliverable = Deliverable.objects.filter(project=project).first()
        bug = BugReport.objects.filter(deliverable__project=project).first()
        cr = ChangeRequest.objects.filter(project=project).first()

        Notification.objects.create(
            user=client_user,
            type=Notification.TYPE_GENERAL,
            title=f'{SEED_PREFIX} Welcome to the project hub',
            message='Synthetic row: use this inbox to test read/unread and deep links.',
            project=project,
            is_read=True,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.TYPE_DELIVERABLE_UPLOADED,
            title=f'{SEED_PREFIX} New deliverable available',
            message='Synthetic row for deliverable notification styling.',
            project=project,
            deliverable=deliverable,
            related_object_type='deliverable',
            related_object_id=deliverable.id if deliverable else None,
            is_read=False,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.TYPE_CR_STATUS_CHANGED,
            title=f'{SEED_PREFIX} Change request updated',
            message='Synthetic row tied to a change request.',
            project=project,
            related_object_type='change_request',
            related_object_id=cr.id if cr else None,
            is_read=False,
        )
        Notification.objects.create(
            user=client_user,
            type=Notification.TYPE_BUG_STATUS_CHANGED,
            title=f'{SEED_PREFIX} Bug status changed',
            message='Synthetic row tied to a bug report.',
            project=project,
            deliverable=bug.deliverable if bug else None,
            related_object_type='bug_report',
            related_object_id=bug.id if bug else None,
            is_read=False,
        )

        Notification.objects.create(
            user=admin_user,
            type=Notification.TYPE_BUG_REPORTED,
            title=f'{SEED_PREFIX} Client reported a bug (sample)',
            message='Synthetic row for admin notification list.',
            project=project,
            deliverable=bug.deliverable if bug else None,
            related_object_type='bug_report',
            related_object_id=bug.id if bug else None,
            is_read=False,
        )
        Notification.objects.create(
            user=admin_user,
            type=Notification.TYPE_CR_CREATED,
            title=f'{SEED_PREFIX} New change request (sample)',
            message='Synthetic row for triage workflows.',
            project=project,
            related_object_type='change_request',
            related_object_id=cr.id if cr else None,
            is_read=True,
        )
        self.stdout.write(self.style.SUCCESS('  Created seed notifications (admin + client)'))

    def _create_seed_comments(self, project, admin_user, client_user):
        if not RequirementComment.objects.filter(content__startswith=SEED_PREFIX).exists():
            req = Requirement.objects.filter(
                deliverable__project=project, status=Requirement.STATUS_IN_PROGRESS,
            ).first()
            if req:
                RequirementComment.objects.create(
                    requirement=req,
                    user=admin_user,
                    content=f'{SEED_PREFIX} Internal: synced scope with backend; no blockers.',
                    is_internal=True,
                )
                RequirementComment.objects.create(
                    requirement=req,
                    user=client_user,
                    content=f'{SEED_PREFIX} Can we prioritize checkout before recommendations?',
                    is_internal=False,
                )
                self.stdout.write(self.style.SUCCESS('  Created seed requirement comments'))

        first_bug = BugReport.objects.filter(deliverable__project=project).order_by('id').first()
        if first_bug and not BugComment.objects.filter(
            bug_report=first_bug,
            content__startswith=SEED_PREFIX,
        ).exists():
            BugComment.objects.create(
                bug_report=first_bug,
                user=client_user,
                content=f'{SEED_PREFIX} A short screen recording would help us reproduce faster.',
                is_internal=False,
            )
            self.stdout.write(self.style.SUCCESS('  Created seed bug follow-up comment'))

    def _create_seed_markdown_documents(self, admin_user, client_user, project):
        """Panel / PDF markdown documents (not collection_account)."""
        from content.models import Document, DocumentType
        from content.services.document_type_codes import MARKDOWN
        from content.services.markdown_parser import markdown_to_blocks

        dt_md = DocumentType.objects.filter(code=MARKDOWN).first()
        if not dt_md:
            self.stdout.write(self.style.WARNING('  Skipping seed markdown documents: DocumentType markdown missing'))
            return

        def meta_block(title, client_label):
            return {
                'title': title,
                'client_name': client_label,
                'cover_type': 'generic',
                'include_portada': True,
                'include_subportada': True,
                'include_contraportada': True,
            }

        title_en = f'{SEED_PREFIX} Markdown playbook (panel PDF)'
        if not Document.objects.filter(title=title_en).exists():
            body = (
                '# Seed playbook\n\n'
                'This **markdown** document tests the admin panel PDF pipeline.\n\n'
                '## Sections\n\n'
                '- Preview\n'
                '- Export\n'
            )
            Document.objects.create(
                document_type=dt_md,
                title=title_en,
                created_by=admin_user,
                client_name='Internal QA',
                language=Document.Language.EN,
                status=Document.Status.PUBLISHED,
                content_markdown=body,
                content_json={'meta': meta_block(title_en, 'Internal QA'), 'blocks': markdown_to_blocks(body)},
            )
            self.stdout.write(self.style.SUCCESS(f'  Created markdown document: {title_en}'))

        title_es = f'{SEED_PREFIX} Guía rápida (ES)'
        if not Document.objects.filter(title=title_es).exists():
            body_es = '# Guía\n\nContenido de prueba **semilla** enlazado al proyecto demo.\n'
            Document.objects.create(
                document_type=dt_md,
                title=title_es,
                created_by=admin_user,
                client_name='TechStartup Co.',
                language=Document.Language.ES,
                status=Document.Status.DRAFT,
                content_markdown=body_es,
                content_json={'meta': meta_block(title_es, 'TechStartup Co.'), 'blocks': markdown_to_blocks(body_es)},
                client_user=client_user,
                project=project,
            )
            self.stdout.write(self.style.SUCCESS(f'  Created markdown document: {title_es}'))

    def _create_demo_proposal(self, client_user):
        """Create a full demo BusinessProposal (all default sections) for TechStartup e-commerce."""
        from copy import deepcopy
        from decimal import Decimal

        from content.demo_technical_document import DEMO_TECHNICAL_DOCUMENT_JSON
        from content.models import BusinessProposal, ProposalSection
        from content.services.proposal_service import ProposalService

        existing = BusinessProposal.objects.filter(
            client_name='TechStartup Co.', title__icontains='E-commerce',
        ).first()
        if existing:
            self.stdout.write(f'  Demo proposal already exists: {existing.title}')
            return existing

        proposal_title = 'Propuesta Plataforma E-commerce — TechStartup Co.'
        proposal = BusinessProposal.objects.create(
            title=proposal_title,
            client_name='TechStartup Co.',
            client_email=client_user.email,
            client_phone='+57 300 123 4567',
            language='es',
            total_investment=Decimal('11000000'),
            currency='COP',
            hosting_percent=30,
            hosting_discount_semiannual=20,
            hosting_discount_quarterly=10,
            status='accepted',
            project_type='ecommerce',
            market_type='b2c',
        )

        default_sections = ProposalService.get_default_sections(language='es')
        inv_base = deepcopy(
            next(s['content_json'] for s in default_sections if s['section_type'] == 'investment')
        )
        inv_base['introText'] = 'La inversión total para este proyecto es:'
        inv_base['totalInvestment'] = '$11.000.000'
        inv_base['currency'] = 'COP'
        inv_base['paymentOptions'] = [
            {'label': '40% al firmar el contrato \u270d\ufe0f', 'description': '$4.400.000 COP'},
            {'label': '30% al aprobar el diseño final \u2705', 'description': '$3.300.000 COP'},
            {'label': '30% al desplegar el sitio web \U0001f680', 'description': '$3.300.000 COP'},
        ]
        inv_base['hostingPlan'] = {
            'title': 'Hosting Cloud 1',
            'description': 'Infraestructura optimizada para alto rendimiento.',
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
        }
        inv_base['whatsIncluded'] = [
            {'icon': '\U0001f3a8', 'title': 'Diseño', 'description': 'UX/UI personalizado'},
            {'icon': '\u2699\ufe0f', 'title': 'Desarrollo', 'description': 'Frontend y backend a medida'},
            {'icon': '\U0001f680', 'title': 'Despliegue', 'description': 'Puesta en producción'},
        ]

        demo_tech = deepcopy(DEMO_TECHNICAL_DOCUMENT_JSON)
        for epic in demo_tech.get('epics') or []:
            if epic.get('epicKey') == 'storefront':
                reqs = epic.get('requirements') or []
                if not any(r.get('flowKey') == 'flow-wompi-checkout' for r in reqs if isinstance(r, dict)):
                    reqs.append({
                        'flowKey': 'flow-wompi-checkout',
                        'title': 'Integración Wompi en checkout',
                        'description': 'Cobro con tarjeta y PSE (demo plataforma).',
                        'configuration': 'Sandbox',
                        'usageFlow': 'Usuario completa datos → confirma → redirección Wompi.',
                        'priority': 'critical',
                    })
                    epic['requirements'] = reqs
                break

        for section_cfg in default_sections:
            cfg = deepcopy(section_cfg)
            st = cfg['section_type']
            if st == 'greeting':
                cfg['content_json']['clientName'] = 'TechStartup Co.'
                cfg['content_json']['proposalTitle'] = proposal_title
            elif st == 'investment':
                cfg['content_json'] = inv_base
            elif st == 'technical_document':
                cfg['content_json'] = demo_tech
            ProposalSection.objects.create(proposal=proposal, **cfg)

        self.stdout.write(self.style.SUCCESS(f'  Created demo proposal: {proposal.title}'))
        return proposal

    def _create_requirements(self, project):
        if Requirement.objects.filter(deliverable__project=project).exists():
            self.stdout.write(f'  Requirements already exist for {project.name}')
            return

        default_deliverable = (
            Deliverable.objects.filter(project=project)
            .filter(business_proposal__isnull=False)
            .order_by('id')
            .first()
        ) or Deliverable.objects.filter(project=project).order_by('id').first()

        if not default_deliverable:
            default_deliverable = Deliverable.objects.create(
                project=project,
                category=Deliverable.CATEGORY_OTHER,
                title='Alcance inicial',
                description='',
                file=None,
                uploaded_by=project.client,
            )

        order_counters = {}
        objs = []
        for req in REQUIREMENTS_ECOMMERCE:
            status = req['status']
            order_counters.setdefault(status, 0)
            epic_key = req.get('epic', '')
            objs.append(Requirement(
                deliverable=default_deliverable,
                title=req['title'],
                description=req.get('description', ''),
                configuration=req.get('configuration', ''),
                flow=req.get('flow', ''),
                status=status,
                priority=req.get('priority', 'medium'),
                order=order_counters[status],
                source_epic_key=epic_key,
                source_epic_title=EPICS_ECOMMERCE.get(epic_key, ''),
            ))
            order_counters[status] += 1

        Requirement.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS(
            f'  Created {len(objs)} requirements across {len(EPICS_ECOMMERCE)} epics for {project.name}'
        ))

    def _create_inventory_requirements(self, project):
        if Requirement.objects.filter(deliverable__project=project).exists():
            self.stdout.write(f'  Requirements already exist for {project.name}')
            return

        default_deliverable = Deliverable.objects.filter(project=project).order_by('id').first()
        if not default_deliverable:
            default_deliverable = Deliverable.objects.create(
                project=project,
                category=Deliverable.CATEGORY_OTHER,
                title='Alcance App Inventarios',
                description='',
                file=None,
                uploaded_by=project.client,
            )

        order_counters = {}
        objs = []
        for req in REQUIREMENTS_INVENTORY:
            status = req['status']
            order_counters.setdefault(status, 0)
            epic_key = req.get('epic', '')
            objs.append(Requirement(
                deliverable=default_deliverable,
                title=req['title'],
                description=req.get('description', ''),
                configuration=req.get('configuration', ''),
                flow=req.get('flow', ''),
                status=status,
                priority=req.get('priority', 'medium'),
                order=order_counters[status],
                source_epic_key=epic_key,
                source_epic_title=EPICS_INVENTORY.get(epic_key, ''),
            ))
            order_counters[status] += 1

        Requirement.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS(
            f'  Created {len(objs)} requirements across {len(EPICS_INVENTORY)} epics for {project.name}'
        ))

    def _create_change_requests(self, project, client_user, admin_user):
        if ChangeRequest.objects.filter(project=project).exists():
            self.stdout.write(f'  Change requests already exist for {project.name}')
            return

        crs = [
            {
                'title': 'Agregar filtro de rango de precio en catálogo',
                'description': 'Los usuarios necesitan poder filtrar productos por un rango de precio mínimo y máximo, similar a lo que hace MercadoLibre.',
                'module_or_screen': 'Catálogo / Filtros',
                'suggested_priority': 'high',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_APPROVED,
                'admin_response': 'Buen punto, lo incluiremos en el sprint actual. Estimamos 2 días de trabajo.',
                'estimated_cost': 0,
                'estimated_time': '2 días',
            },
            {
                'title': 'Cambiar color del botón de compra a verde',
                'description': 'El botón "Agregar al carrito" actualmente es azul, pero creemos que verde genera más confianza para la acción de compra.',
                'module_or_screen': 'Producto detalle',
                'suggested_priority': 'low',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_EVALUATING,
                'admin_response': '',
                'estimated_cost': None,
                'estimated_time': '',
            },
            {
                'title': 'Integrar login con Google',
                'description': 'Queremos que los clientes puedan iniciar sesión con su cuenta de Google además del email/password.',
                'module_or_screen': 'Autenticación',
                'suggested_priority': 'medium',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_PENDING,
                'admin_response': '',
                'estimated_cost': None,
                'estimated_time': '',
            },
            {
                'title': 'Agregar sección de productos recomendados',
                'description': 'En la página de detalle de producto, mostrar una sección "También te puede interesar" con productos relacionados.',
                'module_or_screen': 'Producto detalle',
                'suggested_priority': 'medium',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_REJECTED,
                'admin_response': 'Este cambio requiere un motor de recomendaciones que está fuera del alcance actual. Lo evaluaremos para la fase 2.',
                'estimated_cost': None,
                'estimated_time': '',
            },
            {
                'title': 'Notificación WhatsApp cuando hay pedido nuevo',
                'description': 'Además del email, necesitamos una notificación por WhatsApp cuando un cliente realiza un pedido.',
                'module_or_screen': 'Notificaciones',
                'suggested_priority': 'high',
                'is_urgent': True,
                'status': ChangeRequest.STATUS_NEEDS_CLARIFICATION,
                'admin_response': '¿Quieres recibir la notificación solo tú o también el equipo de bodega?',
                'estimated_cost': None,
                'estimated_time': '',
            },
        ]

        for cr_data in crs:
            cr = ChangeRequest.objects.create(
                project=project,
                created_by=client_user,
                title=cr_data['title'],
                description=cr_data['description'],
                module_or_screen=cr_data.get('module_or_screen', ''),
                suggested_priority=cr_data['suggested_priority'],
                is_urgent=cr_data.get('is_urgent', False),
                status=cr_data['status'],
                admin_response=cr_data.get('admin_response', ''),
                estimated_cost=cr_data.get('estimated_cost'),
                estimated_time=cr_data.get('estimated_time', ''),
            )

            if cr_data['admin_response']:
                ChangeRequestComment.objects.create(
                    change_request=cr,
                    user=admin_user,
                    content=cr_data['admin_response'],
                    is_internal=False,
                )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(crs)} change requests for {project.name}'))

    def _create_bug_reports(self, project, client_user, admin_user):
        if BugReport.objects.filter(deliverable__project=project).exists():
            self.stdout.write(f'  Bug reports already exist for {project.name}')
            return

        deliverable_list = list(
            Deliverable.objects.filter(project=project).order_by('id'),
        )
        if not deliverable_list:
            self.stdout.write(self.style.WARNING(f'  Skipping bug reports — no deliverables for {project.name}'))
            return

        bugs = [
            {
                'title': 'Botón "Agregar al carrito" no responde en móvil',
                'description': 'En dispositivos móviles (iPhone 14, Safari), al tocar el botón de agregar al carrito no pasa nada.',
                'severity': BugReport.SEVERITY_CRITICAL,
                'steps_to_reproduce': [
                    'Abrir la tienda desde un iPhone',
                    'Navegar a cualquier producto',
                    'Tocar el botón "Agregar al carrito"',
                    'No sucede nada, el carrito sigue vacío',
                ],
                'expected_behavior': 'El producto debería agregarse al carrito y mostrar confirmación.',
                'actual_behavior': 'El botón no responde al touch en Safari iOS.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'iPhone 14 / Safari 17',
                'is_recurring': True,
                'status': BugReport.STATUS_CONFIRMED,
                'admin_response': 'Confirmado. Parece un problema con el event handler en Safari. Lo priorizamos.',
            },
            {
                'title': 'Imágenes del catálogo cargan muy lento',
                'description': 'Las imágenes de productos tardan más de 5 segundos en cargar, especialmente en conexiones 4G.',
                'severity': BugReport.SEVERITY_HIGH,
                'steps_to_reproduce': [
                    'Abrir el catálogo de productos',
                    'Hacer scroll por la lista',
                    'Las imágenes aparecen como placeholder gris por varios segundos',
                ],
                'expected_behavior': 'Las imágenes deberían cargar en menos de 2 segundos.',
                'actual_behavior': 'Tardan 5-8 segundos. No hay lazy loading.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Chrome 120 / Windows',
                'is_recurring': True,
                'status': BugReport.STATUS_FIXING,
                'admin_response': 'Vamos a implementar lazy loading y optimización de imágenes.',
            },
            {
                'title': 'Error 500 al buscar con caracteres especiales',
                'description': 'Si se busca un producto usando comillas o el símbolo & en el buscador, da error de servidor.',
                'severity': BugReport.SEVERITY_MEDIUM,
                'steps_to_reproduce': [
                    'Ir al buscador de productos',
                    'Escribir: camiseta "roja"',
                    'Presionar Enter',
                    'Aparece página de error 500',
                ],
                'expected_behavior': 'Debería mostrar resultados o un mensaje de "sin resultados".',
                'actual_behavior': 'Error 500 Internal Server Error.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Chrome / macOS',
                'is_recurring': True,
                'status': BugReport.STATUS_REPORTED,
                'admin_response': '',
            },
            {
                'title': 'Precio muestra $0 en algunos productos',
                'description': 'Algunos productos muestran $0 como precio aunque en el admin tienen precio configurado.',
                'severity': BugReport.SEVERITY_HIGH,
                'steps_to_reproduce': [
                    'Navegar al catálogo',
                    'Filtrar por categoría "Electrónicos"',
                    'Ver que 2 productos muestran $0',
                ],
                'expected_behavior': 'Todos los productos deberían mostrar su precio real.',
                'actual_behavior': 'Algunos muestran $0.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Cualquier navegador',
                'is_recurring': False,
                'status': BugReport.STATUS_RESOLVED,
                'admin_response': 'Era un problema de caché. Ya se limpió y se agregó invalidación automática.',
            },
            {
                'title': 'Formulario de contacto no envía en Firefox',
                'description': 'El formulario de contacto del footer no envía en Firefox. El botón se queda en estado "Enviando..." indefinidamente.',
                'severity': BugReport.SEVERITY_LOW,
                'steps_to_reproduce': [
                    'Abrir la tienda en Firefox',
                    'Ir al footer y llenar el formulario de contacto',
                    'Hacer clic en Enviar',
                    'El botón cambia a "Enviando..." y nunca termina',
                ],
                'expected_behavior': 'El formulario debería enviarse y mostrar mensaje de confirmación.',
                'actual_behavior': 'Se queda cargando indefinidamente.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Firefox 121 / Windows',
                'is_recurring': True,
                'status': BugReport.STATUS_REPORTED,
                'admin_response': '',
            },
        ]

        for i, bug_data in enumerate(bugs):
            dlv = deliverable_list[i % len(deliverable_list)]
            bug = BugReport.objects.create(
                deliverable=dlv,
                reported_by=client_user,
                title=bug_data['title'],
                description=bug_data['description'],
                severity=bug_data['severity'],
                steps_to_reproduce=bug_data['steps_to_reproduce'],
                expected_behavior=bug_data['expected_behavior'],
                actual_behavior=bug_data['actual_behavior'],
                environment=bug_data['environment'],
                device_browser=bug_data.get('device_browser', ''),
                is_recurring=bug_data.get('is_recurring', False),
                status=bug_data['status'],
                admin_response=bug_data.get('admin_response', ''),
            )

            if bug_data['admin_response']:
                BugComment.objects.create(
                    bug_report=bug,
                    user=admin_user,
                    content=bug_data['admin_response'],
                    is_internal=False,
                )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(bugs)} bug reports for {project.name}'))

    def _create_data_model_entities(self, project):
        """Seed DataModelEntity records for the documents deliverable (idempotent)."""
        if DataModelEntity.objects.filter(
            deliverable__project=project,
            source_entity_name='Usuario',
        ).exists():
            self.stdout.write(f'  DataModelEntity records already seeded for {project.name}')
            return

        deliverable = Deliverable.objects.filter(
            project=project,
            category=Deliverable.CATEGORY_DOCUMENTS,
        ).first()
        if not deliverable:
            self.stdout.write('  No documents deliverable found — skipping DataModelEntity seed')
            return

        entities = [
            {
                'name': 'Usuario',
                'source_entity_name': 'Usuario',
                'description': 'Representa a un usuario registrado en la plataforma.',
                'key_fields': 'id, email, rol',
                'relationship': '',
            },
            {
                'name': 'Producto',
                'source_entity_name': 'Producto',
                'description': 'Artículo disponible en el catálogo del e-commerce.',
                'key_fields': 'id, sku, nombre, precio',
                'relationship': 'Pertenece a Categoría',
            },
            {
                'name': 'Pedido',
                'source_entity_name': 'Pedido',
                'description': 'Orden de compra creada por un cliente.',
                'key_fields': 'id, estado, total, fecha',
                'relationship': 'Pertenece a Usuario, contiene Producto',
            },
        ]

        for e_data in entities:
            DataModelEntity.objects.create(
                deliverable=deliverable,
                name=e_data['name'],
                source_entity_name=e_data['source_entity_name'],
                description=e_data['description'],
                key_fields=e_data['key_fields'],
                relationship=e_data.get('relationship', ''),
            )

        # Also seed ProjectDataModelEntity rows for the project
        if not ProjectDataModelEntity.objects.filter(project=project).exists():
            project_entities = [
                {'name': 'Usuario', 'key_fields': 'id, email, rol',
                 'description': 'Usuario registrado', 'relationship': ''},
                {'name': 'Producto', 'key_fields': 'id, sku, nombre',
                 'description': 'Artículo del catálogo', 'relationship': 'N:1 con Categoría'},
                {'name': 'Pedido', 'key_fields': 'id, estado, total',
                 'description': 'Orden de compra', 'relationship': 'N:1 con Usuario'},
            ]
            for pe_data in project_entities:
                ProjectDataModelEntity.objects.create(project=project, **pe_data)

        self.stdout.write(self.style.SUCCESS(
            f'  Created {len(entities)} DataModelEntity records for {project.name}'
        ))

    def _create_deliverables(self, project, admin_user):
        marker_title = 'Wireframes — Catálogo y checkout'
        if Deliverable.objects.filter(project=project, title=marker_title).exists():
            self.stdout.write(f'  File deliverables already seeded for {project.name}')
            return

        from accounts.models import DeliverableVersion
        from django.core.files.base import ContentFile

        deliverables = [
            {
                'title': 'Wireframes — Catálogo y checkout',
                'description': 'Wireframes de baja fidelidad para catálogo, detalle de producto, carrito y flujo de checkout en 3 pasos.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'wireframes-catalogo-checkout-v1.pdf',
                'epic_key': 'CART',
            },
            {
                'title': 'Guía de estilos UI — TechStartup',
                'description': 'Sistema de diseño: colores, tipografías, componentes de botones, formularios, tarjetas y estados.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'style-guide-techstartup-v1.pdf',
                'epic_key': 'CATALOG',
            },
            {
                'title': 'Credenciales Wompi Sandbox',
                'description': 'Llaves de API para pruebas en sandbox de Wompi: public key, events secret y URL de webhooks configurada.',
                'category': Deliverable.CATEGORY_CREDENTIALS,
                'filename': 'wompi-sandbox-keys.txt',
                'epic_key': 'PAYMENTS',
            },
            {
                'title': 'Manual del panel de administración',
                'description': 'Guía paso a paso para administradores: gestión de productos, categorías, pedidos, inventario y reportes.',
                'category': Deliverable.CATEGORY_DOCUMENTS,
                'filename': 'manual-admin-ecommerce-v1.pdf',
                'epic_key': 'ADMIN',
            },
            {
                'title': 'Documento de arquitectura — Plataforma E-commerce',
                'description': 'Diagrama de arquitectura: Next.js frontend, Django API, PostgreSQL, Redis, Wompi webhooks y CDN para imágenes.',
                'category': Deliverable.CATEGORY_DOCUMENTS,
                'filename': 'arquitectura-ecommerce-v1.pdf',
                'epic_key': '',
            },
        ]

        for d_data in deliverables:
            placeholder = ContentFile(b'placeholder content', name=d_data['filename'])
            epic_key = d_data.get('epic_key', '')
            d = Deliverable.objects.create(
                project=project,
                uploaded_by=admin_user,
                title=d_data['title'],
                description=d_data['description'],
                category=d_data['category'],
                file=placeholder,
                current_version=1,
                source_epic_key=epic_key,
                source_epic_title=EPICS_ECOMMERCE.get(epic_key, ''),
            )
            DeliverableVersion.objects.create(
                deliverable=d,
                file=placeholder,
                version_number=1,
                uploaded_by=admin_user,
            )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(deliverables)} deliverables for {project.name}'))

    def _create_inventory_deliverables(self, project, admin_user):
        if Deliverable.objects.filter(project=project).exists():
            self.stdout.write(f'  Deliverables already exist for {project.name}')
            return

        from accounts.models import DeliverableVersion
        from django.core.files.base import ContentFile

        deliverables = [
            {
                'title': 'Mockups de pantallas principales — App Inventarios',
                'description': 'Diseño de las pantallas clave: dashboard, listado de artículos, detalle, entradas/salidas y alertas.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'mockups-app-inventarios-v1.pdf',
                'epic_key': 'INVENTORY',
            },
            {
                'title': 'Documento de integración SAP Business One',
                'description': 'Especificación técnica del API de sincronización con SAP B1: endpoints, autenticación, modelos de datos y manejo de errores.',
                'category': Deliverable.CATEGORY_DOCUMENTS,
                'filename': 'integracion-sap-b1-v1.pdf',
                'epic_key': 'SYNC',
            },
            {
                'title': 'APK Android beta v0.1',
                'description': 'Build de prueba para Android con autenticación, listado de inventario y escáner básico de código de barras.',
                'category': Deliverable.CATEGORY_APKS,
                'filename': 'inventarios-beta-v0.1.apk',
                'epic_key': 'BARCODE',
            },
            {
                'title': 'Manual de uso para almacenistas',
                'description': 'Guía de usuario para almacenistas: registrar entradas, salidas, escanear códigos y ver historial de movimientos.',
                'category': Deliverable.CATEGORY_DOCUMENTS,
                'filename': 'manual-almacenista-v1.pdf',
                'epic_key': '',
            },
        ]

        for d_data in deliverables:
            placeholder = ContentFile(b'placeholder content', name=d_data['filename'])
            epic_key = d_data.get('epic_key', '')
            d = Deliverable.objects.create(
                project=project,
                uploaded_by=admin_user,
                title=d_data['title'],
                description=d_data['description'],
                category=d_data['category'],
                file=placeholder,
                current_version=1,
                source_epic_key=epic_key,
                source_epic_title=EPICS_INVENTORY.get(epic_key, ''),
            )
            DeliverableVersion.objects.create(
                deliverable=d,
                file=placeholder,
                version_number=1,
                uploaded_by=admin_user,
            )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(deliverables)} deliverables for {project.name}'))

    def _create_subscription(self, project):
        if HostingSubscription.objects.filter(project=project).exists():
            self.stdout.write(f'  Subscription already exists for {project.name}')
            return

        from decimal import Decimal

        today = date.today()

        sub = HostingSubscription.objects.create(
            project=project,
            plan=HostingSubscription.PLAN_QUARTERLY,
            base_monthly_amount=Decimal('330000'),
            discount_percent=10,
            effective_monthly_amount=Decimal('297000'),
            billing_amount=Decimal('891000'),
            status=HostingSubscription.STATUS_ACTIVE,
            start_date=today - timedelta(days=90),
            next_billing_date=today + timedelta(days=90),
        )

        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting trimestral — {project.name}',
            billing_period_start=today - timedelta(days=90),
            billing_period_end=today - timedelta(days=1),
            due_date=today - timedelta(days=90),
            status=Payment.STATUS_PAID,
            paid_at=timezone.now() - timedelta(days=88),
        )
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting trimestral — {project.name}',
            billing_period_start=today,
            billing_period_end=today + timedelta(days=89),
            due_date=today,
            status=Payment.STATUS_PAID,
            paid_at=timezone.now() - timedelta(hours=2),
        )

        self.stdout.write(self.style.SUCCESS(f'  Created subscription + 2 payments for {project.name}'))

    def _create_collection_accounts(self, ecommerce_project, inventory_project, client_user, admin_user):
        """
        Seed collection_account documents for platform QA: draft, issued, paid, cancelled, overdue.
        Titles are prefixed with [Demo] for easy identification.
        """
        from decimal import Decimal

        from content.models import (
            Document,
            DocumentCollectionAccount,
            DocumentItem,
            DocumentPaymentMethod,
            IssuerProfile,
        )
        from content.services.collection_account_service import (
            issue_collection_account,
            mark_collection_account_cancelled,
            mark_collection_account_paid,
            recalculate_document_totals,
        )
        from content.services.document_type_utils import get_collection_account_document_type

        if not ecommerce_project:
            self.stdout.write(self.style.WARNING('  Skipping collection accounts: no e-commerce project'))
            return

        if Document.objects.filter(
            project=ecommerce_project,
            document_type__code='collection_account',
        ).exists():
            self.stdout.write('  Collection accounts already seeded for demo project')
            return

        issuer = IssuerProfile.objects.order_by('pk').first()
        if not issuer:
            self.stdout.write(
                self.style.WARNING(
                    '  Skipping collection accounts: run migrations (IssuerProfile / DocumentType)',
                ),
            )
            return

        try:
            doc_type = get_collection_account_document_type()
        except Exception:
            self.stdout.write(
                self.style.WARNING('  Skipping collection accounts: collection_account DocumentType missing'),
            )
            return

        today = date.today()

        def new_draft(title, project, *, billing_concept, payment_term_days=30, support_ref=''):
            doc = Document.objects.create(
                title=title,
                document_type=doc_type,
                commercial_status=Document.CommercialStatus.DRAFT,
                project=project,
                client_user=client_user,
                currency='COP',
                city='Bogotá',
                notes='Demo seed data for platform tests.',
                created_by=admin_user,
                updated_by=admin_user,
            )
            DocumentCollectionAccount.objects.create(
                document=doc,
                billing_concept=billing_concept,
                payment_term_type=DocumentCollectionAccount.PaymentTermType.DAYS_AFTER_ISSUE,
                payment_term_days=payment_term_days,
                support_reference=support_ref or f'DEMO-PROJ-{project.id}',
            )
            return doc

        def add_items(doc, rows):
            for idx, row in enumerate(rows):
                qty = Decimal(str(row['quantity']))
                up = Decimal(str(row['unit_price']))
                da = Decimal(str(row.get('discount_amount', '0')))
                ta = Decimal(str(row.get('tax_amount', '0')))
                lt = row.get('line_total')
                if lt is None:
                    lt = qty * up - da + ta
                else:
                    lt = Decimal(str(lt))
                DocumentItem.objects.create(
                    document=doc,
                    position=row.get('position', idx),
                    item_type=row.get('item_type', DocumentItem.ItemType.SERVICE),
                    description=row['description'],
                    quantity=qty,
                    unit_price=up,
                    discount_amount=da,
                    tax_amount=ta,
                    line_total=lt,
                )
            recalculate_document_totals(doc)
            doc.save()

        def add_bank_transfer(doc):
            DocumentPaymentMethod.objects.create(
                document=doc,
                payment_method_type=DocumentPaymentMethod.MethodType.BANK_TRANSFER,
                bank_name='Bancolombia',
                account_type='checking',
                account_number='1234567890',
                account_holder_name='ProjectApp SAS',
                account_holder_identification='900123456',
                payment_instructions='Reference: invoice number. Email receipt to finance@projectapp.co',
                is_primary=True,
            )

        # 1) Draft only (admin sees it; client list hides drafts)
        d1 = new_draft(
            '[Demo] Draft collection account',
            ecommerce_project,
            billing_concept='E-commerce milestone 1 — pending approval',
        )
        add_items(
            d1,
            [
                {
                    'description': 'UX/UI design sprint (40h)',
                    'quantity': '1',
                    'unit_price': '4400000',
                    'discount_amount': '0',
                    'tax_amount': '0',
                },
            ],
        )

        # 2) Issued + payment method (client visible, PDF-ready)
        d2 = new_draft(
            '[Demo] Issued collection account',
            ecommerce_project,
            billing_concept='Development installment — design sign-off',
            payment_term_days=15,
        )
        add_items(
            d2,
            [
                {
                    'description': 'Payment milestone: 30% after design approval',
                    'quantity': '1',
                    'unit_price': '3300000',
                    'item_type': DocumentItem.ItemType.ADVANCE,
                },
                {
                    'description': 'Hosting setup (quarterly)',
                    'quantity': '1',
                    'unit_price': '891000',
                    'item_type': DocumentItem.ItemType.HOSTING,
                },
            ],
        )
        add_bank_transfer(d2)
        d2 = Document.objects.get(pk=d2.pk)
        issue_collection_account(d2, issuer=issuer, acting_user=admin_user)

        # 3) Paid (terminal state)
        d3 = new_draft(
            '[Demo] Paid collection account',
            ecommerce_project,
            billing_concept='Initial deposit — contract signature',
            payment_term_days=7,
        )
        add_items(
            d3,
            [
                {
                    'description': '40% at contract signature',
                    'quantity': '1',
                    'unit_price': '4400000',
                },
            ],
        )
        add_bank_transfer(d3)
        d3 = Document.objects.get(pk=d3.pk)
        issue_collection_account(d3, issuer=issuer, acting_user=admin_user)
        mark_collection_account_paid(d3, acting_user=admin_user)

        # 4) Cancelled from draft
        d4 = new_draft(
            '[Demo] Cancelled from draft',
            ecommerce_project,
            billing_concept='Superseded by revised quote',
        )
        add_items(
            d4,
            [{'description': 'Placeholder line', 'quantity': '1', 'unit_price': '100'}],
        )
        d4 = Document.objects.get(pk=d4.pk)
        mark_collection_account_cancelled(d4, acting_user=admin_user)

        # 5) Issued + overdue (due date in the past)
        d5 = new_draft(
            '[Demo] Overdue collection account',
            ecommerce_project,
            billing_concept='Balance due — integration phase',
            payment_term_days=14,
        )
        add_items(
            d5,
            [
                {
                    'description': 'Wompi integration + testing',
                    'quantity': '1',
                    'unit_price': '2500000',
                },
            ],
        )
        add_bank_transfer(d5)
        d5 = Document.objects.get(pk=d5.pk)
        issue_collection_account(d5, issuer=issuer, acting_user=admin_user)
        Document.objects.filter(pk=d5.pk).update(due_date=today - timedelta(days=20))

        # 6) Issued then cancelled (voided after issue)
        d6 = new_draft(
            '[Demo] Cancelled after issue',
            ecommerce_project,
            billing_concept='Invoice void — duplicate entry',
            payment_term_days=10,
        )
        add_items(
            d6,
            [{'description': 'Duplicate billing correction', 'quantity': '1', 'unit_price': '500000'}],
        )
        d6 = Document.objects.get(pk=d6.pk)
        issue_collection_account(d6, issuer=issuer, acting_user=admin_user)
        d6 = Document.objects.get(pk=d6.pk)
        mark_collection_account_cancelled(d6, acting_user=admin_user)

        # 7) Second project — small issued document
        if inventory_project:
            d7 = new_draft(
                '[Demo] Inventory app — discovery invoice',
                inventory_project,
                billing_concept='Discovery workshop (2 days)',
                payment_term_days=20,
            )
            add_items(
                d7,
                [{'description': 'Workshop + backlog', 'quantity': '2', 'unit_price': '800000'}],
            )
            d7 = Document.objects.get(pk=d7.pk)
            issue_collection_account(d7, issuer=issuer, acting_user=admin_user)

        self.stdout.write(
            self.style.SUCCESS(
                '  Created demo collection accounts (draft, issued, paid, cancelled, overdue, multi-project)',
            ),
        )

    def _create_inventory_change_requests(self, project, client_user, admin_user):
        if ChangeRequest.objects.filter(project=project).exists():
            self.stdout.write(f'  Change requests already exist for {project.name}')
            return

        crs = [
            {
                'title': 'Soporte para lectura de códigos QR además de barcode',
                'description': 'Actualmente el escáner solo lee EAN-13 y Code 128. Necesitamos que también lea QR para los artículos nuevos que vienen de fábrica con etiqueta QR.',
                'module_or_screen': 'Escáner / Entrada de inventario',
                'suggested_priority': 'high',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_APPROVED,
                'admin_response': 'El SDK de zxing soporta QR de forma nativa. Lo habilitaremos en el sprint actual sin costo adicional.',
                'estimated_cost': 0,
                'estimated_time': '1 día',
            },
            {
                'title': 'Integración con Coordinadora para despachos directos',
                'description': 'Al registrar una salida hacia cliente externo, queremos poder generar la guía de Coordinadora desde la app sin tener que entrar al portal por separado.',
                'module_or_screen': 'Registro de salidas',
                'suggested_priority': 'medium',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_EVALUATING,
                'admin_response': 'Coordinadora tiene una API REST. Estamos revisando el costo de la integración y los planes de acceso. Te confirmamos en 3 días.',
                'estimated_cost': None,
                'estimated_time': '',
            },
            {
                'title': 'Agregar campo de foto al registrar una salida',
                'description': 'El almacenista quiere tomar una foto del artículo al momento de registrar la salida para dejar evidencia del estado en que fue entregado.',
                'module_or_screen': 'Registro de salidas',
                'suggested_priority': 'low',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_PENDING,
                'admin_response': '',
                'estimated_cost': None,
                'estimated_time': '',
            },
            {
                'title': 'Exportar historial de movimientos a Excel',
                'description': 'El gerente de operaciones necesita descargar el historial de movimientos por artículo o por bodega en formato Excel para su reporte mensual.',
                'module_or_screen': 'Reportes / Historial',
                'suggested_priority': 'medium',
                'is_urgent': True,
                'status': ChangeRequest.STATUS_NEEDS_CLARIFICATION,
                'admin_response': '¿El reporte debe incluir solo movimientos del mes actual o histórico completo? ¿Necesitan filtro por bodega también?',
                'estimated_cost': None,
                'estimated_time': '',
            },
        ]

        for cr_data in crs:
            cr = ChangeRequest.objects.create(
                project=project,
                created_by=client_user,
                title=cr_data['title'],
                description=cr_data['description'],
                module_or_screen=cr_data.get('module_or_screen', ''),
                suggested_priority=cr_data['suggested_priority'],
                is_urgent=cr_data.get('is_urgent', False),
                status=cr_data['status'],
                admin_response=cr_data.get('admin_response', ''),
                estimated_cost=cr_data.get('estimated_cost'),
                estimated_time=cr_data.get('estimated_time', ''),
            )

            if cr_data['admin_response']:
                ChangeRequestComment.objects.create(
                    change_request=cr,
                    user=admin_user,
                    content=cr_data['admin_response'],
                    is_internal=False,
                )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(crs)} change requests for {project.name}'))

    def _create_inventory_bug_reports(self, project, client_user, admin_user):
        if BugReport.objects.filter(deliverable__project=project).exists():
            self.stdout.write(f'  Bug reports already exist for {project.name}')
            return

        deliverable_list = list(
            Deliverable.objects.filter(project=project).order_by('id'),
        )
        if not deliverable_list:
            self.stdout.write(self.style.WARNING(f'  Skipping bug reports — no deliverables for {project.name}'))
            return

        bugs = [
            {
                'title': 'El escáner de código de barras falla en Android 14',
                'description': 'En dispositivos con Android 14, al intentar escanear un código de barras la cámara se abre pero nunca reconoce el código. En Android 12 y 13 funciona correctamente.',
                'severity': BugReport.SEVERITY_CRITICAL,
                'steps_to_reproduce': [
                    'Abrir la app en un dispositivo Android 14 (ej. Samsung Galaxy S23)',
                    'Navegar a Entradas → Nueva entrada',
                    'Tocar el ícono de escáner',
                    'Apuntar la cámara a un código de barras EAN-13',
                    'La cámara no reconoce el código indefinidamente',
                ],
                'expected_behavior': 'El sistema debería identificar el código en menos de 2 segundos y navegar al detalle del artículo.',
                'actual_behavior': 'La cámara permanece activa pero nunca lee el código. Solo se puede cerrar manualmente.',
                'environment': BugReport.ENV_STAGING,
                'device_browser': 'Samsung Galaxy S23 / Android 14',
                'is_recurring': True,
                'status': BugReport.STATUS_CONFIRMED,
                'admin_response': 'Confirmado en nuestros dispositivos de prueba. El problema está en el permiso de cámara en Android 14 que cambió su modelo de permisos. Actualizando el SDK.',
            },
            {
                'title': 'La sincronización con SAP no actualiza el stock en tiempo real',
                'description': 'Después de registrar una entrada en la app, el stock en SAP B1 no se refleja hasta después de varios minutos o hasta que se fuerza una sync manual.',
                'severity': BugReport.SEVERITY_HIGH,
                'steps_to_reproduce': [
                    'Registrar una entrada de 10 unidades del artículo COD-0042',
                    'Ir inmediatamente a SAP B1 y revisar el stock del artículo',
                    'El stock en SAP sigue mostrando la cantidad anterior',
                    'Esperar 15 minutos — el stock se actualiza eventualmente',
                ],
                'expected_behavior': 'El stock en SAP debería actualizarse en menos de 60 segundos tras registrar el movimiento.',
                'actual_behavior': 'La actualización toma entre 10 y 20 minutos. Durante ese tiempo los datos están desincronizados.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'App v0.1 / SAP B1 9.3',
                'is_recurring': True,
                'status': BugReport.STATUS_FIXING,
                'admin_response': 'El worker de sync está procesando en batch cada 15 minutos. Cambiando a sync inmediata por webhook para movimientos de entrada/salida.',
            },
            {
                'title': 'La app se cierra al escanear más de 20 artículos seguidos',
                'description': 'Durante el inventario físico, cuando un almacenista escanea más de 20 artículos de forma consecutiva la app se cierra inesperadamente y se pierde el conteo.',
                'severity': BugReport.SEVERITY_HIGH,
                'steps_to_reproduce': [
                    'Iniciar una sesión de conteo físico',
                    'Escanear artículos usando la cámara de forma continua',
                    'Aproximadamente en el escaneo 20-25 la app se cierra',
                    'Al reabrir, los artículos escaneados anteriormente no fueron guardados',
                ],
                'expected_behavior': 'La app debería manejar sesiones de escaneo prolongadas sin cerrarse. Los datos deben guardarse progresivamente.',
                'actual_behavior': 'La app se cierra (crash) alrededor del escaneo 20. Los datos de la sesión no persisten.',
                'environment': BugReport.ENV_STAGING,
                'device_browser': 'Motorola G Play / Android 12',
                'is_recurring': True,
                'status': BugReport.STATUS_REPORTED,
                'admin_response': '',
            },
            {
                'title': 'Alerta de stock mínimo aparece para artículos ya reabastecidos',
                'description': 'Después de registrar una entrada que lleva el stock por encima del mínimo, la notificación de stock bajo sigue apareciendo en el dashboard.',
                'severity': BugReport.SEVERITY_MEDIUM,
                'steps_to_reproduce': [
                    'Configurar artículo COD-0015 con stock mínimo de 5 unidades',
                    'Bajar el stock a 3 (debajo del mínimo) — aparece la alerta',
                    'Registrar una entrada de 20 unidades → stock queda en 23',
                    'El dashboard sigue mostrando la alerta de stock bajo para COD-0015',
                ],
                'expected_behavior': 'La alerta debería desaparecer automáticamente cuando el stock supera el umbral mínimo.',
                'actual_behavior': 'La alerta persiste aunque el stock ya esté por encima del mínimo. Solo desaparece al reiniciar la app.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Cualquier dispositivo',
                'is_recurring': False,
                'status': BugReport.STATUS_RESOLVED,
                'admin_response': 'El estado de la alerta no se recalculaba al registrar entradas. Corregido: ahora el listener de movimientos invalida las alertas activas cuando el stock supera el umbral.',
            },
            {
                'title': 'El historial de movimientos no carga con más de 500 registros',
                'description': 'Para artículos con mucha rotación (más de 500 movimientos), la pantalla de historial queda en estado de carga indefinido.',
                'severity': BugReport.SEVERITY_LOW,
                'steps_to_reproduce': [
                    'Navegar al artículo COD-0001 (alta rotación)',
                    'Tap en "Ver historial"',
                    'La pantalla muestra spinner de carga indefinidamente',
                    'Para artículos con menos de 100 movimientos la pantalla carga normalmente',
                ],
                'expected_behavior': 'El historial debería paginar y cargar en menos de 3 segundos independientemente del total de registros.',
                'actual_behavior': 'La API devuelve todos los movimientos en una sola respuesta. Con 500+ registros supera el tiempo de espera del cliente.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Todos los dispositivos',
                'is_recurring': True,
                'status': BugReport.STATUS_REPORTED,
                'admin_response': '',
            },
        ]

        for i, bug_data in enumerate(bugs):
            dlv = deliverable_list[i % len(deliverable_list)]
            bug = BugReport.objects.create(
                deliverable=dlv,
                reported_by=client_user,
                title=bug_data['title'],
                description=bug_data['description'],
                severity=bug_data['severity'],
                steps_to_reproduce=bug_data['steps_to_reproduce'],
                expected_behavior=bug_data['expected_behavior'],
                actual_behavior=bug_data['actual_behavior'],
                environment=bug_data['environment'],
                device_browser=bug_data.get('device_browser', ''),
                is_recurring=bug_data.get('is_recurring', False),
                status=bug_data['status'],
                admin_response=bug_data.get('admin_response', ''),
            )

            if bug_data['admin_response']:
                BugComment.objects.create(
                    bug_report=bug,
                    user=admin_user,
                    content=bug_data['admin_response'],
                    is_internal=False,
                )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(bugs)} bug reports for {project.name}'))
