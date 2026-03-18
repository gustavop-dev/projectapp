from django.urls import path

from accounts.views import (
    change_request_all_view,
    change_request_comment_view,
    change_request_convert_view,
    change_request_detail_view,
    change_request_evaluate_view,
    change_request_list_view,
    client_detail_view,
    client_list_view,
    client_resend_invite_view,
    complete_profile_view,
    login_view,
    me_view,
    project_detail_view,
    project_list_view,
    requirement_comment_view,
    requirement_detail_view,
    requirement_list_view,
    requirement_move_view,
    resend_code_view,
    token_refresh_view,
    verify_view,
)

urlpatterns = [
    # Auth
    path('login/', login_view, name='platform-login'),
    path('verify/', verify_view, name='platform-verify'),
    path('resend-code/', resend_code_view, name='platform-resend-code'),
    path('token/refresh/', token_refresh_view, name='platform-token-refresh'),

    # Profile
    path('me/', me_view, name='platform-me'),
    path('me/complete-profile/', complete_profile_view, name='platform-complete-profile'),

    # Admin — client management
    path('clients/', client_list_view, name='platform-client-list'),
    path('clients/<int:user_id>/', client_detail_view, name='platform-client-detail'),
    path('clients/<int:user_id>/resend-invite/', client_resend_invite_view, name='platform-client-resend-invite'),

    # Projects
    path('projects/', project_list_view, name='platform-project-list'),
    path('projects/<int:project_id>/', project_detail_view, name='platform-project-detail'),

    # Requirements (Kanban board)
    path('projects/<int:project_id>/requirements/', requirement_list_view, name='platform-requirement-list'),
    path('projects/<int:project_id>/requirements/<int:req_id>/', requirement_detail_view, name='platform-requirement-detail'),
    path('projects/<int:project_id>/requirements/<int:req_id>/move/', requirement_move_view, name='platform-requirement-move'),
    path('projects/<int:project_id>/requirements/<int:req_id>/comments/', requirement_comment_view, name='platform-requirement-comments'),

    # Change Requests
    path('change-requests/', change_request_all_view, name='platform-change-request-all'),
    path('projects/<int:project_id>/change-requests/', change_request_list_view, name='platform-change-request-list'),
    path('projects/<int:project_id>/change-requests/<int:cr_id>/', change_request_detail_view, name='platform-change-request-detail'),
    path('projects/<int:project_id>/change-requests/<int:cr_id>/evaluate/', change_request_evaluate_view, name='platform-change-request-evaluate'),
    path('projects/<int:project_id>/change-requests/<int:cr_id>/comments/', change_request_comment_view, name='platform-change-request-comments'),
    path('projects/<int:project_id>/change-requests/<int:cr_id>/convert/', change_request_convert_view, name='platform-change-request-convert'),
]
