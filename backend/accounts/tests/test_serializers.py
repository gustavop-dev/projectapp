from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from accounts.models import (
    BugReport,
    ChangeRequest,
    Deliverable,
    DeliverableClientFolder,
    DeliverableClientUpload,
    DeliverableFile,
    DeliverableVersion,
    Project,
    Requirement,
    RequirementComment,
    RequirementHistory,
    UserProfile,
)
from accounts.serializers import (
    BugReportDetailSerializer,
    BugReportListSerializer,
    ChangeRequestDetailSerializer,
    ChangeRequestListSerializer,
    ClientListSerializer,
    CompleteProfileSerializer,
    CreateAdminSerializer,
    CreateBugReportSerializer,
    CreateClientSerializer,
    CreateCommentSerializer,
    CreateProjectSerializer,
    CreateRequirementSerializer,
    DeliverableClientUploadSerializer,
    DeliverableFileSerializer,
    DeliverableListSerializer,
    DeliverableVersionSerializer,
    EvaluateBugReportSerializer,
    LoginSerializer,
    MoveRequirementSerializer,
    ProjectListSerializer,
    RequirementCommentSerializer,
    RequirementDetailSerializer,
    RequirementHistorySerializer,
    RequirementListSerializer,
    UpdateClientSerializer,
    UpdateProfileSerializer,
    UpdateProjectSerializer,
    UpdateRequirementSerializer,
    UserProfileSerializer,
    VerifyOnboardingSerializer,
)

User = get_user_model()
factory = APIRequestFactory()


# =========================================================================
# LoginSerializer
# =========================================================================

class TestLoginSerializer:
    def test_valid_data_passes_validation(self):
        serializer = LoginSerializer(data={'email': 'a@b.com', 'password': 'secret'})

        assert serializer.is_valid() is True

    def test_missing_email_fails_validation(self):
        serializer = LoginSerializer(data={'password': 'secret'})

        assert serializer.is_valid() is False
        assert 'email' in serializer.errors

    def test_missing_password_fails_validation(self):
        serializer = LoginSerializer(data={'email': 'a@b.com'})

        assert serializer.is_valid() is False
        assert 'password' in serializer.errors

    def test_invalid_email_format_fails_validation(self):
        serializer = LoginSerializer(data={'email': 'not-an-email', 'password': 'x'})

        assert serializer.is_valid() is False
        assert 'email' in serializer.errors


# =========================================================================
# VerifyOnboardingSerializer
# =========================================================================

class TestVerifyOnboardingSerializer:
    def test_valid_data_passes_validation(self):
        serializer = VerifyOnboardingSerializer(
            data={'code': '123456', 'new_password': 'MySecure1!'},
        )

        assert serializer.is_valid() is True

    def test_code_too_short_fails_validation(self):
        serializer = VerifyOnboardingSerializer(
            data={'code': '123', 'new_password': 'MySecure1!'},
        )

        assert serializer.is_valid() is False
        assert 'code' in serializer.errors

    def test_password_too_short_fails_validation(self):
        serializer = VerifyOnboardingSerializer(
            data={'code': '123456', 'new_password': 'short'},
        )

        assert serializer.is_valid() is False
        assert 'new_password' in serializer.errors


# =========================================================================
# CompleteProfileSerializer
# =========================================================================

class TestCompleteProfileSerializer:
    VALID_DATA = {
        'company_name': 'ACME Corp',
        'phone': '+57 300 111 2222',
        'cedula': '1234567890',
        'date_of_birth': '1990-05-15',
        'gender': 'male',
        'education_level': 'universitario',
    }

    def test_valid_data_passes_validation(self):
        serializer = CompleteProfileSerializer(data=self.VALID_DATA)

        assert serializer.is_valid() is True

    def test_missing_cedula_fails_validation(self):
        data = {**self.VALID_DATA}
        del data['cedula']
        serializer = CompleteProfileSerializer(data=data)

        assert serializer.is_valid() is False
        assert 'cedula' in serializer.errors

    def test_blank_cedula_fails_custom_validation(self):
        data = {**self.VALID_DATA, 'cedula': '   '}
        serializer = CompleteProfileSerializer(data=data)

        assert serializer.is_valid() is False
        assert 'cedula' in serializer.errors

    def test_blank_phone_fails_custom_validation(self):
        data = {**self.VALID_DATA, 'phone': '   '}
        serializer = CompleteProfileSerializer(data=data)

        assert serializer.is_valid() is False
        assert 'phone' in serializer.errors

    def test_invalid_gender_choice_fails_validation(self):
        data = {**self.VALID_DATA, 'gender': 'invalid_choice'}
        serializer = CompleteProfileSerializer(data=data)

        assert serializer.is_valid() is False
        assert 'gender' in serializer.errors

    def test_invalid_education_level_fails_validation(self):
        data = {**self.VALID_DATA, 'education_level': 'phd'}
        serializer = CompleteProfileSerializer(data=data)

        assert serializer.is_valid() is False
        assert 'education_level' in serializer.errors

    def test_avatar_is_optional(self):
        serializer = CompleteProfileSerializer(data=self.VALID_DATA)

        assert serializer.is_valid() is True
        assert serializer.validated_data.get('avatar') is None


# =========================================================================
# CreateClientSerializer
# =========================================================================

@pytest.mark.django_db
class TestCreateClientSerializer:
    def test_valid_data_passes_validation(self):
        serializer = CreateClientSerializer(data={
            'email': 'new@client.com',
            'first_name': 'New',
            'last_name': 'Client',
        })

        assert serializer.is_valid() is True

    def test_duplicate_email_fails_validation(self):
        User.objects.create_user(
            username='exist@test.com', email='exist@test.com', password='pass',
        )
        serializer = CreateClientSerializer(data={
            'email': 'exist@test.com',
            'first_name': 'A',
            'last_name': 'B',
        })

        assert serializer.is_valid() is False
        assert 'email' in serializer.errors

    def test_email_normalized_to_lowercase(self):
        serializer = CreateClientSerializer(data={
            'email': '  UPPER@Example.COM  ',
            'first_name': 'A',
            'last_name': 'B',
        })

        assert serializer.is_valid() is True
        assert serializer.validated_data['email'] == 'upper@example.com'


# =========================================================================
# UpdateClientSerializer
# =========================================================================

class TestUpdateClientSerializer:
    def test_partial_update_with_single_field(self):
        serializer = UpdateClientSerializer(data={'first_name': 'Updated'})

        assert serializer.is_valid() is True
        assert serializer.validated_data == {'first_name': 'Updated'}

    def test_is_active_boolean_field(self):
        serializer = UpdateClientSerializer(data={'is_active': False})

        assert serializer.is_valid() is True
        assert serializer.validated_data['is_active'] is False


# =========================================================================
# UpdateProfileSerializer
# =========================================================================

class TestUpdateProfileSerializer:
    def test_valid_partial_update(self):
        serializer = UpdateProfileSerializer(data={
            'first_name': 'Updated',
            'gender': 'female',
        })

        assert serializer.is_valid() is True

    def test_invalid_gender_choice_fails(self):
        serializer = UpdateProfileSerializer(data={'gender': 'xyz'})

        assert serializer.is_valid() is False
        assert 'gender' in serializer.errors

    def test_empty_payload_is_valid(self):
        serializer = UpdateProfileSerializer(data={})

        assert serializer.is_valid() is True


# =========================================================================
# CreateProjectSerializer
# =========================================================================

@pytest.mark.django_db
class TestCreateProjectSerializer:
    @pytest.fixture
    def client_user(self):
        user = User.objects.create_user(
            username='cli@test.com', email='cli@test.com', password='pass',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
        return user

    def test_valid_data_passes_validation(self, client_user):
        serializer = CreateProjectSerializer(data={
            'name': 'Test Project',
            'client_id': client_user.id,
        })

        assert serializer.is_valid() is True

    def test_nonexistent_client_id_fails_validation(self):
        serializer = CreateProjectSerializer(data={
            'name': 'Test',
            'client_id': 99999,
        })

        assert serializer.is_valid() is False
        assert 'client_id' in serializer.errors

    def test_admin_as_client_fails_validation(self):
        admin = User.objects.create_user(
            username='adm@test.com', email='adm@test.com', password='pass',
        )
        UserProfile.objects.create(user=admin, role=UserProfile.ROLE_ADMIN)

        serializer = CreateProjectSerializer(data={
            'name': 'Test',
            'client_id': admin.id,
        })

        assert serializer.is_valid() is False
        assert 'client_id' in serializer.errors

    def test_invalid_status_choice_fails_validation(self, client_user):
        serializer = CreateProjectSerializer(data={
            'name': 'Test',
            'client_id': client_user.id,
            'status': 'nonexistent',
        })

        assert serializer.is_valid() is False
        assert 'status' in serializer.errors

    def test_progress_out_of_range_fails_validation(self, client_user):
        serializer = CreateProjectSerializer(data={
            'name': 'Test',
            'client_id': client_user.id,
            'progress': 150,
        })

        assert serializer.is_valid() is False
        assert 'progress' in serializer.errors


# =========================================================================
# UpdateProjectSerializer
# =========================================================================

class TestUpdateProjectSerializer:
    def test_partial_update_valid(self):
        serializer = UpdateProjectSerializer(data={'name': 'New Name'})

        assert serializer.is_valid() is True

    def test_invalid_status_fails(self):
        serializer = UpdateProjectSerializer(data={'status': 'bad'})

        assert serializer.is_valid() is False
        assert 'status' in serializer.errors


# =========================================================================
# CreateRequirementSerializer
# =========================================================================

class TestCreateRequirementSerializer:
    def test_valid_minimal_data(self):
        serializer = CreateRequirementSerializer(data={'title': 'Build login page'})

        assert serializer.is_valid() is True

    def test_invalid_priority_fails(self):
        serializer = CreateRequirementSerializer(data={
            'title': 'Test',
            'priority': 'ultra',
        })

        assert serializer.is_valid() is False
        assert 'priority' in serializer.errors

    def test_missing_title_fails(self):
        serializer = CreateRequirementSerializer(data={'description': 'No title'})

        assert serializer.is_valid() is False
        assert 'title' in serializer.errors


# =========================================================================
# UpdateRequirementSerializer
# =========================================================================

class TestUpdateRequirementSerializer:
    def test_partial_update_status(self):
        serializer = UpdateRequirementSerializer(data={'status': 'in_progress'})

        assert serializer.is_valid() is True

    def test_invalid_status_fails(self):
        serializer = UpdateRequirementSerializer(data={'status': 'invalid'})

        assert serializer.is_valid() is False

    def test_negative_order_fails(self):
        serializer = UpdateRequirementSerializer(data={'order': -1})

        assert serializer.is_valid() is False
        assert 'order' in serializer.errors


# =========================================================================
# MoveRequirementSerializer
# =========================================================================

class TestMoveRequirementSerializer:
    def test_valid_move(self):
        serializer = MoveRequirementSerializer(data={'status': 'done', 'order': 0})

        assert serializer.is_valid() is True

    def test_missing_status_fails(self):
        serializer = MoveRequirementSerializer(data={'order': 0})

        assert serializer.is_valid() is False
        assert 'status' in serializer.errors


# =========================================================================
# CreateCommentSerializer
# =========================================================================

class TestCreateCommentSerializer:
    def test_valid_comment(self):
        serializer = CreateCommentSerializer(data={'content': 'Hello'})

        assert serializer.is_valid() is True
        assert serializer.validated_data['is_internal'] is False

    def test_internal_comment_flag(self):
        serializer = CreateCommentSerializer(
            data={'content': 'Internal note', 'is_internal': True},
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data['is_internal'] is True

    def test_empty_content_fails(self):
        serializer = CreateCommentSerializer(data={'content': ''})

        assert serializer.is_valid() is False
        assert 'content' in serializer.errors


# =========================================================================
# ClientListSerializer (ModelSerializer output)
# =========================================================================

@pytest.mark.django_db
class TestClientListSerializer:
    def test_serializes_client_profile_correctly(self):
        user = User.objects.create_user(
            username='cl@test.com', email='cl@test.com', password='pass',
            first_name='Carlos', last_name='López',
        )
        profile = UserProfile.objects.create(
            user=user, role=UserProfile.ROLE_CLIENT,
            company_name='Tech Corp', phone='+57 300',
            is_onboarded=True,
        )

        data = ClientListSerializer(profile).data

        assert data['email'] == 'cl@test.com'
        assert data['first_name'] == 'Carlos'
        assert data['last_name'] == 'López'
        assert data['company_name'] == 'Tech Corp'
        assert data['is_onboarded'] is True
        assert data['user_id'] == user.id


# =========================================================================
# ProjectListSerializer (ModelSerializer output)
# =========================================================================

@pytest.mark.django_db
class TestProjectListSerializer:
    def test_serializes_project_with_client_info(self):
        user = User.objects.create_user(
            username='pj@test.com', email='pj@test.com', password='pass',
            first_name='Maria', last_name='García',
        )
        UserProfile.objects.create(
            user=user, role=UserProfile.ROLE_CLIENT, company_name='ACME',
        )
        project = Project.objects.create(
            name='Website Redesign', client=user, status=Project.STATUS_ACTIVE,
        )

        data = ProjectListSerializer(project).data

        assert data['name'] == 'Website Redesign'
        assert data['client_name'] == 'Maria García'
        assert data['client_email'] == 'pj@test.com'
        assert data['client_company'] == 'ACME'

    def test_client_name_falls_back_to_email(self):
        user = User.objects.create_user(
            username='fb@test.com', email='fb@test.com', password='pass',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=user)

        data = ProjectListSerializer(project).data

        assert data['client_name'] == 'fb@test.com'


# =========================================================================
# RequirementDetailSerializer — internal comment filtering
# =========================================================================

@pytest.mark.django_db
class TestRequirementDetailSerializer:
    @pytest.fixture
    def setup_data(self):
        admin = User.objects.create_user(
            username='adm@test.com', email='adm@test.com', password='pass',
        )
        admin_profile = UserProfile.objects.create(
            user=admin, role=UserProfile.ROLE_ADMIN,
        )
        client = User.objects.create_user(
            username='cli@test.com', email='cli@test.com', password='pass',
        )
        client_profile = UserProfile.objects.create(
            user=client, role=UserProfile.ROLE_CLIENT,
        )
        project = Project.objects.create(name='P', client=client)
        d = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        req = Requirement.objects.create(deliverable=d, title='Card')
        RequirementComment.objects.create(
            requirement=req, user=admin, content='Public', is_internal=False,
        )
        RequirementComment.objects.create(
            requirement=req, user=admin, content='Secret', is_internal=True,
        )
        return req, admin, client

    def test_admin_sees_internal_comments(self, setup_data):
        req, admin, _ = setup_data
        request = factory.get('/')
        request.user = admin

        data = RequirementDetailSerializer(req, context={'request': request}).data

        assert len(data['comments']) == 2

    def test_client_does_not_see_internal_comments(self, setup_data):
        req, _, client = setup_data
        request = factory.get('/')
        request.user = client

        data = RequirementDetailSerializer(req, context={'request': request}).data

        assert len(data['comments']) == 1
        assert data['comments'][0]['content'] == 'Public'


# =========================================================================
# RequirementCommentSerializer
# =========================================================================

@pytest.mark.django_db
class TestRequirementCommentSerializer:
    def test_user_name_falls_back_to_email(self):
        user = User.objects.create_user(
            username='nofn@test.com', email='nofn@test.com', password='pass',
        )
        client = User.objects.create_user(
            username='own2@test.com', email='own2@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        d = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        req = Requirement.objects.create(deliverable=d, title='R')
        comment = RequirementComment.objects.create(
            requirement=req, user=user, content='Note',
        )

        data = RequirementCommentSerializer(comment).data

        assert data['user_name'] == 'nofn@test.com'

    def test_serializes_comment_with_user_name(self):
        user = User.objects.create_user(
            username='cm@test.com', email='cm@test.com', password='pass',
            first_name='Juan', last_name='Pérez',
        )
        client = User.objects.create_user(
            username='owner@test.com', email='owner@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        d = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        req = Requirement.objects.create(deliverable=d, title='R')
        comment = RequirementComment.objects.create(
            requirement=req, user=user, content='Note',
        )

        data = RequirementCommentSerializer(comment).data

        assert data['user_name'] == 'Juan Pérez'
        assert data['user_email'] == 'cm@test.com'
        assert data['content'] == 'Note'


# =========================================================================
# UserProfileSerializer (output)
# =========================================================================

@pytest.mark.django_db
class TestUserProfileSerializer:
    def test_serializes_full_profile_fields(self):
        user = User.objects.create_user(
            username='ups@test.com', email='ups@test.com', password='pass',
            first_name='Laura', last_name='Ríos',
        )
        profile = UserProfile.objects.create(
            user=user, role=UserProfile.ROLE_CLIENT,
            company_name='LauraInc', phone='+57 300',
            is_onboarded=True, profile_completed=True,
            cedula='1234567890', gender='female',
            education_level='universitario',
        )
        request = factory.get('/')

        data = UserProfileSerializer(profile, context={'request': request}).data

        assert data['email'] == 'ups@test.com'
        assert data['first_name'] == 'Laura'
        assert data['last_name'] == 'Ríos'
        assert data['user_id'] == user.id
        assert data['role'] == 'client'
        assert data['company_name'] == 'LauraInc'
        assert data['is_onboarded'] is True
        assert data['profile_completed'] is True
        assert data['cedula'] == '1234567890'
        assert data['gender'] == 'female'
        assert data['education_level'] == 'universitario'

    def test_avatar_display_url_returns_empty_when_no_avatar(self):
        user = User.objects.create_user(
            username='noav2@test.com', email='noav2@test.com', password='pass',
        )
        profile = UserProfile.objects.create(user=user)
        request = factory.get('/')

        data = UserProfileSerializer(profile, context={'request': request}).data

        assert data['avatar_display_url'] == ''

    def test_avatar_display_url_returns_absolute_url_for_avatar_url_field(self):
        user = User.objects.create_user(
            username='avurl@test.com', email='avurl@test.com', password='pass',
        )
        profile = UserProfile.objects.create(
            user=user, avatar_url='https://cdn.example.com/pic.jpg',
        )
        request = factory.get('/')

        data = UserProfileSerializer(profile, context={'request': request}).data

        assert data['avatar_display_url'] == 'https://cdn.example.com/pic.jpg'


# =========================================================================
# RequirementHistorySerializer (output)
# =========================================================================

@pytest.mark.django_db
class TestRequirementHistorySerializer:
    def test_serializes_history_entry(self):
        admin = User.objects.create_user(
            username='ha@test.com', email='ha@test.com', password='pass',
        )
        client = User.objects.create_user(
            username='hc@test.com', email='hc@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        d = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        req = Requirement.objects.create(deliverable=d, title='R')
        history = RequirementHistory.objects.create(
            requirement=req, from_status='todo',
            to_status='in_progress', changed_by=admin,
        )

        data = RequirementHistorySerializer(history).data

        assert data['from_status'] == 'todo'
        assert data['to_status'] == 'in_progress'
        assert data['changed_by_email'] == 'ha@test.com'
        assert 'created_at' in data


# =========================================================================
# RequirementListSerializer.get_comments_count
# =========================================================================

@pytest.mark.django_db
class TestRequirementListSerializerCommentsCount:
    def test_comments_count_reflects_actual_count(self):
        user = User.objects.create_user(
            username='cc@test.com', email='cc@test.com', password='pass',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=user)
        d = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=user,
        )
        req = Requirement.objects.create(deliverable=d, title='R')
        RequirementComment.objects.create(requirement=req, user=user, content='A')
        RequirementComment.objects.create(requirement=req, user=user, content='B')

        data = RequirementListSerializer(req).data

        assert data['comments_count'] == 2

    def test_comments_count_zero_when_no_comments(self):
        user = User.objects.create_user(
            username='cc0@test.com', email='cc0@test.com', password='pass',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=user)
        d = Deliverable.objects.create(
            project=project, title='D', category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=user,
        )
        req = Requirement.objects.create(deliverable=d, title='R')

        data = RequirementListSerializer(req).data

        assert data['comments_count'] == 0


# =========================================================================
# CreateAdminSerializer — duplicate email validation (line 127)
# =========================================================================

@pytest.mark.django_db
class TestCreateAdminSerializer:
    def test_duplicate_email_fails_validation(self):
        User.objects.create_user(
            username='addup@test.com', email='addup@test.com', password='pass',
        )
        serializer = CreateAdminSerializer(data={
            'email': 'addup@test.com',
            'first_name': 'A',
            'last_name': 'B',
        })

        assert serializer.is_valid() is False
        assert 'email' in serializer.errors

    def test_email_normalized_to_lowercase(self):
        serializer = CreateAdminSerializer(data={
            'email': '  NEWADMIN@TEST.COM  ',
            'first_name': 'A',
            'last_name': 'B',
        })

        assert serializer.is_valid() is True
        assert serializer.validated_data['email'] == 'newadmin@test.com'


# =========================================================================
# ClientListSerializer.get_avatar_display_url — relative URL with request (line 173)
# =========================================================================

@pytest.mark.django_db
class TestClientListSerializerAvatarUrl:
    def test_avatar_display_url_builds_absolute_for_relative_url(self):
        user = User.objects.create_user(
            username='avtest@test.com', email='avtest@test.com', password='pass',
        )
        profile = UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

        with patch.object(
            type(profile), 'avatar_display_url',
            new_callable=PropertyMock,
            return_value='/media/avatars/pic.jpg',
        ):
            request = factory.get('/')
            data = ClientListSerializer(profile, context={'request': request}).data

        assert data['avatar_display_url'].startswith('http')


# =========================================================================
# CreateProjectSerializer.validate_proposal_id — already linked (line 272)
# =========================================================================

@pytest.mark.django_db
class TestCreateProjectSerializerProposalValidation:
    def test_proposal_already_linked_to_deliverable_fails(self):
        from content.models import BusinessProposal

        client = User.objects.create_user(
            username='pvcli@test.com', email='pvcli@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='Linked', client=client)
        deliverable = Deliverable.objects.create(
            project=project, title='D',
            category=Deliverable.CATEGORY_OTHER,
            file=None, uploaded_by=client,
        )
        proposal = BusinessProposal.objects.create(
            title='Linked Proposal', client_name='Client',
            client_email='c@t.com', status='accepted',
            deliverable=deliverable,
        )

        serializer = CreateProjectSerializer(data={
            'name': 'New Project',
            'client_id': client.id,
            'proposal_id': proposal.id,
        })

        assert serializer.is_valid() is False
        assert 'proposal_id' in serializer.errors


# =========================================================================
# ChangeRequestListSerializer.get_screenshot_url (lines 441-443)
# ChangeRequestDetailSerializer.get_screenshot_url (lines 479-483)
# =========================================================================

class TestChangeRequestSerializerScreenshotUrl:
    def test_list_serializer_returns_http_url_directly(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = MagicMock()
        mock_obj.screenshot.url = 'https://cdn.example.com/shot.png'

        s = ChangeRequestListSerializer()
        result = s.get_screenshot_url(mock_obj)

        assert result == 'https://cdn.example.com/shot.png'

    def test_list_serializer_returns_none_when_no_screenshot(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = None

        s = ChangeRequestListSerializer()
        result = s.get_screenshot_url(mock_obj)

        assert result is None

    def test_list_serializer_builds_absolute_with_request(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = MagicMock()
        mock_obj.screenshot.url = '/media/shot.png'

        request = factory.get('/')
        s = ChangeRequestListSerializer(context={'request': request})
        result = s.get_screenshot_url(mock_obj)

        assert result.startswith('http')

    def test_detail_serializer_returns_http_url_directly(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = MagicMock()
        mock_obj.screenshot.url = 'https://cdn.example.com/shot.png'

        s = ChangeRequestDetailSerializer()
        result = s.get_screenshot_url(mock_obj)

        assert result == 'https://cdn.example.com/shot.png'

    def test_detail_serializer_returns_none_when_no_screenshot(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = None

        s = ChangeRequestDetailSerializer()
        result = s.get_screenshot_url(mock_obj)

        assert result is None

    def test_detail_serializer_builds_absolute_with_request(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = MagicMock()
        mock_obj.screenshot.url = '/media/shot.png'

        request = factory.get('/')
        s = ChangeRequestDetailSerializer(context={'request': request})
        result = s.get_screenshot_url(mock_obj)

        assert result.startswith('http')


# =========================================================================
# BugReportListSerializer.get_screenshot_url (lines 562-566)
# BugReportDetailSerializer.get_screenshot_url (lines 603-609)
# =========================================================================

class TestBugReportSerializerScreenshotUrl:
    def test_list_serializer_returns_http_url_directly(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = MagicMock()
        mock_obj.screenshot.url = 'https://cdn.example.com/bug.png'

        s = BugReportListSerializer()
        result = s.get_screenshot_url(mock_obj)

        assert result == 'https://cdn.example.com/bug.png'

    def test_list_serializer_returns_none_when_no_screenshot(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = None

        s = BugReportListSerializer()
        result = s.get_screenshot_url(mock_obj)

        assert result is None

    def test_list_serializer_builds_absolute_with_request(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = MagicMock()
        mock_obj.screenshot.url = '/media/bug.png'

        request = factory.get('/')
        s = BugReportListSerializer(context={'request': request})
        result = s.get_screenshot_url(mock_obj)

        assert result.startswith('http')

    def test_detail_serializer_returns_http_url_directly(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = MagicMock()
        mock_obj.screenshot.url = 'https://cdn.example.com/bug.png'

        s = BugReportDetailSerializer()
        result = s.get_screenshot_url(mock_obj)

        assert result == 'https://cdn.example.com/bug.png'

    def test_detail_serializer_returns_none_when_no_screenshot(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = None

        s = BugReportDetailSerializer()
        result = s.get_screenshot_url(mock_obj)

        assert result is None

    def test_detail_serializer_builds_absolute_with_request(self):
        mock_obj = MagicMock()
        mock_obj.screenshot = MagicMock()
        mock_obj.screenshot.url = '/media/bug.png'

        request = factory.get('/')
        s = BugReportDetailSerializer(context={'request': request})
        result = s.get_screenshot_url(mock_obj)

        assert result.startswith('http')


# =========================================================================
# CreateBugReportSerializer.validate_deliverable_id — no project context (line 634)
# =========================================================================

@pytest.mark.django_db
class TestCreateBugReportSerializerValidation:
    def test_no_project_context_raises_validation_error(self):
        serializer = CreateBugReportSerializer(
            data={'deliverable_id': 1, 'title': 'Bug'},
            context={},  # no 'project' key
        )

        assert serializer.is_valid() is False
        assert 'deliverable_id' in serializer.errors

    def test_deliverable_not_in_project_fails(self):
        client = User.objects.create_user(
            username='bugcli@test.com', email='bugcli@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        other_project = Project.objects.create(name='Other', client=client)
        deliverable = Deliverable.objects.create(
            project=other_project, title='D',
            category=Deliverable.CATEGORY_OTHER, file=None, uploaded_by=client,
        )

        serializer = CreateBugReportSerializer(
            data={'deliverable_id': deliverable.id, 'title': 'Bug'},
            context={'project': project},
        )

        assert serializer.is_valid() is False
        assert 'deliverable_id' in serializer.errors


# =========================================================================
# EvaluateBugReportSerializer.validate — linked_bug not found (line 653),
# linked_bug archived (line 655)
# =========================================================================

@pytest.mark.django_db
class TestEvaluateBugReportSerializerValidation:
    @pytest.fixture
    def deliverable_with_bug(self):
        client = User.objects.create_user(
            username='evbug@test.com', email='evbug@test.com', password='pass',
        )
        UserProfile.objects.create(user=client, role=UserProfile.ROLE_CLIENT)
        project = Project.objects.create(name='P', client=client)
        deliverable = Deliverable.objects.create(
            project=project, title='D',
            category=Deliverable.CATEGORY_OTHER, file=None, uploaded_by=client,
        )
        bug = BugReport.objects.create(
            deliverable=deliverable, reported_by=client,
            title='Main bug', severity=BugReport.SEVERITY_MEDIUM,
        )
        return deliverable, bug

    def test_nonexistent_linked_bug_fails(self, deliverable_with_bug):
        _, bug = deliverable_with_bug
        serializer = EvaluateBugReportSerializer(
            data={'status': BugReport.STATUS_REPORTED, 'linked_bug_id': 99999},
            context={'bug': bug},
        )

        assert serializer.is_valid() is False
        assert 'linked_bug_id' in serializer.errors

    def test_archived_linked_bug_fails(self, deliverable_with_bug):
        deliverable, bug = deliverable_with_bug
        archived_bug = BugReport.objects.create(
            deliverable=deliverable, reported_by=bug.reported_by,
            title='Archived bug', severity=BugReport.SEVERITY_MEDIUM,
            is_archived=True,
        )
        serializer = EvaluateBugReportSerializer(
            data={'status': BugReport.STATUS_REPORTED, 'linked_bug_id': archived_bug.id},
            context={'bug': bug},
        )

        assert serializer.is_valid() is False
        assert 'linked_bug_id' in serializer.errors

    def test_valid_linked_bug_passes(self, deliverable_with_bug):
        deliverable, bug = deliverable_with_bug
        other_bug = BugReport.objects.create(
            deliverable=deliverable, reported_by=bug.reported_by,
            title='Other bug', severity=BugReport.SEVERITY_MEDIUM,
        )
        serializer = EvaluateBugReportSerializer(
            data={'status': BugReport.STATUS_REPORTED, 'linked_bug_id': other_bug.id},
            context={'bug': bug},
        )

        assert serializer.is_valid() is True


# =========================================================================
# DeliverableVersionSerializer.get_file_url (lines 701, 706)
# DeliverableListSerializer.get_file_url (lines 733, 738)
# DeliverableFileSerializer (lines 753-763)
# DeliverableClientUploadSerializer.get_file_url (lines 784-786)
# =========================================================================

class TestDeliverableSerializerFileUrls:
    def test_version_serializer_builds_absolute_url_with_request(self):
        mock_version = MagicMock()
        mock_version.file = MagicMock()
        mock_version.file.url = '/media/versions/file.pdf'

        request = factory.get('/')
        s = DeliverableVersionSerializer(context={'request': request})
        result = s.get_file_url(mock_version)

        assert result.startswith('http')

    def test_version_serializer_returns_http_url_directly(self):
        mock_version = MagicMock()
        mock_version.file = MagicMock()
        mock_version.file.url = 'https://cdn.example.com/file.pdf'

        s = DeliverableVersionSerializer()
        result = s.get_file_url(mock_version)

        assert result == 'https://cdn.example.com/file.pdf'

    def test_version_serializer_returns_none_when_no_file(self):
        mock_version = MagicMock()
        mock_version.file = None

        s = DeliverableVersionSerializer()
        result = s.get_file_url(mock_version)

        assert result is None

    def test_list_serializer_builds_absolute_url_with_request(self):
        mock_deliverable = MagicMock()
        mock_deliverable.file = MagicMock()
        mock_deliverable.file.url = '/media/deliverables/file.pdf'

        request = factory.get('/')
        s = DeliverableListSerializer(context={'request': request})
        result = s.get_file_url(mock_deliverable)

        assert result.startswith('http')

    def test_list_serializer_returns_http_url_directly(self):
        mock_deliverable = MagicMock()
        mock_deliverable.file = MagicMock()
        mock_deliverable.file.url = 'https://cdn.example.com/file.pdf'

        s = DeliverableListSerializer()
        result = s.get_file_url(mock_deliverable)

        assert result == 'https://cdn.example.com/file.pdf'

    def test_file_serializer_returns_none_when_no_file(self):
        mock_file = MagicMock()
        mock_file.file = None

        s = DeliverableFileSerializer()
        result = s.get_file_url(mock_file)

        assert result is None

    def test_file_serializer_builds_absolute_url_with_request(self):
        mock_file = MagicMock()
        mock_file.file = MagicMock()
        mock_file.file.url = '/media/files/attachment.pdf'

        request = factory.get('/')
        s = DeliverableFileSerializer(context={'request': request})
        result = s.get_file_url(mock_file)

        assert result.startswith('http')

    def test_file_serializer_get_uploaded_by_name(self):
        mock_file = MagicMock()
        mock_file.uploaded_by.first_name = 'Ana'
        mock_file.uploaded_by.last_name = 'García'
        mock_file.uploaded_by.email = 'ana@test.com'

        s = DeliverableFileSerializer()
        result = s.get_uploaded_by_name(mock_file)

        assert result == 'Ana García'

    def test_client_upload_serializer_returns_none_when_no_file(self):
        mock_upload = MagicMock()
        mock_upload.file = None

        s = DeliverableClientUploadSerializer()
        result = s.get_file_url(mock_upload)

        assert result is None

    def test_client_upload_serializer_builds_absolute_url_with_request(self):
        mock_upload = MagicMock()
        mock_upload.file = MagicMock()
        mock_upload.file.url = '/media/uploads/doc.pdf'

        request = factory.get('/')
        s = DeliverableClientUploadSerializer(context={'request': request})
        result = s.get_file_url(mock_upload)

        assert result.startswith('http')
