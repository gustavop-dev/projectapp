import logging

logger = logging.getLogger(__name__)

from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserProfile
from accounts.permissions import IsAdminRole
from accounts.serializers import (
    ClientListSerializer,
    CompleteProfileSerializer,
    CreateClientSerializer,
    LoginSerializer,
    ResendCodeSerializer,
    UpdateClientSerializer,
    UpdateProfileSerializer,
    UserProfileSerializer,
    VerifyOnboardingSerializer,
)
from accounts.services.onboarding import create_client, resend_invitation
from accounts.services.tokens import get_tokens_for_user, get_verification_token_for_user
from accounts.services.verification import create_and_send_otp, validate_otp

User = get_user_model()


# ==========================================================================
# Auth endpoints
# ==========================================================================

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login_view(request):
    """
    Unified login for admin and client.
    - If user is onboarded → return JWT tokens.
    - If user is NOT onboarded → send OTP, return verification_token.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email'].lower().strip()
    password = serializer.validated_data['password']

    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response(
            {'detail': 'Credenciales incorrectas.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {'detail': 'Tu cuenta ha sido desactivada. Contacta al administrador.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    profile = getattr(user, 'profile', None)
    if profile is None:
        return Response(
            {'detail': 'Tu cuenta no tiene un perfil de plataforma configurado.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not profile.is_onboarded:
        create_and_send_otp(user)
        verification_token = get_verification_token_for_user(user)
        return Response({
            'requires_verification': True,
            'verification_token': verification_token,
            'email': user.email,
        })

    tokens = get_tokens_for_user(user)
    return Response({
        'requires_verification': False,
        'tokens': tokens,
        'user': UserProfileSerializer(profile, context={'request': request}).data,
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def verify_view(request):
    """
    Step 2 of onboarding: verify OTP and set permanent password.
    The user is identified via the verification_token in the Authorization header.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response(
            {'detail': 'Token de verificación requerido.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token_str = auth_header.split(' ', 1)[1]

    try:
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token_str)
        user = jwt_auth.get_user(validated_token)
    except Exception:
        return Response(
            {'detail': 'Token de verificación inválido o expirado.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    serializer = VerifyOnboardingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data['code']
    new_password = serializer.validated_data['new_password']

    success, error_msg = validate_otp(user, code)
    if not success:
        return Response({'detail': error_msg}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save(update_fields=['password'])

    profile = user.profile
    profile.is_onboarded = True
    profile.save(update_fields=['is_onboarded'])

    tokens = get_tokens_for_user(user)
    return Response({
        'tokens': tokens,
        'user': UserProfileSerializer(profile, context={'request': request}).data,
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def resend_code_view(request):
    """Resend the OTP code. User identified via verification_token."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response(
            {'detail': 'Token de verificación requerido.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token_str = auth_header.split(' ', 1)[1]

    try:
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token_str)
        user = jwt_auth.get_user(validated_token)
    except Exception:
        return Response(
            {'detail': 'Token de verificación inválido o expirado.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    create_and_send_otp(user)
    return Response({'detail': 'Código reenviado a tu email.'})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def token_refresh_view(request):
    """Refresh JWT access token."""
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token requerido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    except TokenError:
        return Response(
            {'detail': 'Refresh token inválido o expirado.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )


# ==========================================================================
# Profile endpoints
# ==========================================================================

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Get or update the authenticated user's profile."""
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        return Response(
            {'detail': 'Perfil no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(UserProfileSerializer(profile, context={'request': request}).data)

    serializer = UpdateProfileSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    user = request.user
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    user.save(update_fields=['first_name', 'last_name'])

    profile_fields = ['updated_at']
    for field in ('company_name', 'phone', 'cedula', 'date_of_birth', 'gender', 'education_level'):
        if field in data:
            setattr(profile, field, data[field])
            profile_fields.append(field)
    profile.save(update_fields=profile_fields)

    return Response(UserProfileSerializer(profile, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_profile_view(request):
    """Mandatory profile completion after first onboarding. Accepts multipart/form-data for avatar."""
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        return Response(
            {'detail': 'Perfil no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if profile.profile_completed:
        return Response(
            {'detail': 'El perfil ya fue completado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CompleteProfileSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    user = request.user
    if data.get('first_name'):
        user.first_name = data['first_name']
    if data.get('last_name'):
        user.last_name = data['last_name']
    user.save(update_fields=['first_name', 'last_name'])

    profile.company_name = data['company_name']
    profile.phone = data['phone']
    profile.cedula = data['cedula']
    profile.date_of_birth = data['date_of_birth']
    profile.gender = data['gender']
    profile.education_level = data['education_level']
    profile.profile_completed = True

    if data.get('avatar'):
        profile.avatar = data['avatar']

    profile.save()

    return Response(UserProfileSerializer(profile, context={'request': request}).data)


# ==========================================================================
# Admin — Client management
# ==========================================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdminRole])
def client_list_view(request):
    """List all clients or create a new one."""
    if request.method == 'GET':
        filter_param = request.query_params.get('filter', 'all')
        qs = UserProfile.objects.filter(role=UserProfile.ROLE_CLIENT).select_related('user')

        if filter_param == 'onboarded':
            qs = qs.filter(is_onboarded=True, user__is_active=True)
        elif filter_param == 'pending':
            qs = qs.filter(is_onboarded=False, user__is_active=True)
        elif filter_param == 'inactive':
            qs = qs.filter(user__is_active=False)

        serializer = ClientListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    serializer = CreateClientSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        user, _ = create_client(
            email=serializer.validated_data['email'],
            first_name=serializer.validated_data['first_name'],
            last_name=serializer.validated_data['last_name'],
            company_name=serializer.validated_data.get('company_name', ''),
            phone=serializer.validated_data.get('phone', ''),
            created_by=request.user,
        )
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        ClientListSerializer(user.profile, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdminRole])
def client_detail_view(request, user_id):
    """Get, update, or deactivate a client."""
    try:
        profile = (
            UserProfile.objects
            .filter(role=UserProfile.ROLE_CLIENT, user_id=user_id)
            .select_related('user')
            .get()
        )
    except UserProfile.DoesNotExist:
        return Response(
            {'detail': 'Cliente no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(ClientListSerializer(profile, context={'request': request}).data)

    if request.method == 'DELETE':
        user = profile.user
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({'detail': 'Cliente desactivado.'})

    serializer = UpdateClientSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    user = profile.user
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'is_active' in data:
        user.is_active = data['is_active']
    user.save(update_fields=['first_name', 'last_name', 'is_active'])

    if 'company_name' in data:
        profile.company_name = data['company_name']
    if 'phone' in data:
        profile.phone = data['phone']
    profile.save(update_fields=['company_name', 'phone', 'updated_at'])

    return Response(ClientListSerializer(profile, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminRole])
def client_resend_invite_view(request, user_id):
    """Resend invitation email with a new temp password."""
    try:
        profile = (
            UserProfile.objects
            .filter(role=UserProfile.ROLE_CLIENT, user_id=user_id)
            .select_related('user')
            .get()
        )
    except UserProfile.DoesNotExist:
        return Response(
            {'detail': 'Cliente no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    resend_invitation(profile.user)
    return Response({'detail': 'Invitación reenviada.'})


# ==========================================================================
# Projects
# ==========================================================================

from accounts.models import Project  # noqa: E402
from accounts.serializers import (  # noqa: E402
    CreateProjectSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    UpdateProjectSerializer,
)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def project_list_view(request):
    """
    GET  — Admin sees all projects; client sees only their own.
    POST — Admin creates a project for a client.
    """
    profile = getattr(request.user, 'profile', None)

    if request.method == 'GET':
        if profile and profile.is_admin:
            qs = Project.objects.select_related('client', 'client__profile').all()
            client_filter = request.query_params.get('client')
            if client_filter:
                qs = qs.filter(client_id=client_filter)
            status_filter = request.query_params.get('status')
            if status_filter:
                qs = qs.filter(status=status_filter)
        else:
            qs = Project.objects.select_related('client', 'client__profile').filter(
                client=request.user,
            )
        serializer = ProjectListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden crear proyectos.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = CreateProjectSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    proposal = None
    proposal_id = data.get('proposal_id')
    if proposal_id:
        from content.models import BusinessProposal
        proposal = BusinessProposal.objects.filter(id=proposal_id).first()

    # Extract proposal data before creating the project
    payment_milestones = []
    hosting_tiers = []
    if proposal:
        payment_milestones, hosting_tiers = _extract_proposal_financial_data(proposal)

    project = Project.objects.create(
        name=data['name'],
        description=data.get('description', ''),
        client_id=data['client_id'],
        proposal=proposal,
        status=data.get('status', Project.STATUS_ACTIVE),
        progress=data.get('progress', 0),
        start_date=data.get('start_date'),
        estimated_end_date=data.get('estimated_end_date'),
        hosting_start_date=data.get('hosting_start_date'),
        payment_milestones=payment_milestones,
        hosting_tiers=hosting_tiers,
    )

    from accounts.models import Notification
    from accounts.services.notifications import notify
    client = User.objects.get(id=data['client_id'])
    notify(
        user=client,
        type=Notification.TYPE_GENERAL,
        title=f'Nuevo proyecto: {project.name}',
        message=f'Se creó el proyecto "{project.name}" para ti. Ya puedes acceder desde tu plataforma.',
        project=project,
        related_object_type='project',
        related_object_id=project.id,
    )

    return Response(
        ProjectDetailSerializer(project, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def project_detail_view(request, project_id):
    """
    GET    — Admin or owning client can view.
    PATCH  — Admin only.
    DELETE — Admin only (archives the project).
    """
    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin

    try:
        project = Project.objects.select_related('client', 'client__profile').get(id=project_id)
    except Project.DoesNotExist:
        return Response({'detail': 'Proyecto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if not is_admin and project.client_id != request.user.id:
        return Response({'detail': 'No tienes acceso a este proyecto.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(ProjectDetailSerializer(project, context={'request': request}).data)

    if not is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden modificar proyectos.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'DELETE':
        project.status = Project.STATUS_ARCHIVED
        project.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'Proyecto archivado.'})

    serializer = UpdateProjectSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    update_fields = ['updated_at']
    for field in ('name', 'description', 'status', 'progress', 'start_date', 'estimated_end_date'):
        if field in data:
            setattr(project, field, data[field])
            update_fields.append(field)
    project.save(update_fields=update_fields)

    return Response(ProjectDetailSerializer(project, context={'request': request}).data)


# ==========================================================================
# Requirements (Kanban board)
# ==========================================================================

from accounts.models import Requirement, RequirementComment, RequirementHistory  # noqa: E402
from accounts.serializers import (  # noqa: E402
    CreateCommentSerializer,
    CreateRequirementSerializer,
    MoveRequirementSerializer,
    RequirementDetailSerializer,
    RequirementListSerializer,
    UpdateRequirementSerializer,
)


def _get_project_or_403(request, project_id):
    """Helper: get project checking access for admin or owning client."""
    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin
    try:
        proj = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return None, Response({'detail': 'Proyecto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    if not is_admin and proj.client_id != request.user.id:
        return None, Response({'detail': 'No tienes acceso a este proyecto.'}, status=status.HTTP_403_FORBIDDEN)
    return proj, None


def _recalculate_project_progress(project):
    """Auto-sync project.progress from done/total requirements."""
    total = Requirement.objects.filter(project=project).count()
    if total == 0:
        project.progress = 0
    else:
        done = Requirement.objects.filter(project=project, status=Requirement.STATUS_DONE).count()
        project.progress = round((done / total) * 100)
    project.save(update_fields=['progress', 'updated_at'])


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def requirement_list_view(request, project_id):
    """
    GET  — All requirements for a project (both roles).
    POST — Admin creates a new requirement.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    if request.method == 'GET':
        qs = Requirement.objects.filter(project=proj)
        serializer = RequirementListSerializer(qs, many=True)
        return Response(serializer.data)

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden crear requerimientos.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = CreateRequirementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    max_order = Requirement.objects.filter(
        project=proj, status=data.get('status', Requirement.STATUS_BACKLOG),
    ).count()

    req = Requirement.objects.create(
        project=proj,
        title=data['title'],
        description=data.get('description', ''),
        configuration=data.get('configuration', ''),
        flow=data.get('flow', ''),
        status=data.get('status', Requirement.STATUS_BACKLOG),
        priority=data.get('priority', Requirement.PRIORITY_MEDIUM),
        order=max_order,
    )

    _recalculate_project_progress(proj)
    return Response(RequirementListSerializer(req).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminRole])
def requirement_bulk_upload_view(request, project_id):
    """
    Admin uploads a JSON array of requirements to create in bulk.
    Expected format: [{ title, description?, configuration?, flow?, priority?, status? }, ...]
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    items = request.data
    if not isinstance(items, list):
        return Response(
            {'detail': 'Se espera un array JSON de requerimientos.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(items) > 500:
        return Response(
            {'detail': 'Máximo 500 requerimientos por carga.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created = []
    order_offset = Requirement.objects.filter(project=proj).count()

    for idx, item in enumerate(items):
        if not isinstance(item, dict) or not item.get('title'):
            continue

        req = Requirement.objects.create(
            project=proj,
            title=item['title'][:300],
            description=item.get('description', ''),
            configuration=item.get('configuration', ''),
            flow=item.get('flow', ''),
            status=item.get('status', Requirement.STATUS_BACKLOG),
            priority=item.get('priority', Requirement.PRIORITY_MEDIUM),
            order=order_offset + idx,
        )
        created.append(req)

    _recalculate_project_progress(proj)
    return Response(
        {'created': len(created), 'requirements': RequirementListSerializer(created, many=True).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def requirement_detail_view(request, project_id, req_id):
    """GET detail, PATCH update (admin), DELETE remove (admin)."""
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        req = Requirement.objects.prefetch_related('comments__user', 'history__changed_by').get(
            id=req_id, project=proj,
        )
    except Requirement.DoesNotExist:
        return Response({'detail': 'Requerimiento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(RequirementDetailSerializer(req, context={'request': request}).data)

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden modificar requerimientos.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'DELETE':
        req.delete()
        _recalculate_project_progress(proj)
        return Response({'detail': 'Requerimiento eliminado.'})

    serializer = UpdateRequirementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    old_status = req.status
    upd_fields = ['updated_at']
    for field in ('title', 'description', 'status', 'priority', 'estimated_hours', 'module', 'order'):
        if field in data:
            setattr(req, field, data[field])
            upd_fields.append(field)
    req.save(update_fields=upd_fields)

    if 'status' in data and data['status'] != old_status:
        RequirementHistory.objects.create(
            requirement=req, from_status=old_status,
            to_status=data['status'], changed_by=request.user,
        )
        _recalculate_project_progress(proj)

    return Response(RequirementDetailSerializer(req, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def requirement_move_view(request, project_id, req_id):
    """
    Move a card to a new column/order.
    Admin can move to any column. Client can only approve (approval→done).
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        req = Requirement.objects.get(id=req_id, project=proj)
    except Requirement.DoesNotExist:
        return Response({'detail': 'Requerimiento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = MoveRequirementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    new_status = serializer.validated_data['status']
    new_order = serializer.validated_data.get('order', 0)

    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin

    if not is_admin:
        if not (req.status == Requirement.STATUS_APPROVAL and new_status == Requirement.STATUS_DONE):
            return Response(
                {'detail': 'Solo puedes aprobar requerimientos en la columna de aprobación.'},
                status=status.HTTP_403_FORBIDDEN,
            )

    old_status = req.status
    req.status = new_status
    req.order = new_order
    req.save(update_fields=['status', 'order', 'updated_at'])

    if new_status != old_status:
        RequirementHistory.objects.create(
            requirement=req, from_status=old_status,
            to_status=new_status, changed_by=request.user,
        )
        _recalculate_project_progress(proj)

        # Notifications
        from accounts.models import Notification
        from accounts.services.notifications import notify_project_admins, notify_project_client

        status_labels = dict(Requirement.STATUS_CHOICES)
        new_label = status_labels.get(new_status, new_status)

        if new_status == Requirement.STATUS_DONE and not is_admin:
            notify_project_admins(
                proj, Notification.TYPE_REQUIREMENT_APPROVED,
                f'Requerimiento aprobado: {req.title}',
                message=f'{request.user.first_name} aprobó "{req.title}" en {proj.name}.',
                related_object_type='requirement', related_object_id=req.id,
                exclude_user=request.user,
            )
        elif is_admin:
            notify_project_client(
                proj, Notification.TYPE_REQUIREMENT_MOVED,
                f'Requerimiento actualizado: {req.title}',
                message=f'"{req.title}" se movió a "{new_label}" en {proj.name}.',
                related_object_type='requirement', related_object_id=req.id,
                exclude_user=request.user,
            )

    return Response(RequirementListSerializer(req).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def requirement_comment_view(request, project_id, req_id):
    """Add a comment to a requirement. Both roles can comment."""
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        req = Requirement.objects.get(id=req_id, project=proj)
    except Requirement.DoesNotExist:
        return Response({'detail': 'Requerimiento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CreateCommentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin
    is_internal = data.get('is_internal', False) and is_admin

    comment = RequirementComment.objects.create(
        requirement=req, user=request.user,
        content=data['content'], is_internal=is_internal,
    )

    from accounts.serializers import RequirementCommentSerializer as RCS  # noqa: E402
    return Response(RCS(comment).data, status=status.HTTP_201_CREATED)


# ==========================================================================
# Change Requests
# ==========================================================================

from accounts.models import ChangeRequest, ChangeRequestComment  # noqa: E402
from accounts.services.notifications import notify_project_admins, notify_project_client  # noqa: E402
from accounts.serializers import (  # noqa: E402
    ChangeRequestCommentSerializer,
    ChangeRequestDetailSerializer,
    ChangeRequestListSerializer,
    CreateChangeRequestCommentSerializer,
    CreateChangeRequestSerializer,
    EvaluateChangeRequestSerializer,
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def change_request_all_view(request):
    """
    GET — All change requests across all projects the user has access to.
    Admin sees all; client sees only their projects.
    """
    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin

    if is_admin:
        qs = ChangeRequest.objects.select_related('created_by', 'project').all()
    else:
        qs = ChangeRequest.objects.select_related('created_by', 'project').filter(
            project__client=request.user,
        )

    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    serializer = ChangeRequestListSerializer(qs, many=True, context={'request': request})

    data = serializer.data
    for item, cr in zip(data, qs):
        item['project_id'] = cr.project_id
        item['project_name'] = cr.project.name

    return Response(data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def change_request_list_view(request, project_id):
    """
    GET  — All change requests for a project (both roles, filtered by status optionally).
    POST — Both roles can create a change request.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    if request.method == 'GET':
        qs = ChangeRequest.objects.filter(project=proj).select_related('created_by')
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        serializer = ChangeRequestListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    serializer = CreateChangeRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    cr = ChangeRequest(
        project=proj,
        created_by=request.user,
        title=data['title'],
        description=data.get('description', ''),
        module_or_screen=data.get('module_or_screen', ''),
        suggested_priority=data.get('suggested_priority', ChangeRequest.PRIORITY_MEDIUM),
        is_urgent=data.get('is_urgent', False),
    )
    if data.get('screenshot'):
        cr.screenshot = data['screenshot']
    cr.save()

    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin
    if is_admin:
        notify_project_client(
            proj, Notification.TYPE_CR_CREATED, f'Nueva solicitud de cambio: {cr.title}',
            message=f'El equipo creó una solicitud de cambio en {proj.name}.',
            related_object_type='change_request', related_object_id=cr.id,
            exclude_user=request.user,
        )
    else:
        notify_project_admins(
            proj, Notification.TYPE_CR_CREATED, f'Nueva solicitud de cambio: {cr.title}',
            message=f'{request.user.first_name} creó una solicitud en {proj.name}.',
            related_object_type='change_request', related_object_id=cr.id,
            exclude_user=request.user,
        )

    return Response(
        ChangeRequestListSerializer(cr, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def change_request_detail_view(request, project_id, cr_id):
    """
    GET    — Detail with comments (both roles).
    DELETE — Admin only.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        cr = ChangeRequest.objects.prefetch_related('comments__user').get(
            id=cr_id, project=proj,
        )
    except ChangeRequest.DoesNotExist:
        return Response(
            {'detail': 'Solicitud de cambio no encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(
            ChangeRequestDetailSerializer(cr, context={'request': request}).data,
        )

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden eliminar solicitudes de cambio.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    cr.delete()
    return Response({'detail': 'Solicitud de cambio eliminada.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_request_evaluate_view(request, project_id, cr_id):
    """
    Admin evaluates a change request: update status, admin_response, estimated_cost/time.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden evaluar solicitudes de cambio.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        cr = ChangeRequest.objects.get(id=cr_id, project=proj)
    except ChangeRequest.DoesNotExist:
        return Response(
            {'detail': 'Solicitud de cambio no encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = EvaluateChangeRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    upd_fields = ['updated_at']
    for field in ('status', 'admin_response', 'estimated_cost', 'estimated_time'):
        if field in data:
            setattr(cr, field, data[field])
            upd_fields.append(field)
    cr.save(update_fields=upd_fields)

    if 'status' in data:
        status_display = dict(ChangeRequest.STATUS_CHOICES).get(data['status'], data['status'])
        notify_project_client(
            proj, Notification.TYPE_CR_STATUS_CHANGED,
            f'Solicitud actualizada: {cr.title}',
            message=f'Estado cambiado a "{status_display}".',
            related_object_type='change_request', related_object_id=cr.id,
            exclude_user=request.user,
        )

    return Response(
        ChangeRequestDetailSerializer(cr, context={'request': request}).data,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_request_comment_view(request, project_id, cr_id):
    """Add a comment to a change request. Both roles can comment."""
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        cr = ChangeRequest.objects.get(id=cr_id, project=proj)
    except ChangeRequest.DoesNotExist:
        return Response(
            {'detail': 'Solicitud de cambio no encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = CreateChangeRequestCommentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin
    is_internal = data.get('is_internal', False) and is_admin

    comment = ChangeRequestComment.objects.create(
        change_request=cr,
        user=request.user,
        content=data['content'],
        is_internal=is_internal,
    )

    return Response(
        ChangeRequestCommentSerializer(comment).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_request_convert_view(request, project_id, cr_id):
    """
    Admin converts an approved change request into a Kanban requirement.
    Creates the requirement and links it back to the CR.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden convertir solicitudes en requerimientos.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        cr = ChangeRequest.objects.get(id=cr_id, project=proj)
    except ChangeRequest.DoesNotExist:
        return Response(
            {'detail': 'Solicitud de cambio no encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if cr.status != ChangeRequest.STATUS_APPROVED:
        return Response(
            {'detail': 'Solo se pueden convertir solicitudes aprobadas.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if cr.linked_requirement is not None:
        return Response(
            {'detail': 'Esta solicitud ya fue convertida en un requerimiento.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    max_order = Requirement.objects.filter(
        project=proj, status=Requirement.STATUS_TODO,
    ).count()

    req = Requirement.objects.create(
        project=proj,
        title=cr.title,
        description=cr.description,
        configuration=f'Originado de solicitud de cambio #{cr.id} — módulo: {cr.module_or_screen}',
        status=Requirement.STATUS_TODO,
        priority=cr.suggested_priority,
        order=max_order,
    )

    cr.linked_requirement = req
    cr.save(update_fields=['linked_requirement', 'updated_at'])

    _recalculate_project_progress(proj)

    return Response(
        ChangeRequestDetailSerializer(cr, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


# ==========================================================================
# Bug Reports
# ==========================================================================

from accounts.models import BugReport, BugComment  # noqa: E402
from accounts.serializers import (  # noqa: E402
    BugCommentSerializer,
    BugReportDetailSerializer,
    BugReportListSerializer,
    CreateBugCommentSerializer,
    CreateBugReportSerializer,
    EvaluateBugReportSerializer,
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bug_report_all_view(request):
    """
    GET — All bug reports across all projects the user has access to.
    Admin sees all; client sees only their projects.
    """
    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin

    if is_admin:
        qs = BugReport.objects.select_related('reported_by', 'project').all()
    else:
        qs = BugReport.objects.select_related('reported_by', 'project').filter(
            project__client=request.user,
        )

    status_filter = request.query_params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)
    severity_filter = request.query_params.get('severity')
    if severity_filter:
        qs = qs.filter(severity=severity_filter)

    serializer = BugReportListSerializer(qs, many=True, context={'request': request})

    data = serializer.data
    for item, bug in zip(data, qs):
        item['project_id'] = bug.project_id
        item['project_name'] = bug.project.name

    return Response(data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def bug_report_list_view(request, project_id):
    """
    GET  — All bug reports for a project (both roles, filtered optionally).
    POST — Both roles can report a bug.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    if request.method == 'GET':
        qs = BugReport.objects.filter(project=proj).select_related('reported_by')
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        severity_filter = request.query_params.get('severity')
        if severity_filter:
            qs = qs.filter(severity=severity_filter)
        serializer = BugReportListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    serializer = CreateBugReportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    bug = BugReport(
        project=proj,
        reported_by=request.user,
        title=data['title'],
        description=data.get('description', ''),
        severity=data.get('severity', BugReport.SEVERITY_MEDIUM),
        steps_to_reproduce=data.get('steps_to_reproduce', []),
        expected_behavior=data.get('expected_behavior', ''),
        actual_behavior=data.get('actual_behavior', ''),
        environment=data.get('environment', BugReport.ENV_PRODUCTION),
        device_browser=data.get('device_browser', ''),
        is_recurring=data.get('is_recurring', False),
    )
    if data.get('screenshot'):
        bug.screenshot = data['screenshot']
    bug.save()

    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin
    if is_admin:
        notify_project_client(
            proj, Notification.TYPE_BUG_REPORTED, f'Bug reportado: {bug.title}',
            message=f'El equipo reportó un bug en {proj.name}.',
            related_object_type='bug_report', related_object_id=bug.id,
            exclude_user=request.user,
        )
    else:
        notify_project_admins(
            proj, Notification.TYPE_BUG_REPORTED, f'Bug reportado: {bug.title}',
            message=f'{request.user.first_name} reportó un bug en {proj.name}.',
            related_object_type='bug_report', related_object_id=bug.id,
            exclude_user=request.user,
        )

    return Response(
        BugReportListSerializer(bug, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def bug_report_detail_view(request, project_id, bug_id):
    """
    GET    — Detail with comments (both roles).
    DELETE — Admin only.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        bug = BugReport.objects.prefetch_related('comments__user').get(
            id=bug_id, project=proj,
        )
    except BugReport.DoesNotExist:
        return Response(
            {'detail': 'Bug no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(
            BugReportDetailSerializer(bug, context={'request': request}).data,
        )

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden eliminar reportes de bugs.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    bug.delete()
    return Response({'detail': 'Reporte de bug eliminado.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bug_report_evaluate_view(request, project_id, bug_id):
    """
    Admin evaluates a bug report: update status, admin_response, linked_bug.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden evaluar reportes de bugs.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        bug = BugReport.objects.get(id=bug_id, project=proj)
    except BugReport.DoesNotExist:
        return Response(
            {'detail': 'Bug no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = EvaluateBugReportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    upd_fields = ['updated_at']
    for field in ('status', 'admin_response'):
        if field in data:
            setattr(bug, field, data[field])
            upd_fields.append(field)
    if 'linked_bug_id' in data:
        bug.linked_bug_id = data['linked_bug_id']
        upd_fields.append('linked_bug_id')
    bug.save(update_fields=upd_fields)

    if 'status' in data:
        status_display = dict(BugReport.STATUS_CHOICES).get(data['status'], data['status'])
        notify_project_client(
            proj, Notification.TYPE_BUG_STATUS_CHANGED,
            f'Bug actualizado: {bug.title}',
            message=f'Estado cambiado a "{status_display}".',
            related_object_type='bug_report', related_object_id=bug.id,
            exclude_user=request.user,
        )

    return Response(
        BugReportDetailSerializer(bug, context={'request': request}).data,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bug_report_comment_view(request, project_id, bug_id):
    """Add a comment to a bug report. Both roles can comment."""
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        bug = BugReport.objects.get(id=bug_id, project=proj)
    except BugReport.DoesNotExist:
        return Response(
            {'detail': 'Bug no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = CreateBugCommentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin
    is_internal = data.get('is_internal', False) and is_admin

    comment = BugComment.objects.create(
        bug_report=bug,
        user=request.user,
        content=data['content'],
        is_internal=is_internal,
    )

    return Response(
        BugCommentSerializer(comment).data,
        status=status.HTTP_201_CREATED,
    )


# ==========================================================================
# Deliverables
# ==========================================================================

from accounts.models import Deliverable, DeliverableVersion  # noqa: E402
from accounts.serializers import (  # noqa: E402
    CreateDeliverableSerializer,
    DeliverableDetailSerializer,
    DeliverableListSerializer,
    UpdateDeliverableSerializer,
    UploadNewVersionSerializer,
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deliverable_all_view(request):
    """
    GET — All deliverables across all projects the user has access to.
    Admin sees all; client sees only their projects.
    """
    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin

    if is_admin:
        qs = Deliverable.objects.select_related('uploaded_by', 'project').all()
    else:
        qs = Deliverable.objects.select_related('uploaded_by', 'project').filter(
            project__client=request.user,
        )

    category_filter = request.query_params.get('category')
    if category_filter:
        qs = qs.filter(category=category_filter)

    serializer = DeliverableListSerializer(qs, many=True, context={'request': request})

    data = serializer.data
    for item, d in zip(data, qs):
        item['project_id'] = d.project_id
        item['project_name'] = d.project.name

    return Response(data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def deliverable_list_view(request, project_id):
    """
    GET  — All deliverables for a project (both roles, filtered by category optionally).
    POST — Admin uploads a new deliverable.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    if request.method == 'GET':
        qs = Deliverable.objects.filter(project=proj).select_related('uploaded_by')
        category_filter = request.query_params.get('category')
        if category_filter:
            qs = qs.filter(category=category_filter)
        serializer = DeliverableListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden subir entregables.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = CreateDeliverableSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    deliverable = Deliverable.objects.create(
        project=proj,
        uploaded_by=request.user,
        title=data['title'],
        description=data.get('description', ''),
        category=data.get('category', Deliverable.CATEGORY_OTHER),
        file=data['file'],
        current_version=1,
    )

    DeliverableVersion.objects.create(
        deliverable=deliverable,
        file=data['file'],
        version_number=1,
        uploaded_by=request.user,
    )

    notify_project_client(
        proj, Notification.TYPE_DELIVERABLE_UPLOADED,
        f'Nuevo entregable: {deliverable.title}',
        message=f'Se subió un archivo en {proj.name}.',
        related_object_type='deliverable', related_object_id=deliverable.id,
        exclude_user=request.user,
    )

    return Response(
        DeliverableListSerializer(deliverable, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def deliverable_detail_view(request, project_id, deliverable_id):
    """
    GET    — Detail with version history (both roles).
    PATCH  — Admin updates metadata (title, description, category).
    DELETE — Admin only.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        deliverable = Deliverable.objects.get(id=deliverable_id, project=proj)
    except Deliverable.DoesNotExist:
        return Response(
            {'detail': 'Entregable no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(
            DeliverableDetailSerializer(deliverable, context={'request': request}).data,
        )

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden modificar entregables.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'DELETE':
        deliverable.delete()
        return Response({'detail': 'Entregable eliminado.'})

    serializer = UpdateDeliverableSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    upd_fields = ['updated_at']
    for field in ('title', 'description', 'category'):
        if field in data:
            setattr(deliverable, field, data[field])
            upd_fields.append(field)
    deliverable.save(update_fields=upd_fields)

    return Response(
        DeliverableDetailSerializer(deliverable, context={'request': request}).data,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deliverable_upload_version_view(request, project_id, deliverable_id):
    """
    Admin uploads a new version of an existing deliverable.
    The old file is kept in DeliverableVersion history.
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden subir nuevas versiones.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        deliverable = Deliverable.objects.get(id=deliverable_id, project=proj)
    except Deliverable.DoesNotExist:
        return Response(
            {'detail': 'Entregable no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = UploadNewVersionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    new_version = deliverable.current_version + 1

    DeliverableVersion.objects.create(
        deliverable=deliverable,
        file=serializer.validated_data['file'],
        version_number=new_version,
        uploaded_by=request.user,
    )

    deliverable.file = serializer.validated_data['file']
    deliverable.current_version = new_version
    deliverable.save(update_fields=['file', 'current_version', 'updated_at'])

    notify_project_client(
        proj, Notification.TYPE_DELIVERABLE_NEW_VERSION,
        f'Nueva versión: {deliverable.title} v{new_version}',
        message=f'Se actualizó un entregable en {proj.name}.',
        related_object_type='deliverable', related_object_id=deliverable.id,
        exclude_user=request.user,
    )

    return Response(
        DeliverableDetailSerializer(deliverable, context={'request': request}).data,
        status=status.HTTP_201_CREATED,
    )


# ==========================================================================
# Notifications
# ==========================================================================

from accounts.models import Notification  # noqa: E402
from accounts.serializers import NotificationSerializer  # noqa: E402


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list_view(request):
    """
    GET — List notifications for the authenticated user.
    Supports ?is_read=true/false filter and ?limit=N.
    """
    qs = Notification.objects.filter(user=request.user).select_related('project')

    is_read_param = request.query_params.get('is_read')
    if is_read_param == 'true':
        qs = qs.filter(is_read=True)
    elif is_read_param == 'false':
        qs = qs.filter(is_read=False)

    limit = request.query_params.get('limit')
    if limit:
        try:
            qs = qs[:int(limit)]
        except (ValueError, TypeError):
            pass

    serializer = NotificationSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_unread_count_view(request):
    """GET — Return count of unread notifications for badge display."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'count': count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notification_mark_read_view(request, notification_id):
    """Mark a single notification as read."""
    try:
        notif = Notification.objects.get(id=notification_id, user=request.user)
    except Notification.DoesNotExist:
        return Response(
            {'detail': 'Notificación no encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return Response(NotificationSerializer(notif).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def notification_mark_all_read_view(request):
    """Mark all unread notifications as read for the authenticated user."""
    updated = Notification.objects.filter(
        user=request.user, is_read=False,
    ).update(is_read=True)
    return Response({'marked_read': updated})


# ==========================================================================
# Payments & Subscriptions
# ==========================================================================

from accounts.models import HostingSubscription, Payment  # noqa: E402
from accounts.serializers import (  # noqa: E402
    HostingSubscriptionListSerializer,
    HostingSubscriptionSerializer,
    PaymentSerializer,
    ProposalSummarySerializer,
    UpdateSubscriptionSerializer,
)


def _extract_proposal_financial_data(proposal):
    """
    Extract payment milestones and hosting tiers from the proposal's
    investment section (section_type='investment') content_json.
    Returns (payment_milestones, hosting_tiers) as plain lists.
    """
    from content.models import ProposalSection
    from decimal import Decimal

    payment_milestones = []
    hosting_tiers = []

    try:
        section = ProposalSection.objects.get(
            proposal=proposal, section_type='investment',
        )
    except ProposalSection.DoesNotExist:
        return payment_milestones, hosting_tiers

    cj = section.content_json or {}

    # --- Payment milestones (admin-visible only) ---
    for opt in cj.get('paymentOptions', []):
        payment_milestones.append({
            'label': opt.get('label', ''),
            'description': opt.get('description', ''),
        })

    # --- Hosting tiers (pricing for client plan selection) ---
    hosting_plan = cj.get('hostingPlan', {})
    base_percent = hosting_plan.get('hostingPercent', proposal.hosting_percent)
    hosting_annual = float(proposal.total_investment) * base_percent / 100
    base_monthly = round(hosting_annual / 12, 2)
    currency = str(cj.get('currency', proposal.currency))

    billing_tiers = hosting_plan.get('billingTiers', [])

    if billing_tiers:
        for tier in billing_tiers:
            discount = tier.get('discountPercent', 0)
            effective_monthly = round(base_monthly * (100 - discount) / 100, 2)
            months = tier.get('months', 1)
            hosting_tiers.append({
                'frequency': tier.get('frequency', ''),
                'months': months,
                'label': tier.get('label', ''),
                'badge': tier.get('badge', ''),
                'discount_percent': discount,
                'base_monthly': base_monthly,
                'effective_monthly': effective_monthly,
                'billing_amount': round(effective_monthly * months, 2),
                'currency': currency,
            })
    else:
        # Compute default tiers from proposal model fields
        default_tiers = [
            {'frequency': 'semiannual', 'months': 6, 'label': 'Semestral', 'badge': 'Mejor precio', 'discount': proposal.hosting_discount_semiannual},
            {'frequency': 'quarterly', 'months': 3, 'label': 'Trimestral', 'badge': f'{proposal.hosting_discount_quarterly}% dcto' if proposal.hosting_discount_quarterly else '', 'discount': proposal.hosting_discount_quarterly},
            {'frequency': 'monthly', 'months': 1, 'label': 'Mensual', 'badge': '', 'discount': 0},
        ]
        for tier in default_tiers:
            discount = tier['discount']
            effective_monthly = round(base_monthly * (100 - discount) / 100, 2)
            months = tier['months']
            hosting_tiers.append({
                'frequency': tier['frequency'],
                'months': months,
                'label': tier['label'],
                'badge': tier['badge'],
                'discount_percent': discount,
                'base_monthly': base_monthly,
                'effective_monthly': effective_monthly,
                'billing_amount': round(effective_monthly * months, 2),
                'currency': currency,
            })

    return payment_milestones, hosting_tiers


def _create_subscription_from_proposal(project, proposal, plan, start_date):
    """Create a HostingSubscription from a BusinessProposal's hosting pricing."""
    from decimal import Decimal

    hosting_annual = proposal.total_investment * Decimal(proposal.hosting_percent) / Decimal(100)
    base_monthly = round(hosting_annual / Decimal(12), 2)

    discount_map = {
        HostingSubscription.PLAN_MONTHLY: 0,
        HostingSubscription.PLAN_QUARTERLY: proposal.hosting_discount_quarterly,
        HostingSubscription.PLAN_SEMIANNUAL: proposal.hosting_discount_semiannual,
    }
    discount = discount_map.get(plan, 0)

    from dateutil.relativedelta import relativedelta

    sub = HostingSubscription(
        project=project,
        plan=plan,
        base_monthly_amount=base_monthly,
        discount_percent=discount,
        start_date=start_date,
        next_billing_date=start_date,
        status=HostingSubscription.STATUS_PENDING,
    )
    sub.calculate_amounts()
    sub.save()

    # Create the first payment record
    months = sub.billing_months
    billing_end = start_date + relativedelta(months=months) - relativedelta(days=1)

    Payment.objects.create(
        subscription=sub,
        amount=sub.billing_amount,
        description=f'Hosting {sub.get_plan_display()} — {start_date} a {billing_end}',
        billing_period_start=start_date,
        billing_period_end=billing_end,
        due_date=start_date,
        status=Payment.STATUS_PENDING,
    )

    # Update next_billing_date to the start of the NEXT cycle
    sub.next_billing_date = billing_end + relativedelta(days=1)
    sub.save(update_fields=['next_billing_date'])

    return sub


def _generate_next_payment(subscription):
    """
    Generate the next Payment record for a subscription's billing cycle.
    Called after a payment is completed (auto-renewal) or when a subscription
    is first created.
    Skips if a pending/processing payment already exists for the next period.
    """
    from dateutil.relativedelta import relativedelta

    # Check if there's already a pending/processing payment
    existing = Payment.objects.filter(
        subscription=subscription,
        status__in=[Payment.STATUS_PENDING, Payment.STATUS_PROCESSING],
    ).exists()
    if existing:
        return None

    billing_start = subscription.next_billing_date
    if not billing_start:
        return None

    months = subscription.billing_months
    billing_end = billing_start + relativedelta(months=months) - relativedelta(days=1)

    payment = Payment.objects.create(
        subscription=subscription,
        amount=subscription.billing_amount,
        description=f'Hosting {subscription.get_plan_display()} — {billing_start} a {billing_end}',
        billing_period_start=billing_start,
        billing_period_end=billing_end,
        due_date=billing_start,
        status=Payment.STATUS_PENDING,
    )
    return payment


def _handle_payment_approved(payment):
    """
    Common logic when a payment is approved (card-pay, verify, webhook).
    Marks payment as paid, updates subscription, and generates next payment (auto-renewal).
    """
    from django.utils import timezone as tz
    from dateutil.relativedelta import relativedelta

    payment.status = Payment.STATUS_PAID
    payment.paid_at = tz.now()
    payment.save(update_fields=['wompi_transaction_id', 'status', 'paid_at'])

    sub = payment.subscription
    sub.next_billing_date = payment.billing_period_end + relativedelta(days=1)
    if sub.status == HostingSubscription.STATUS_PENDING:
        sub.status = HostingSubscription.STATUS_ACTIVE
    sub.save(update_fields=['next_billing_date', 'status', 'updated_at'])

    # Auto-renewal: generate the next billing cycle payment
    _generate_next_payment(sub)

    # Notify about payment
    try:
        from accounts.models import Notification
        from accounts.services.notifications import notify, notify_project_admins
        project = sub.project
        notify(
            user=project.client,
            type=Notification.TYPE_GENERAL,
            title='Pago confirmado',
            message=f'Tu pago de ${payment.amount:,.0f} COP para "{project.name}" fue procesado exitosamente. Próxima renovación: {sub.next_billing_date}.',
            project=project,
            related_object_type='payment',
            related_object_id=payment.id,
        )
        notify_project_admins(
            project, Notification.TYPE_GENERAL,
            f'Pago recibido: {project.name}',
            message=f'{project.client.first_name} pagó ${payment.amount:,.0f} COP del hosting de "{project.name}".',
            related_object_type='payment', related_object_id=payment.id,
        )
    except Exception:
        logger.warning('Failed to create payment notifications for payment %s', payment.id)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminRole])
def proposal_list_for_selector_view(request):
    """Admin-only: list proposals for the project creation selector."""
    from content.models import BusinessProposal

    qs = BusinessProposal.objects.filter(
        status__in=['accepted', 'sent', 'viewed', 'negotiating'],
    ).order_by('-created_at')

    serializer = ProposalSummarySerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_list_view(request):
    """
    Admin sees all subscriptions. Client sees only their projects' subscriptions.
    """
    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin

    if is_admin:
        qs = HostingSubscription.objects.select_related('project').all()
    else:
        qs = HostingSubscription.objects.select_related('project').filter(
            project__client=request.user,
        )

    serializer = HostingSubscriptionListSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([IsAuthenticated])
def project_subscription_view(request, project_id):
    """
    GET  — Subscription detail with payments (admin or owning client).
           Returns 404 if no subscription exists yet.
    POST — Client (or admin) creates subscription by choosing a hosting plan.
           Required: { plan: 'monthly'|'quarterly'|'semiannual' }
           Only works if no subscription exists yet and project has a linked proposal.
    PATCH — Change hosting plan (admin or client) or status (admin only).
    """
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    # --- POST: create subscription ---
    if request.method == 'POST':
        if HostingSubscription.objects.filter(project=proj).exists():
            return Response(
                {'detail': 'Ya existe una suscripción de hosting para este proyecto.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not proj.proposal:
            return Response(
                {'detail': 'El proyecto no tiene una propuesta vinculada para calcular el hosting.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plan = request.data.get('plan')
        if plan not in dict(HostingSubscription.PLAN_CHOICES):
            return Response(
                {'detail': 'Plan inválido. Opciones: monthly, quarterly, semiannual.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from datetime import date
        start_date = proj.hosting_start_date or date.today()
        sub = _create_subscription_from_proposal(proj, proj.proposal, plan, start_date)
        return Response(
            HostingSubscriptionSerializer(sub).data,
            status=status.HTTP_201_CREATED,
        )

    # --- GET / PATCH: existing subscription ---
    try:
        sub = HostingSubscription.objects.prefetch_related('payments').get(project=proj)
    except HostingSubscription.DoesNotExist:
        return Response(
            {'detail': 'No hay suscripción de hosting para este proyecto.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response(HostingSubscriptionSerializer(sub).data)

    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin

    serializer = UpdateSubscriptionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Client can only change plan, not status
    if 'status' in data and not is_admin:
        return Response(
            {'detail': 'Solo los administradores pueden cambiar el estado de la suscripción.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if 'plan' in data:
        sub.plan = data['plan']
        discount = _get_plan_discount(proj, data['plan'])
        sub.discount_percent = discount
        sub.calculate_amounts()
    if 'status' in data:
        sub.status = data['status']
    sub.save()

    return Response(HostingSubscriptionSerializer(sub).data)


def _get_plan_discount(project, plan):
    """Get the discount % for a hosting plan from project.hosting_tiers or proposal defaults."""
    # Try to find discount from stored hosting_tiers
    for tier in (project.hosting_tiers or []):
        if tier.get('frequency') == plan:
            return tier.get('discount_percent', 0)
    # Fallback to proposal if linked
    if project.proposal:
        discount_map = {
            HostingSubscription.PLAN_MONTHLY: 0,
            HostingSubscription.PLAN_QUARTERLY: project.proposal.hosting_discount_quarterly,
            HostingSubscription.PLAN_SEMIANNUAL: project.proposal.hosting_discount_semiannual,
        }
        return discount_map.get(plan, 0)
    # Hardcoded fallback
    return {
        HostingSubscription.PLAN_MONTHLY: 0,
        HostingSubscription.PLAN_QUARTERLY: 10,
        HostingSubscription.PLAN_SEMIANNUAL: 20,
    }.get(plan, 0)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_payments_view(request, project_id):
    """List payments for a project's subscription."""
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        sub = HostingSubscription.objects.get(project=proj)
    except HostingSubscription.DoesNotExist:
        return Response([])

    payments = Payment.objects.filter(subscription=sub).select_related('subscription__project')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminRole])
def payment_generate_link_view(request, project_id, payment_id):
    """Admin generates a Wompi payment link for a pending payment."""
    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        payment = Payment.objects.select_related('subscription__project').get(
            id=payment_id, subscription__project=proj,
        )
    except Payment.DoesNotExist:
        return Response(
            {'detail': 'Pago no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if payment.status not in (Payment.STATUS_PENDING, Payment.STATUS_OVERDUE, Payment.STATUS_FAILED):
        return Response(
            {'detail': 'Solo se pueden generar links para pagos pendientes, vencidos o fallidos.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from accounts.services.wompi import create_payment_link
        link_id, link_url = create_payment_link(payment)
        return Response({
            'payment_id': payment.id,
            'wompi_payment_link_id': link_id,
            'wompi_payment_link_url': link_url,
        })
    except Exception as e:
        return Response(
            {'detail': f'Error al generar el link de pago: {str(e)}'},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_widget_data_view(request, project_id, payment_id):
    """
    Generate Wompi widget checkout data (integrity signature, reference, etc.)
    for the frontend to open the Wompi widget with a custom branded button.
    """
    import hashlib
    import time

    from django.conf import settings as django_settings

    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        payment = Payment.objects.select_related('subscription__project').get(
            id=payment_id, subscription__project=proj,
        )
    except Payment.DoesNotExist:
        return Response(
            {'detail': 'Pago no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if payment.status not in (Payment.STATUS_PENDING, Payment.STATUS_OVERDUE, Payment.STATUS_PROCESSING, Payment.STATUS_FAILED):
        return Response(
            {'detail': 'Este pago no está disponible para cobro.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    amount_in_cents = int(payment.amount * 100)
    ts = int(time.time())
    reference = f'PA{payment.id}P{proj.id}T{ts}'

    integrity_secret = django_settings.WOMPI_INTEGRITY_SECRET
    integrity_str = f'{reference}{amount_in_cents}COP{integrity_secret}'
    integrity_signature = hashlib.sha256(integrity_str.encode()).hexdigest()

    base_url = django_settings.FRONTEND_BASE_URL
    redirect_url = ''
    if base_url.startswith('https'):
        redirect_url = f'{base_url}/platform/projects/{proj.id}/payments?payment={payment.id}'

    logger.info(
        'Wompi widget data — ref=%s amount=%s redirect=%s',
        reference, amount_in_cents, redirect_url or '(omitted for dev)',
    )

    data = {
        'public_key': django_settings.WOMPI_PUBLIC_KEY,
        'currency': 'COP',
        'amount_in_cents': amount_in_cents,
        'reference': reference,
        'integrity_signature': integrity_signature,
        'customer_email': proj.client.email,
        'customer_full_name': f'{proj.client.first_name} {proj.client.last_name}'.strip(),
    }
    if redirect_url:
        data['redirect_url'] = redirect_url

    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_card_pay_view(request, project_id, payment_id):
    """
    Process a card payment: tokenize card → create Wompi transaction with installments=1.
    Card data is tokenized server-side to guarantee installments=1 (subscription, no multi-cuota).
    """
    import hashlib
    import time

    from django.conf import settings as django_settings

    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        payment = Payment.objects.select_related('subscription__project__client').get(
            id=payment_id, subscription__project=proj,
        )
    except Payment.DoesNotExist:
        return Response({'detail': 'Pago no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if payment.status not in (Payment.STATUS_PENDING, Payment.STATUS_OVERDUE, Payment.STATUS_FAILED):
        return Response({'detail': 'Este pago no está disponible para cobro.'}, status=status.HTTP_400_BAD_REQUEST)

    card_number = request.data.get('card_number', '')
    exp_month = request.data.get('exp_month', '')
    exp_year = request.data.get('exp_year', '')
    cvc = request.data.get('cvc', '')
    card_holder = request.data.get('card_holder', '')

    if not all([card_number, exp_month, exp_year, cvc, card_holder]):
        return Response({'detail': 'Todos los campos de la tarjeta son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

    from django.utils import timezone as tz

    try:
        from accounts.services.wompi import tokenize_card, get_acceptance_token, create_card_transaction

        card_token = tokenize_card(card_number, exp_month, exp_year, cvc, card_holder)
        acceptance_token = get_acceptance_token()

        ts = int(time.time())
        reference = f'PA{payment.id}P{proj.id}T{ts}'
        amount_in_cents = int(payment.amount * 100)
        integrity_str = f'{reference}{amount_in_cents}COP{django_settings.WOMPI_INTEGRITY_SECRET}'
        signature = hashlib.sha256(integrity_str.encode()).hexdigest()

        txn_data = create_card_transaction(payment, card_token, acceptance_token, reference, signature)

        txn_id = txn_data.get('id', '')
        txn_status = txn_data.get('status', '')

        payment.wompi_transaction_id = str(txn_id)

        if txn_status == 'APPROVED':
            _handle_payment_approved(payment)
        elif txn_status == 'PENDING':
            payment.status = Payment.STATUS_PROCESSING
            payment.save(update_fields=['wompi_transaction_id', 'status'])
        elif txn_status in ('DECLINED', 'ERROR', 'VOIDED'):
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=['wompi_transaction_id', 'status'])

        return Response({
            'payment_id': payment.id,
            'payment_status': payment.status,
            'transaction_id': txn_id,
            'transaction_status': txn_status,
        })

    except Exception as e:
        logger.error('Card payment error for payment %s: %s', payment.id, e)
        return Response(
            {'detail': f'Error procesando el pago: {str(e)}'},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_verify_transaction_view(request, project_id, payment_id):
    """
    After the Wompi widget completes, the frontend calls this endpoint
    with the transaction_id to verify the payment status directly with Wompi
    (needed because webhooks can't reach localhost in dev).
    """
    from django.utils import timezone as tz

    proj, err = _get_project_or_403(request, project_id)
    if err:
        return err

    try:
        payment = Payment.objects.select_related('subscription').get(
            id=payment_id, subscription__project=proj,
        )
    except Payment.DoesNotExist:
        return Response(
            {'detail': 'Pago no encontrado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    transaction_id = request.data.get('transaction_id')
    if not transaction_id:
        return Response(
            {'detail': 'transaction_id es requerido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from accounts.services.wompi import verify_transaction
        txn_data = verify_transaction(str(transaction_id))
    except Exception as e:
        logger.error('Wompi verify error: %s', e)
        return Response(
            {'detail': 'No se pudo verificar la transacción con Wompi.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    txn_status = txn_data.get('status', '')
    payment.wompi_transaction_id = str(transaction_id)

    if txn_status == 'APPROVED':
        _handle_payment_approved(payment)
    elif txn_status in ('DECLINED', 'ERROR', 'VOIDED'):
        payment.status = Payment.STATUS_FAILED
        payment.save(update_fields=['wompi_transaction_id', 'status'])
    else:
        payment.save(update_fields=['wompi_transaction_id'])

    logger.info('Payment %s verified — Wompi status: %s', payment.id, txn_status)

    return Response({
        'payment_id': payment.id,
        'payment_status': payment.status,
        'transaction_status': txn_status,
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def wompi_webhook_view(request):
    """
    Public webhook endpoint for Wompi transaction events.
    Validates signature and updates payment status.
    """
    import json
    from django.utils import timezone as tz

    event = request.data
    event_type = event.get('event')
    data = event.get('data', {})
    transaction = data.get('transaction', {})

    if event_type != 'transaction.updated':
        return Response({'status': 'ignored'})

    transaction_id = transaction.get('id', '')
    transaction_status = transaction.get('status', '')
    reference = transaction.get('reference', '')

    if not transaction_id or not reference:
        return Response({'status': 'missing data'}, status=status.HTTP_400_BAD_REQUEST)

    import re

    payment = None

    try:
        payment = Payment.objects.select_related('subscription').get(
            wompi_payment_link_id=reference,
        )
    except Payment.DoesNotExist:
        pass

    if payment is None:
        match = re.match(r'^PA(\d+)P\d+T\d+$', reference)
        if match:
            try:
                payment = Payment.objects.select_related('subscription').get(id=int(match.group(1)))
            except Payment.DoesNotExist:
                pass

    if payment is None:
        try:
            payment = Payment.objects.select_related('subscription').get(id=int(reference))
        except (ValueError, Payment.DoesNotExist):
            pass

    if payment is None:
        logger.warning('Wompi webhook — payment not found for reference=%s', reference)
        return Response({'status': 'payment not found'}, status=status.HTTP_404_NOT_FOUND)

    payment.wompi_transaction_id = str(transaction_id)

    if transaction_status == 'APPROVED':
        _handle_payment_approved(payment)
    elif transaction_status in ('DECLINED', 'ERROR', 'VOIDED'):
        payment.status = Payment.STATUS_FAILED
        payment.save(update_fields=['wompi_transaction_id', 'status'])
    else:
        payment.save(update_fields=['wompi_transaction_id'])

    return Response({'status': 'ok'})
