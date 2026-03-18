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

    project = Project.objects.create(
        name=data['name'],
        description=data.get('description', ''),
        client_id=data['client_id'],
        status=data.get('status', Project.STATUS_ACTIVE),
        progress=data.get('progress', 0),
        start_date=data.get('start_date'),
        estimated_end_date=data.get('estimated_end_date'),
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
        status=data.get('status', Requirement.STATUS_BACKLOG),
        priority=data.get('priority', Requirement.PRIORITY_MEDIUM),
        estimated_hours=data.get('estimated_hours'),
        module=data.get('module', ''),
        order=max_order,
    )

    _recalculate_project_progress(proj)
    return Response(RequirementListSerializer(req).data, status=status.HTTP_201_CREATED)


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
        status=Requirement.STATUS_TODO,
        priority=cr.suggested_priority,
        module=cr.module_or_screen,
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
