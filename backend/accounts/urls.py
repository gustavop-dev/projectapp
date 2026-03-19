from django.urls import path

from accounts.views import (
    bug_report_all_view,
    bug_report_comment_view,
    bug_report_detail_view,
    bug_report_evaluate_view,
    bug_report_list_view,
    change_request_all_view,
    deliverable_all_view,
    deliverable_detail_view,
    deliverable_list_view,
    deliverable_upload_version_view,
    notification_list_view,
    notification_mark_all_read_view,
    notification_mark_read_view,
    notification_unread_count_view,
    payment_generate_link_view,
    payment_verify_transaction_view,
    payment_widget_data_view,
    project_payments_view,
    project_subscription_view,
    proposal_list_for_selector_view,
    subscription_list_view,
    wompi_webhook_view,
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

    # Bug Reports
    path('bug-reports/', bug_report_all_view, name='platform-bug-report-all'),
    path('projects/<int:project_id>/bug-reports/', bug_report_list_view, name='platform-bug-report-list'),
    path('projects/<int:project_id>/bug-reports/<int:bug_id>/', bug_report_detail_view, name='platform-bug-report-detail'),
    path('projects/<int:project_id>/bug-reports/<int:bug_id>/evaluate/', bug_report_evaluate_view, name='platform-bug-report-evaluate'),
    path('projects/<int:project_id>/bug-reports/<int:bug_id>/comments/', bug_report_comment_view, name='platform-bug-report-comments'),

    # Deliverables
    path('deliverables/', deliverable_all_view, name='platform-deliverable-all'),
    path('projects/<int:project_id>/deliverables/', deliverable_list_view, name='platform-deliverable-list'),
    path('projects/<int:project_id>/deliverables/<int:deliverable_id>/', deliverable_detail_view, name='platform-deliverable-detail'),
    path('projects/<int:project_id>/deliverables/<int:deliverable_id>/upload-version/', deliverable_upload_version_view, name='platform-deliverable-upload-version'),

    # Notifications
    path('notifications/', notification_list_view, name='platform-notification-list'),
    path('notifications/unread-count/', notification_unread_count_view, name='platform-notification-unread-count'),
    path('notifications/<int:notification_id>/read/', notification_mark_read_view, name='platform-notification-mark-read'),
    path('notifications/mark-all-read/', notification_mark_all_read_view, name='platform-notification-mark-all-read'),

    # Payments & Subscriptions
    path('proposals/', proposal_list_for_selector_view, name='platform-proposal-list'),
    path('subscriptions/', subscription_list_view, name='platform-subscription-list'),
    path('projects/<int:project_id>/subscription/', project_subscription_view, name='platform-project-subscription'),
    path('projects/<int:project_id>/payments/', project_payments_view, name='platform-project-payments'),
    path('projects/<int:project_id>/payments/<int:payment_id>/generate-link/', payment_generate_link_view, name='platform-payment-generate-link'),
    path('projects/<int:project_id>/payments/<int:payment_id>/widget-data/', payment_widget_data_view, name='platform-payment-widget-data'),
    path('projects/<int:project_id>/payments/<int:payment_id>/verify/', payment_verify_transaction_view, name='platform-payment-verify'),
    path('webhooks/wompi/', wompi_webhook_view, name='platform-wompi-webhook'),
]
