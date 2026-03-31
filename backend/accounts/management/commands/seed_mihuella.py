"""
Seed Mi Huella demo project with realistic Kanban data.

Creates:
  - 1 client: Laura Blanco (laura@entre-especies.com / LauraEntre2026!)
  - 1 project: Mi Huella — Plataforma de Adopción Animal
  - 55 requirements distributed across backlog, todo, in_progress, in_review, done

Usage:
  python manage.py seed_mihuella
  python manage.py seed_mihuella --flush
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import (
    BugComment, BugReport, ChangeRequest, ChangeRequestComment,
    Deliverable, DeliverableVersion, HostingSubscription, Payment,
    Project, Requirement, UserProfile,
)

User = get_user_model()

CLIENT_EMAIL = 'laura@entre-especies.com'
CLIENT_PASSWORD = 'LauraEntre2026!'
PROJECT_NAME = 'Mi Huella — Plataforma de Adopción Animal'

# fmt: off
REQUIREMENTS = [
    # ── DONE (10) — Foundation & core auth ─────────────────────────────
    {"title": "Registro de usuario con email y contraseña", "description": "Pantalla de registro donde nuevos usuarios crean una cuenta proporcionando nombre, email y contraseña. Al registrarse, se asigna automáticamente el rol 'adopter'.", "configuration": "Todos los usuarios no autenticados (guests).", "flow": "Usuario abre /sign-up → completa nombre, email y contraseña → el sistema valida campos → crea cuenta con rol adopter → emite tokens JWT → redirige al home.", "priority": "critical", "status": "done"},
    {"title": "Inicio de sesión con email y contraseña", "description": "Pantalla de autenticación donde usuarios existentes inician sesión con sus credenciales de email y contraseña.", "configuration": "Todos los usuarios no autenticados.", "flow": "Usuario abre /sign-in → ingresa email y contraseña → click en Iniciar sesión → el sistema valida credenciales → emite tokens JWT → redirige al home.", "priority": "critical", "status": "done"},
    {"title": "Inicio de sesión con Google OAuth", "description": "Autenticación alternativa mediante cuenta de Google. Si el usuario no existe, se crea automáticamente con rol adopter.", "configuration": "Todos los usuarios no autenticados.", "flow": "Usuario abre /sign-in → click en 'Iniciar con Google' → flujo OAuth de Google → el sistema crea o vincula usuario → emite tokens JWT → redirige al home.", "priority": "critical", "status": "done"},
    {"title": "Recuperación de contraseña por email", "description": "Flujo de restablecimiento de contraseña mediante envío de código de verificación al email registrado del usuario.", "configuration": "Todos los usuarios registrados.", "flow": "Usuario abre /forgot-password → ingresa email → el sistema genera PasswordCode y envía email → usuario ingresa código → establece nueva contraseña → redirige a /sign-in.", "priority": "critical", "status": "done"},
    {"title": "Cierre de sesión", "description": "Permite al usuario cerrar su sesión activa, eliminando tokens de autenticación del navegador.", "configuration": "Todos los usuarios autenticados.", "flow": "Usuario click en 'Cerrar sesión' en menú de usuario → tokens eliminados de localStorage → redirige a /sign-in.", "priority": "critical", "status": "done"},
    {"title": "Persistencia de sesión con refresh de tokens", "description": "Renovación automática del token de acceso JWT cuando expira, permitiendo sesiones continuas sin re-autenticación.", "configuration": "Todos los usuarios autenticados.", "flow": "Token de acceso expira → interceptor Axios detecta 401 → envía refresh token → el sistema emite nuevos tokens → la solicitud original se reintenta automáticamente.", "priority": "critical", "status": "done"},
    {"title": "Redirección de rutas protegidas", "description": "Los usuarios no autenticados que intentan acceder a rutas protegidas son redirigidos automáticamente a la pantalla de inicio de sesión.", "configuration": "Usuarios no autenticados intentando acceder a rutas que requieren autenticación.", "flow": "Usuario no autenticado navega a ruta protegida → middleware detecta ausencia de token → redirige a /sign-in → tras login, redirige a la ruta original.", "priority": "critical", "status": "done"},
    {"title": "Página de inicio (landing)", "description": "Página principal de la plataforma con sección hero, carrusel de animales destacados, carrusel de campañas activas y spotlight de refugios.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario abre / → ve sección hero con CTA principal → navega carrusel de animales destacados → ve carrusel de campañas activas → ve spotlight de refugio → puede navegar a cualquier sección desde los CTAs.", "priority": "high", "status": "done"},
    {"title": "Navegación principal (header)", "description": "Barra de navegación con enlaces a secciones principales, selector de idioma, campana de notificaciones, toggle de tema y menú de usuario.", "configuration": "Visible para todos los usuarios. Menú de usuario y notificaciones solo para autenticados.", "flow": "Usuario ve header → links visibles: Animales, Refugios, Campañas, Busco Adoptar, Blog → click para navegar → si autenticado: ve campana de notificaciones y menú de usuario.", "priority": "high", "status": "done"},
    {"title": "Menú móvil responsive", "description": "Navegación adaptada para dispositivos móviles con menú hamburguesa que despliega sidebar con todos los enlaces.", "configuration": "Todos los usuarios en dispositivos móviles.", "flow": "Usuario en móvil → click en ícono hamburguesa → sidebar se despliega con todos los enlaces de navegación → click en enlace → navega y sidebar se cierra.", "priority": "medium", "status": "done"},

    # ── IN REVIEW / APROBACIÓN (5) — Ready for QA ─────────────────────
    {"title": "Catálogo de animales con filtros", "description": "Listado paginado de todos los animales disponibles para adopción, con filtros por especie, tamaño, edad y género.", "configuration": "Visible para todos los usuarios (autenticados y guests).", "flow": "Usuario navega a /animales → ve grid de tarjetas de animales → aplica filtros (perro/gato, pequeño/mediano/grande, cachorro/joven/adulto, macho/hembra) → resultados se actualizan en tiempo real.", "priority": "high", "status": "in_review"},
    {"title": "Detalle de animal con galería", "description": "Página de perfil completo del animal mostrando nombre, descripción, historial médico, necesidades especiales, galería de imágenes y CTAs de adopción/apadrinamiento.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario click en tarjeta de animal → navega a /animales/{id} → ve información completa → puede recorrer galería (Swiper) → ve botones de Adoptar, Apadrinar y Donar.", "priority": "high", "status": "in_review"},
    {"title": "Directorio de refugios", "description": "Listado público de todos los refugios verificados en la plataforma con tarjetas informativas.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario navega a /refugios → ve grid de tarjetas de refugios (nombre, logo, ubicación) → click en refugio → navega a perfil del refugio.", "priority": "high", "status": "in_review"},
    {"title": "Perfil público del refugio", "description": "Página de detalle del refugio mostrando información completa, galería, animales disponibles y campañas activas.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario click en refugio → ve /refugios/{id} → ve descripción, galería, contacto → sección de animales del refugio → sección de campañas activas.", "priority": "high", "status": "in_review"},
    {"title": "Modo oscuro/claro", "description": "Toggle de tema visual que permite alternar entre modo oscuro y modo claro en toda la aplicación.", "configuration": "Todos los usuarios.", "flow": "Usuario click en toggle de tema en header → toda la aplicación cambia a modo oscuro/claro → preferencia persistida.", "priority": "low", "status": "in_review"},

    # ── IN PROGRESS (8) — Actively being developed ────────────────────
    {"title": "Formulario de solicitud de adopción (wizard)", "description": "Formulario de adopción en 3 pasos con 6 preguntas por sección, cubriendo información personal, hogar/estilo de vida, y revisión final antes de enviar.", "configuration": "Solo usuarios autenticados con rol adopter. Requiere seleccionar un animal específico.", "flow": "Usuario en detalle de animal → click 'Adoptar' → Paso 1: info personal (6 preguntas) → Paso 2: hogar y estilo de vida (6 preguntas) → Paso 3: revisión y confirmación → envía → solicitud creada con status 'submitted'.", "priority": "high", "status": "in_progress"},
    {"title": "Seguimiento de solicitudes de adopción", "description": "Pantalla donde el adoptante ve todas sus solicitudes de adopción con su estado actual (enviada, en revisión, entrevista, aprobada, rechazada).", "configuration": "Solo usuarios autenticados con rol adopter.", "flow": "Usuario navega a /mis-solicitudes → ve lista de solicitudes con nombre del animal, fecha y badge de estado → puede click en cada una para ver detalles.", "priority": "high", "status": "in_progress"},
    {"title": "Listado de campañas de donación", "description": "Página con todas las campañas de recaudación activas y completadas, mostrando progreso de cada una.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario navega a /campanas → ve tarjetas con título, barra de progreso, meta y monto recaudado → puede alternar entre pestañas Activas/Completadas.", "priority": "high", "status": "in_progress"},
    {"title": "Detalle de campaña con progreso", "description": "Página completa de una campaña mostrando descripción, meta, monto recaudado, porcentaje de progreso y CTA para donar.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario click en campaña → ve /campanas/{id} → ve descripción completa, barra de progreso, porcentaje, galería de evidencia → click en 'Donar'.", "priority": "high", "status": "in_progress"},
    {"title": "Checkout de donación", "description": "Flujo de pago para realizar una donación a un refugio o campaña específica, con montos preestablecidos y método de pago.", "configuration": "Solo usuarios autenticados con rol adopter.", "flow": "Usuario navega a /checkout/donacion → selecciona monto → elige método de pago (tarjeta/PSE/Nequi) → agrega mensaje opcional → confirma → pago procesado vía Wompi → redirige a confirmación.", "priority": "high", "status": "in_progress"},
    {"title": "Integración de pagos con Wompi", "description": "Procesamiento de pagos mediante la pasarela colombiana Wompi, soportando tarjeta de crédito, PSE y Nequi como métodos de pago.", "configuration": "Usuarios autenticados que realizan donaciones o apadrinamientos. Requiere configuración de API keys de Wompi.", "flow": "Usuario en checkout → selecciona método de pago → sistema crea payment intent vía Wompi API → usuario completa pago en widget → webhook de Wompi confirma transacción.", "priority": "critical", "status": "in_progress"},
    {"title": "Registro de refugio (onboarding)", "description": "Formulario de registro para organizaciones de refugio que desean publicar animales en la plataforma. El refugio queda en estado pendiente de verificación.", "configuration": "Usuarios autenticados con rol shelter_admin.", "flow": "Shelter admin navega a /refugio/onboarding → completa formulario (nombre, logo, cover, ubicación, descripción, contacto) → envía → Shelter creado con verification_status=pending.", "priority": "high", "status": "in_progress"},
    {"title": "Gestión de animales del refugio (CRUD)", "description": "Panel completo para crear, ver, editar y archivar animales del refugio, incluyendo carga de galería de imágenes.", "configuration": "Solo usuarios con rol shelter_admin del refugio correspondiente.", "flow": "Shelter admin navega a /refugio/animales → ve lista paginada con filtros → click 'Crear' → completa formulario con galería drag-drop → guarda → animal publicado.", "priority": "high", "status": "in_progress"},

    # ── TODO (12) — Planned for next sprints ───────────────────────────
    {"title": "Marcar animal como favorito", "description": "Permite a usuarios autenticados guardar animales en su lista de favoritos mediante un ícono de corazón.", "configuration": "Solo usuarios autenticados con rol adopter.", "flow": "Usuario autenticado → click en ícono de corazón en tarjeta o detalle de animal → favorito creado en BD → ícono cambia a lleno → animal aparece en /favoritos.", "priority": "medium", "status": "todo"},
    {"title": "Lista de animales favoritos", "description": "Página dedicada donde el usuario ve todos los animales que ha marcado como favoritos.", "configuration": "Solo usuarios autenticados con rol adopter.", "flow": "Usuario navega a /favoritos → ve grid con todos los animales favoritos → puede click en cualquiera para ver detalle → puede quitar favorito.", "priority": "medium", "status": "todo"},
    {"title": "Revisión de solicitudes por refugio", "description": "Panel donde el administrador del refugio revisa las solicitudes de adopción recibidas y puede cambiar su estado.", "configuration": "Solo usuarios con rol shelter_admin, limitado a solicitudes de animales de su refugio.", "flow": "Shelter admin navega a /refugio/solicitudes → ve lista de solicitudes → click en una → ve info del solicitante y respuestas → selecciona nuevo estado → guarda.", "priority": "high", "status": "todo"},
    {"title": "Confirmación de pago", "description": "Página de confirmación mostrada después de un pago exitoso, con resumen del recibo.", "configuration": "Solo usuarios autenticados que acaban de completar un pago.", "flow": "Usuario completa checkout → sistema procesa pago → redirige a /checkout/confirmation → ve mensaje de agradecimiento con detalles (monto, destinatario, fecha, referencia).", "priority": "high", "status": "todo"},
    {"title": "Checkout de apadrinamiento", "description": "Flujo de pago para apadrinar un animal con opción de frecuencia mensual o única, selección de monto y método de pago.", "configuration": "Solo usuarios autenticados con rol adopter.", "flow": "Usuario navega a /checkout/apadrinamiento → selecciona animal → elige frecuencia → selecciona monto → elige método de pago → confirma → Sponsorship y Payment creados.", "priority": "high", "status": "todo"},
    {"title": "Dashboard del panel de refugio", "description": "Panel de navegación central para administradores de refugio con accesos directos a todas las secciones de gestión.", "configuration": "Solo usuarios con rol shelter_admin.", "flow": "Shelter admin navega a /refugio → ve dashboard con enlaces a: animales, solicitudes, campañas, donaciones, updates, configuración.", "priority": "high", "status": "todo"},
    {"title": "Gestión de campañas del refugio", "description": "Panel para crear y administrar campañas de recaudación de fondos del refugio, con seguimiento de progreso.", "configuration": "Solo usuarios con rol shelter_admin del refugio correspondiente.", "flow": "Shelter admin navega a /refugio/campanas → ve campañas activas y completadas → click 'Crear' → completa formulario → publica → ve progreso de recaudación.", "priority": "high", "status": "todo"},
    {"title": "Dashboard de administración de plataforma", "description": "Panel principal del administrador con métricas resumidas: total de usuarios, refugios, animales, solicitudes, donaciones y apadrinamientos.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/dashboard → ve tarjetas resumen con KPIs de la plataforma.", "priority": "high", "status": "todo"},
    {"title": "Aprobación y verificación de refugios", "description": "Cola de aprobación donde el administrador revisa y aprueba o rechaza refugios que se han registrado en la plataforma.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/refugios/aprobar → ve lista de refugios con status pending → click en refugio → revisa información → click Aprobar o Rechazar.", "priority": "high", "status": "todo"},
    {"title": "Cambio de idioma (español/inglés)", "description": "Selector de idioma en el header que permite cambiar toda la interfaz entre español e inglés usando next-intl.", "configuration": "Todos los usuarios.", "flow": "Usuario click en toggle ES/EN en header → toda la página se re-renderiza en el idioma seleccionado → preferencia guardada.", "priority": "medium", "status": "todo"},
    {"title": "Campana de notificaciones con contador", "description": "Ícono de campana en el header que muestra la cantidad de notificaciones no leídas y un dropdown con las más recientes.", "configuration": "Todos los usuarios autenticados.", "flow": "Usuario ve ícono de campana con badge numérico → click → se despliega dropdown con 5 notificaciones recientes → puede marcar todas como leídas.", "priority": "medium", "status": "todo"},
    {"title": "Listado de posts del blog (público)", "description": "Página pública del blog con listado de artículos publicados, imagen destacada, título, extracto y fecha.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario navega a /blog → ve lista de posts publicados con imagen, título, extracto, autor y fecha → puede filtrar por categoría → click en post para leer.", "priority": "medium", "status": "todo"},

    # ── BACKLOG (20) — Not yet planned ─────────────────────────────────
    {"title": "Historial de donaciones del usuario", "description": "Página donde el usuario ve todas las donaciones que ha realizado, con monto, destinatario y fecha.", "configuration": "Solo usuarios autenticados con rol adopter.", "flow": "Usuario navega a /mis-donaciones → ve lista cronológica de donaciones (monto, refugio/campaña, fecha, estado).", "priority": "medium", "status": "backlog"},
    {"title": "Lista de apadrinamientos activos", "description": "Página donde el usuario ve todos sus apadrinamientos activos con animal, monto, frecuencia y estado de suscripción.", "configuration": "Solo usuarios autenticados con rol adopter.", "flow": "Usuario navega a /mis-apadrinamientos → ve lista de apadrinamientos (animal, monto, frecuencia, próximo cobro).", "priority": "medium", "status": "backlog"},
    {"title": "Gestión de suscripción de apadrinamiento", "description": "Permite pausar, reanudar o cancelar un apadrinamiento mensual activo.", "configuration": "Solo usuarios autenticados con rol adopter que tienen apadrinamientos mensuales activos.", "flow": "Usuario en /mis-apadrinamientos → click en apadrinamiento → ve opciones de gestión → click Pausar/Reanudar/Cancelar → confirma acción.", "priority": "medium", "status": "backlog"},
    {"title": "Crear/actualizar intención de adopción", "description": "Perfil de preferencias de adopción donde el usuario publica qué tipo de animal busca, permitiendo que refugios lo descubran.", "configuration": "Solo usuarios autenticados con rol adopter.", "flow": "Usuario navega a /mi-intencion → selecciona preferencias (especie, tamaño, edad) → agrega descripción → elige visibilidad → guarda.", "priority": "medium", "status": "backlog"},
    {"title": "Explorar intenciones de adopción públicas", "description": "Listado de adoptantes que han publicado sus preferencias de adopción, permitiendo a refugios descubrir posibles adoptantes.", "configuration": "Visible para todos los usuarios autenticados.", "flow": "Usuario navega a /busco-adoptar → ve tarjetas de adoptantes con sus preferencias → puede filtrar por tipo de animal.", "priority": "medium", "status": "backlog"},
    {"title": "Enviar invitación a adoptante desde refugio", "description": "Permite al administrador de un refugio invitar a un adoptante interesado a conocer los animales del refugio.", "configuration": "Solo usuarios con rol shelter_admin.", "flow": "Shelter admin en /busco-adoptar → ve intención de adoptante → click 'Enviar invitación' → ShelterInvite creado → notificación enviada.", "priority": "medium", "status": "backlog"},
    {"title": "Gestión de perfil de usuario", "description": "Pantalla donde el usuario puede ver y editar su información personal (nombre, ciudad, avatar).", "configuration": "Todos los usuarios autenticados.", "flow": "Usuario navega a /mi-perfil → ve información actual → edita nombre, ciudad o avatar → click Guardar → datos actualizados.", "priority": "medium", "status": "backlog"},
    {"title": "Preferencias de notificaciones", "description": "Pantalla donde el usuario configura qué notificaciones desea recibir por email y/o en la aplicación.", "configuration": "Todos los usuarios autenticados.", "flow": "Usuario navega a /my-profile/notifications → ve lista de eventos → activa/desactiva canal email e in-app por evento → guarda.", "priority": "low", "status": "backlog"},
    {"title": "Configuración del perfil del refugio", "description": "Pantalla de ajustes donde el administrador del refugio puede actualizar la información de su organización.", "configuration": "Solo usuarios con rol shelter_admin del refugio correspondiente.", "flow": "Shelter admin navega a /refugio/configuracion → edita nombre, descripción, logo, cover, contacto → guarda.", "priority": "medium", "status": "backlog"},
    {"title": "Vista de donaciones recibidas por refugio", "description": "Listado de todas las donaciones recibidas por el refugio, con detalle de donante, monto y fecha.", "configuration": "Solo usuarios con rol shelter_admin del refugio correspondiente.", "flow": "Shelter admin navega a /refugio/donaciones → ve tabla de donaciones (monto, donante, fecha, campaña asociada).", "priority": "medium", "status": "backlog"},
    {"title": "Publicar post de actualización del refugio", "description": "Permite al refugio publicar actualizaciones sobre animales o campañas para mantener informados a donantes y adoptantes.", "configuration": "Solo usuarios con rol shelter_admin del refugio correspondiente.", "flow": "Shelter admin navega a /refugio/updates → click 'Crear' → completa formulario → publica → post visible públicamente.", "priority": "medium", "status": "backlog"},
    {"title": "Editar post de actualización del refugio", "description": "Permite modificar un post de actualización previamente publicado por el refugio.", "configuration": "Solo usuarios con rol shelter_admin del refugio correspondiente.", "flow": "Shelter admin navega a /refugio/updates → click en post existente → edita contenido → guarda.", "priority": "low", "status": "backlog"},
    {"title": "Lectura de artículo del blog", "description": "Página de detalle de un post del blog con contenido completo, barra de progreso de lectura, bio del autor y botones de compartir.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario click en post → ve /blog/{slug} → lee contenido completo → barra de progreso indica avance → ve bio del autor → puede compartir.", "priority": "medium", "status": "backlog"},
    {"title": "Administración de posts del blog (CRUD)", "description": "Panel de administración del blog para crear, editar, duplicar y gestionar artículos con contenido JSON, categorías, SEO y soporte bilingüe.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/blog → ve lista de posts → click 'Crear' → completa formulario → publica o guarda como borrador.", "priority": "medium", "status": "backlog"},
    {"title": "Calendario editorial del blog", "description": "Vista de calendario mensual que muestra la distribución de publicaciones del blog, con conteo por día y colores por estado.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/blog/calendario → ve calendario mensual → cada día muestra cantidad de posts → click en día para ver/crear.", "priority": "low", "status": "backlog"},
    {"title": "Métricas detalladas de la plataforma", "description": "Panel analítico con estadísticas financieras y de adopción: tasa de adopción, totales de donación, ingresos por mes/refugio.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/metricas → ve gráficos y tablas con: tasa de adopción, totales de donaciones, apadrinamientos recurrentes.", "priority": "medium", "status": "backlog"},
    {"title": "Moderación de contenido publicado", "description": "Vista de moderación donde el administrador revisa animales, posts de actualización y posts de blog para detectar contenido inapropiado.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/moderacion → ve contenido publicado → items flaggeados resaltados → puede tomar acción.", "priority": "high", "status": "backlog"},
    {"title": "Auditoría de pagos", "description": "Tabla completa de todos los pagos procesados en la plataforma con fuente, estado y detalles de transacción.", "configuration": "Solo usuarios con rol admin.", "flow": "Admin navega a /admin/pagos → ve tabla con: ID de pago, monto, fuente, refugio, usuario, fecha, estado.", "priority": "high", "status": "backlog"},
    {"title": "Página de preguntas frecuentes (FAQ)", "description": "Página con preguntas frecuentes organizadas por temas en formato acordeón expandible.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario navega a /faq → ve temas organizados → click en pregunta → respuesta se expande en acordeón.", "priority": "low", "status": "backlog"},
    {"title": "Páginas institucionales", "description": "Páginas estáticas de Acerca de nosotros, Términos y condiciones, Trabaja con nosotros y Aliados estratégicos.", "configuration": "Visible para todos los usuarios.", "flow": "Usuario navega a la página correspondiente desde el footer → lee contenido informativo.", "priority": "low", "status": "backlog"},
]
# fmt: on


class Command(BaseCommand):
    help = 'Seed Mi Huella demo project with Laura Blanco as client.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Remove existing Laura Blanco seed data first.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        admin = self._get_admin()
        client = self._create_client()
        project = self._create_project(client)
        self._create_requirements(project)
        self._create_change_requests(project, client, admin)
        self._create_bug_reports(project, client, admin)
        self._create_deliverables(project, admin)
        self._create_subscription(project)

        # Compute progress from statuses
        req_qs = Requirement.objects.filter(deliverable__project=project)
        total = req_qs.count()
        done = req_qs.filter(status=Requirement.STATUS_DONE).count()
        project.progress = round((done / total) * 100) if total else 0
        project.save(update_fields=['progress'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Mi Huella seed data created:'))
        self.stdout.write(f'  Client  → {CLIENT_EMAIL} / {CLIENT_PASSWORD}')
        self.stdout.write(f'  Project → {PROJECT_NAME}')

        for status, label in Requirement.STATUS_CHOICES:
            count = req_qs.filter(status=status).count()
            self.stdout.write(f'    {label:<15} {count}')

        self.stdout.write(f'  Progress         → {project.progress}%')
        self.stdout.write(f'  Change requests  → {ChangeRequest.objects.filter(project=project).count()}')
        self.stdout.write(f'  Bug reports      → {BugReport.objects.filter(project=project).count()}')
        self.stdout.write(f'  Deliverables     → {Deliverable.objects.filter(project=project).count()}')
        self.stdout.write(f'  Subscription     → {HostingSubscription.objects.filter(project=project).count()}')
        self.stdout.write('')

    def _get_admin(self):
        admin_profile = UserProfile.objects.filter(role=UserProfile.ROLE_ADMIN).first()
        return admin_profile.user if admin_profile else None

    def _flush(self):
        user = User.objects.filter(email=CLIENT_EMAIL).first()
        if user:
            Project.objects.filter(client=user).delete()
            user.delete()
            self.stdout.write(f'  Deleted existing user: {CLIENT_EMAIL}')

    def _create_client(self):
        if User.objects.filter(email=CLIENT_EMAIL).exists():
            self.stdout.write(f'  Client already exists: {CLIENT_EMAIL}')
            return User.objects.get(email=CLIENT_EMAIL)

        user = User.objects.create_user(
            username=CLIENT_EMAIL,
            email=CLIENT_EMAIL,
            password=CLIENT_PASSWORD,
            first_name='Laura',
            last_name='Blanco',
        )
        UserProfile.objects.create(
            user=user,
            role=UserProfile.ROLE_CLIENT,
            is_onboarded=True,
            profile_completed=True,
            company_name='Entre Especies',
            phone='+57 315 420 8899',
            cedula='1098765432',
            date_of_birth='1994-08-22',
            gender=UserProfile.GENDER_FEMALE,
            education_level=UserProfile.EDUCATION_UNIVERSITY,
        )
        self.stdout.write(self.style.SUCCESS(f'  Created client: {CLIENT_EMAIL}'))
        return user

    def _create_project(self, client):
        existing = Project.objects.filter(client=client, name=PROJECT_NAME).first()
        if existing:
            self.stdout.write(f'  Project already exists: {PROJECT_NAME}')
            return existing

        today = date.today()
        project = Project.objects.create(
            name=PROJECT_NAME,
            description=(
                'Plataforma web de adopción y apadrinamiento de animales de refugio. '
                'Incluye catálogo de animales, sistema de solicitudes de adopción, '
                'campañas de donación con pasarela Wompi, panel de refugios, '
                'blog, y panel de administración con métricas.'
            ),
            client=client,
            status=Project.STATUS_ACTIVE,
            progress=0,
            start_date=today - timedelta(days=45),
            estimated_end_date=today + timedelta(days=90),
        )
        self.stdout.write(self.style.SUCCESS(f'  Created project: {PROJECT_NAME}'))
        return project

    def _create_requirements(self, project):
        if Requirement.objects.filter(deliverable__project=project).exists():
            self.stdout.write(f'  Requirements already exist for {project.name}')
            return

        d = Deliverable.objects.filter(project=project).order_by('id').first()
        if not d:
            d = Deliverable.objects.create(
                project=project,
                title='Alcance Mi Huella',
                category=Deliverable.CATEGORY_OTHER,
                file=None,
                uploaded_by=project.client,
            )

        order_counters = {}
        objs = []
        for req_data in REQUIREMENTS:
            status = req_data['status']
            order_counters.setdefault(status, 0)
            objs.append(Requirement(
                deliverable=d,
                title=req_data['title'],
                description=req_data.get('description', ''),
                configuration=req_data.get('configuration', ''),
                flow=req_data.get('flow', ''),
                status=status,
                priority=req_data.get('priority', 'medium'),
                order=order_counters[status],
            ))
            order_counters[status] += 1

        Requirement.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS(f'  Created {len(objs)} requirements'))

    def _create_change_requests(self, project, client, admin):
        if ChangeRequest.objects.filter(project=project).exists():
            self.stdout.write(f'  Change requests already exist for {project.name}')
            return

        crs = [
            {
                'title': 'Agregar filtro por raza en el catálogo de animales',
                'description': 'Los adoptantes nos piden poder filtrar no solo por especie y tamaño, sino también por raza. Por ejemplo: Labrador, Siamés, Mestizo.',
                'module_or_screen': 'Catálogo de animales',
                'suggested_priority': 'high',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_APPROVED,
                'admin_response': 'Tiene sentido. Agregaremos un campo "breed" al modelo Animal y un filtro adicional. Estimamos 3 días.',
                'estimated_cost': 0,
                'estimated_time': '3 días',
            },
            {
                'title': 'Botón de compartir perfil de animal en redes sociales',
                'description': 'Queremos que desde la ficha de cada animal se pueda compartir directamente en WhatsApp, Instagram y Facebook con una imagen preview.',
                'module_or_screen': 'Detalle de animal',
                'suggested_priority': 'medium',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_EVALUATING,
                'admin_response': '',
            },
            {
                'title': 'Notificación push cuando un animal que favoritó es adoptado',
                'description': 'Si un usuario tiene un animal en favoritos y ese animal es adoptado, debería recibir una notificación amigable tipo "¡Loki encontró hogar!" y una sugerencia de animales similares.',
                'module_or_screen': 'Notificaciones',
                'suggested_priority': 'medium',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_PENDING,
                'admin_response': '',
            },
            {
                'title': 'Galería de "antes y después" para animales adoptados',
                'description': 'Los adoptantes quieren subir fotos del animal ya en su nuevo hogar. Sería una sección en el perfil del animal mostrando su progreso.',
                'module_or_screen': 'Perfil de animal',
                'suggested_priority': 'low',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_REJECTED,
                'admin_response': 'Es una idea muy bonita pero implica un módulo completo de UGC (user generated content) con moderación. Lo evaluaremos para la fase 2 del proyecto.',
            },
            {
                'title': 'Recibo de donación descargable en PDF para declaración de renta',
                'description': 'En Colombia las donaciones a fundaciones son deducibles de impuestos. Los donantes necesitan un recibo formal en PDF con NIT del refugio y monto.',
                'module_or_screen': 'Historial de donaciones',
                'suggested_priority': 'high',
                'is_urgent': True,
                'status': ChangeRequest.STATUS_NEEDS_CLARIFICATION,
                'admin_response': '¿Cada refugio tiene su propio NIT o usamos el NIT de la fundación paraguas?',
            },
            {
                'title': 'Mapa interactivo con ubicación de refugios',
                'description': 'En el directorio de refugios, además de la lista, queremos un mapa tipo Google Maps donde se vean los pins de cada refugio verificado.',
                'module_or_screen': 'Directorio de refugios',
                'suggested_priority': 'medium',
                'is_urgent': False,
                'status': ChangeRequest.STATUS_APPROVED,
                'admin_response': 'Integraremos Leaflet (open source) con los datos de ubicación. Estimamos 4 días incluyendo la geocodificación.',
                'estimated_cost': 0,
                'estimated_time': '4 días',
            },
        ]

        for cr_data in crs:
            cr = ChangeRequest.objects.create(
                project=project,
                created_by=client,
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
            if cr_data.get('admin_response') and admin:
                ChangeRequestComment.objects.create(
                    change_request=cr,
                    user=admin,
                    content=cr_data['admin_response'],
                    is_internal=False,
                )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(crs)} change requests'))

    def _create_bug_reports(self, project, client, admin):
        if BugReport.objects.filter(project=project).exists():
            self.stdout.write(f'  Bug reports already exist for {project.name}')
            return

        bugs = [
            {
                'title': 'Galería del animal no carga en Safari iOS',
                'description': 'En iPhones con Safari, las imágenes del Swiper de la galería del animal se quedan en blanco. Solo aparece el placeholder.',
                'severity': BugReport.SEVERITY_CRITICAL,
                'steps_to_reproduce': [
                    'Abrir /animales/15 desde un iPhone con Safari',
                    'Esperar a que cargue la página de detalle',
                    'La galería muestra un cuadro gris vacío',
                    'Deslizar no muestra más imágenes',
                ],
                'expected_behavior': 'La galería debería mostrar todas las fotos del animal con el carrusel funcional.',
                'actual_behavior': 'Las imágenes no cargan. Solo se ve el placeholder gris.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'iPhone 13 / Safari 17.2',
                'is_recurring': True,
                'status': BugReport.STATUS_FIXING,
                'admin_response': 'Confirmado. El problema es la carga lazy de imágenes con IntersectionObserver en Safari. Estamos implementando un polyfill.',
            },
            {
                'title': 'Filtro de tamaño "grande" muestra animales pequeños',
                'description': 'Al filtrar por tamaño "grande" en el catálogo, aparecen gatos y perros que claramente son pequeños o medianos.',
                'severity': BugReport.SEVERITY_HIGH,
                'steps_to_reproduce': [
                    'Ir a /animales',
                    'Seleccionar filtro Tamaño → Grande',
                    'Aparece "Luna" (gata siamés, 3kg) que es claramente pequeña',
                ],
                'expected_behavior': 'Solo deberían aparecer animales clasificados como "grande".',
                'actual_behavior': 'Mezcla animales de todos los tamaños. Parece que el filtro no está aplicando bien.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Chrome 121 / macOS',
                'is_recurring': True,
                'status': BugReport.STATUS_CONFIRMED,
                'admin_response': 'El campo size de algunos animales fue ingresado como "large" y otros como "gran" (en español). Necesitamos normalizar la data y validar el input en el form del refugio.',
            },
            {
                'title': 'Donación se cobra dos veces al dar doble click',
                'description': 'Un donante reportó que al hacer doble click rápido en "Confirmar donación" se le cobró el monto duplicado. Aparecen 2 transacciones en Wompi.',
                'severity': BugReport.SEVERITY_CRITICAL,
                'steps_to_reproduce': [
                    'Ir a /checkout/donacion',
                    'Seleccionar monto de $50.000',
                    'Completar datos de tarjeta',
                    'Hacer doble click rápido en "Confirmar donación"',
                    'Se procesan 2 cobros de $50.000',
                ],
                'expected_behavior': 'Solo se debería procesar un cobro. El botón debería deshabilitarse al primer click.',
                'actual_behavior': 'Se procesan dos cobros. No hay protección contra double-submit.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Chrome / Windows',
                'is_recurring': False,
                'status': BugReport.STATUS_REPORTED,
                'admin_response': '',
            },
            {
                'title': 'Email de confirmación de solicitud llega con caracteres raros',
                'description': 'El email que recibe el adoptante después de enviar la solicitud muestra "Â¡" en lugar de "¡" y otros caracteres mal codificados.',
                'severity': BugReport.SEVERITY_MEDIUM,
                'steps_to_reproduce': [
                    'Completar el formulario de solicitud de adopción',
                    'Enviar la solicitud',
                    'Revisar el email de confirmación en Gmail',
                    'El asunto dice "Â¡Solicitud recibida!" en vez de "¡Solicitud recibida!"',
                ],
                'expected_behavior': 'El email debería mostrar caracteres en español correctamente.',
                'actual_behavior': 'Caracteres UTF-8 mal codificados (mojibake).',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Gmail web',
                'is_recurring': True,
                'status': BugReport.STATUS_RESOLVED,
                'admin_response': 'El template del email no tenía el header charset UTF-8. Corregido y desplegado.',
            },
            {
                'title': 'Página de campaña muestra 0% aunque ya tiene donaciones',
                'description': 'La campaña "Esterilización masiva Soacha" tiene $2.300.000 recaudados pero la barra de progreso muestra 0% y $0.',
                'severity': BugReport.SEVERITY_HIGH,
                'steps_to_reproduce': [
                    'Ir a /campanas',
                    'Click en la campaña "Esterilización masiva Soacha"',
                    'La barra muestra 0% y monto recaudado $0',
                    'Pero en el admin se ven 12 donaciones asociadas',
                ],
                'expected_behavior': 'Debería mostrar $2.300.000 / $5.000.000 (46%).',
                'actual_behavior': 'Muestra 0%. Parece que el campo total_raised no se recalcula.',
                'environment': BugReport.ENV_PRODUCTION,
                'device_browser': 'Cualquier navegador',
                'is_recurring': True,
                'status': BugReport.STATUS_FIXING,
                'admin_response': 'El campo total_raised es calculado pero el signal de post_save en Donation no está disparando la actualización. Lo estamos corrigiendo.',
            },
        ]

        for bug_data in bugs:
            bug = BugReport.objects.create(
                project=project,
                reported_by=client,
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
            if bug_data.get('admin_response') and admin:
                BugComment.objects.create(
                    bug_report=bug,
                    user=admin,
                    content=bug_data['admin_response'],
                    is_internal=False,
                )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(bugs)} bug reports'))

    def _create_deliverables(self, project, admin):
        if Deliverable.objects.filter(project=project).exists():
            self.stdout.write(f'  Deliverables already exist for {project.name}')
            return

        if not admin:
            self.stdout.write('  Skipping deliverables (no admin user found)')
            return

        from django.core.files.base import ContentFile

        deliverables = [
            {
                'title': 'Wireframes UX — Flujo de adopción',
                'description': 'Wireframes de baja fidelidad para el wizard de solicitud de adopción (3 pasos) y la pantalla de seguimiento.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'wireframes-adopcion-flow-v1.pdf',
            },
            {
                'title': 'Diseño UI — Catálogo y detalle de animal',
                'description': 'Mockups finales en Figma exportados a PDF. Incluye versión desktop y mobile del catálogo, tarjetas y página de detalle con galería.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'ui-catalogo-animal-v2.pdf',
            },
            {
                'title': 'Guía de marca Mi Huella',
                'description': 'Brandbook con logo, paleta de colores, tipografías, iconografía y tono de voz aprobados por Laura.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'mi-huella-brandbook-v1.pdf',
            },
            {
                'title': 'Credenciales Wompi Sandbox',
                'description': 'Llaves de API para pruebas en sandbox de la pasarela de pagos Wompi. Incluye public key, events secret y URL de webhooks configurada.',
                'category': Deliverable.CATEGORY_CREDENTIALS,
                'filename': 'wompi-sandbox-keys.txt',
            },
            {
                'title': 'Manual de administración de refugios',
                'description': 'Guía paso a paso para shelter_admins: cómo crear animales, gestionar campañas, responder solicitudes y publicar updates.',
                'category': Deliverable.CATEGORY_DOCUMENTS,
                'filename': 'manual-shelter-admin-v1.pdf',
            },
            {
                'title': 'Diagrama de arquitectura del sistema',
                'description': 'Diagrama con la arquitectura técnica: Next.js frontend, Django API, PostgreSQL, Redis, Wompi webhooks, Cloudinary para imágenes.',
                'category': Deliverable.CATEGORY_DOCUMENTS,
                'filename': 'arquitectura-mihuella-v1.pdf',
            },
        ]

        for d_data in deliverables:
            placeholder = ContentFile(b'placeholder content', name=d_data['filename'])
            d = Deliverable.objects.create(
                project=project,
                uploaded_by=admin,
                title=d_data['title'],
                description=d_data['description'],
                category=d_data['category'],
                file=placeholder,
                current_version=1,
            )
            DeliverableVersion.objects.create(
                deliverable=d,
                file=placeholder,
                version_number=1,
                uploaded_by=admin,
            )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(deliverables)} deliverables'))

    def _create_subscription(self, project):
        if HostingSubscription.objects.filter(project=project).exists():
            self.stdout.write(f'  Subscription already exists for {project.name}')
            return

        today = date.today()

        sub = HostingSubscription.objects.create(
            project=project,
            plan=HostingSubscription.PLAN_QUARTERLY,
            base_monthly_amount=Decimal('280000'),
            discount_percent=10,
            effective_monthly_amount=Decimal('252000'),
            billing_amount=Decimal('756000'),
            status=HostingSubscription.STATUS_ACTIVE,
            start_date=today - timedelta(days=45),
            next_billing_date=today + timedelta(days=45),
        )

        # First quarter — paid
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting trimestral — {project.name}',
            billing_period_start=today - timedelta(days=45),
            billing_period_end=today + timedelta(days=44),
            due_date=today - timedelta(days=45),
            status=Payment.STATUS_PAID,
            paid_at=timezone.now() - timedelta(days=43),
        )

        # Next quarter — pending
        Payment.objects.create(
            subscription=sub,
            amount=sub.billing_amount,
            description=f'Hosting trimestral — {project.name}',
            billing_period_start=today + timedelta(days=45),
            billing_period_end=today + timedelta(days=134),
            due_date=today + timedelta(days=45),
            status=Payment.STATUS_PENDING,
        )

        self.stdout.write(self.style.SUCCESS(f'  Created subscription + 2 payments'))
