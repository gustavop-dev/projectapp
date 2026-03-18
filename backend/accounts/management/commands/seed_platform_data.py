"""
Seed the platform with demo data for development.

Creates:
  - 1 admin user (admin@projectapp.dev / Admin1234!)
  - 1 onboarded client (maria@techstartup.co / Client1234!)
  - 2 demo projects for the client

Usage:
  python manage.py seed_platform_data
  python manage.py seed_platform_data --flush   # removes previous seed data first
"""

import os
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import BugComment, BugReport, ChangeRequest, ChangeRequestComment, Deliverable, Project, Requirement, UserProfile

User = get_user_model()

ADMIN_EMAIL = 'admin@projectapp.dev'
CLIENT_EMAIL = 'maria@techstartup.co'

ADMIN_PASSWORD = os.environ.get('SEED_ADMIN_PASSWORD', 'Admin1234!')
CLIENT_PASSWORD = os.environ.get('SEED_CLIENT_PASSWORD', 'Client1234!')


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
        for email in [ADMIN_EMAIL, CLIENT_EMAIL]:
            user = User.objects.filter(email=email).first()
            if user:
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
            if ecommerce_project:
                self._create_requirements(ecommerce_project)
                self._create_change_requests(ecommerce_project, client_user, admin_user)
                self._create_bug_reports(ecommerce_project, client_user, admin_user)
                self._create_deliverables(ecommerce_project, admin_user)
            return

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

        self._create_requirements(ecommerce_project)
        self._create_change_requests(ecommerce_project, client_user, admin_user)
        self._create_bug_reports(ecommerce_project, client_user, admin_user)
        self._create_deliverables(ecommerce_project, admin_user)

    def _create_requirements(self, project):
        if Requirement.objects.filter(project=project).exists():
            self.stdout.write(f'  Requirements already exist for {project.name}')
            return

        reqs = [
            {'title': 'Diseño de la página principal', 'status': 'done', 'priority': 'high', 'module': 'Frontend', 'order': 0, 'estimated_hours': 16},
            {'title': 'Catálogo de productos con filtros', 'status': 'done', 'priority': 'high', 'module': 'Frontend', 'order': 1, 'estimated_hours': 24},
            {'title': 'Carrito de compras', 'status': 'in_review', 'priority': 'critical', 'module': 'Frontend', 'order': 0, 'estimated_hours': 20},
            {'title': 'Integración pasarela de pagos (Wompi)', 'status': 'in_progress', 'priority': 'critical', 'module': 'Backend', 'order': 0, 'estimated_hours': 32},
            {'title': 'Sistema de autenticación de usuarios', 'status': 'in_progress', 'priority': 'high', 'module': 'Backend', 'order': 1, 'estimated_hours': 12},
            {'title': 'Panel de administración de productos', 'status': 'in_review', 'priority': 'medium', 'module': 'Admin', 'order': 1, 'estimated_hours': 18},
            {'title': 'Notificaciones por email de pedidos', 'status': 'todo', 'priority': 'medium', 'module': 'Backend', 'order': 0, 'estimated_hours': 8},
            {'title': 'Sistema de cupones y descuentos', 'status': 'todo', 'priority': 'low', 'module': 'Backend', 'order': 1, 'estimated_hours': 14},
            {'title': 'Gestión de inventario', 'status': 'todo', 'priority': 'medium', 'module': 'Admin', 'order': 2, 'estimated_hours': 20},
            {'title': 'Reportes de ventas', 'status': 'todo', 'priority': 'low', 'module': 'Admin', 'order': 3, 'estimated_hours': 16},
            {'title': 'Optimización SEO del catálogo', 'status': 'todo', 'priority': 'low', 'module': 'Frontend', 'order': 4, 'estimated_hours': 10},
        ]

        for r in reqs:
            Requirement.objects.create(
                project=project,
                title=r['title'],
                status=r['status'],
                priority=r['priority'],
                module=r.get('module', ''),
                order=r.get('order', 0),
                estimated_hours=r.get('estimated_hours'),
            )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(reqs)} requirements for {project.name}'))

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
        if BugReport.objects.filter(project=project).exists():
            self.stdout.write(f'  Bug reports already exist for {project.name}')
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

        for bug_data in bugs:
            bug = BugReport.objects.create(
                project=project,
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

    def _create_deliverables(self, project, admin_user):
        if Deliverable.objects.filter(project=project).exists():
            self.stdout.write(f'  Deliverables already exist for {project.name}')
            return

        from django.core.files.base import ContentFile

        deliverables = [
            {
                'title': 'Wireframes página principal',
                'description': 'Wireframes de baja fidelidad para la estructura de la home page.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'wireframes-home-v1.pdf',
            },
            {
                'title': 'Guía de estilos UI',
                'description': 'Colores, tipografías, espaciados y componentes del sistema de diseño.',
                'category': Deliverable.CATEGORY_DESIGNS,
                'filename': 'style-guide-v1.pdf',
            },
            {
                'title': 'Credenciales Wompi Sandbox',
                'description': 'Llaves de API para pruebas en sandbox de la pasarela de pagos.',
                'category': Deliverable.CATEGORY_CREDENTIALS,
                'filename': 'wompi-sandbox-keys.txt',
            },
            {
                'title': 'Manual de usuario',
                'description': 'Documentación de uso del panel de administración de productos.',
                'category': Deliverable.CATEGORY_DOCUMENTS,
                'filename': 'manual-admin-v1.pdf',
            },
            {
                'title': 'APK Android beta',
                'description': 'Build de prueba para Android. Requiere permisos de instalación de fuentes desconocidas.',
                'category': Deliverable.CATEGORY_APKS,
                'filename': 'ecommerce-beta-v0.1.apk',
            },
        ]

        from accounts.models import DeliverableVersion

        for d_data in deliverables:
            placeholder = ContentFile(b'placeholder content', name=d_data['filename'])

            d = Deliverable.objects.create(
                project=project,
                uploaded_by=admin_user,
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
                uploaded_by=admin_user,
            )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(deliverables)} deliverables for {project.name}'))
