from django.urls import path
from content.views.contact import contact_list, new_contact
from content.views.portfolio_works import (
    list_portfolio_works, retrieve_portfolio_work,
    portfolio_sitemap_data,
    list_admin_portfolio_works, create_portfolio_work,
    create_portfolio_work_from_json, get_portfolio_json_template,
    retrieve_admin_portfolio_work, update_portfolio_work,
    delete_portfolio_work, duplicate_portfolio_work,
    upload_portfolio_cover_image,
)
from content.views.proposal import (
    retrieve_public_proposal, download_proposal_pdf,
    list_proposals, retrieve_proposal, create_proposal,
    create_proposal_from_json, get_proposal_json_template,
    export_proposal_json, update_proposal_from_json,
    update_proposal, delete_proposal, duplicate_proposal, send_proposal,
    resend_proposal, toggle_proposal_active, bulk_action,
    update_proposal_section, bulk_reorder_sections,
    respond_to_proposal, comment_on_proposal, check_admin_auth,
    track_proposal_engagement, track_calculator_interaction, track_requirement_click,
    retrieve_proposal_analytics,
    proposal_dashboard, export_proposal_analytics_csv,
    create_share_link, retrieve_shared_proposal, schedule_followup,
    list_clients, log_activity, proposal_alerts,
    create_proposal_alert, dismiss_proposal_alert,
    update_proposal_status, launch_to_platform, proposal_scorecard,
    proposal_defaults, reset_proposal_defaults,
    email_deliverability_dashboard,
    request_magic_link,
    preview_sync_section, apply_sync_section,
    save_contract_and_negotiate, update_contract_params,
    download_contract_pdf, download_draft_contract_pdf,
    send_documents_to_client,
    get_company_settings,
    get_default_contract_template,
    list_proposal_documents, upload_proposal_document,
    delete_proposal_document,
    send_branded_email, get_branded_email_defaults, list_branded_emails,
    send_proposal_email, get_proposal_email_defaults, list_proposal_emails,
)
from content.views.email_templates import (
    email_template_list, email_template_detail,
    email_template_preview, email_template_reset,
)
from content.views.blog import (
    list_blog_posts, retrieve_blog_post, blog_sitemap_data,
    list_admin_blog_posts, create_blog_post, create_blog_post_from_json,
    get_blog_json_template,
    retrieve_admin_blog_post, update_blog_post, delete_blog_post,
    duplicate_blog_post, upload_blog_cover_image, blog_calendar,
)
from content.views.linkedin import (
    linkedin_auth_url, linkedin_callback, linkedin_status,
    publish_to_linkedin,
)
from content.views.standalone_email import (
    send_standalone_email, get_standalone_email_defaults, list_standalone_emails,
)
from content.views.document import (
    list_documents, create_document, create_document_from_markdown,
    upload_document_markdown, retrieve_document, update_document,
    delete_document, duplicate_document, download_document_pdf,
)

urlpatterns = [
    path('contacts/', contact_list, name='contact-list'),
    path('new-contact/', new_contact, name='new-contact'),

    # Proposals — public
    path('proposals/<uuid:proposal_uuid>/', retrieve_public_proposal, name='retrieve-public-proposal'),
    path('proposals/<uuid:proposal_uuid>/pdf/', download_proposal_pdf, name='download-proposal-pdf'),
    path('proposals/<uuid:proposal_uuid>/respond/', respond_to_proposal, name='respond-to-proposal'),
    path('proposals/<uuid:proposal_uuid>/comment/', comment_on_proposal, name='comment-on-proposal'),
    path('proposals/<uuid:proposal_uuid>/track/', track_proposal_engagement, name='track-proposal-engagement'),
    path('proposals/<uuid:proposal_uuid>/track-calculator/', track_calculator_interaction, name='track-calculator-interaction'),
    path('proposals/<uuid:proposal_uuid>/track-requirement-click/', track_requirement_click, name='track-requirement-click'),
    path('proposals/<uuid:proposal_uuid>/share/', create_share_link, name='create-share-link'),
    path('proposals/<uuid:proposal_uuid>/schedule-followup/', schedule_followup, name='schedule-followup'),
    path('proposals/shared/<uuid:share_uuid>/', retrieve_shared_proposal, name='retrieve-shared-proposal'),
    path('proposals/request-link/', request_magic_link, name='request-magic-link'),

    # Proposals — admin auth check
    path('auth/check/', check_admin_auth, name='check-admin-auth'),

    # Proposals — admin CRUD
    path('proposals/', list_proposals, name='list-proposals'),
    path('proposals/create/', create_proposal, name='create-proposal'),
    path('proposals/create-from-json/', create_proposal_from_json, name='create-proposal-from-json'),
    path('proposals/json-template/', get_proposal_json_template, name='proposal-json-template'),
    path('proposals/<int:proposal_id>/detail/', retrieve_proposal, name='retrieve-proposal'),
    path('proposals/<int:proposal_id>/export-json/', export_proposal_json, name='export-proposal-json'),
    path('proposals/<int:proposal_id>/update-from-json/', update_proposal_from_json, name='update-proposal-from-json'),
    path('proposals/<int:proposal_id>/update/', update_proposal, name='update-proposal'),
    path('proposals/<int:proposal_id>/delete/', delete_proposal, name='delete-proposal'),
    path('proposals/<int:proposal_id>/duplicate/', duplicate_proposal, name='duplicate-proposal'),
    path('proposals/<int:proposal_id>/send/', send_proposal, name='send-proposal'),
    path('proposals/<int:proposal_id>/resend/', resend_proposal, name='resend-proposal'),
    path('proposals/<int:proposal_id>/toggle-active/', toggle_proposal_active, name='toggle-proposal-active'),
    path('proposals/<int:proposal_id>/update-status/', update_proposal_status, name='update-proposal-status'),
    path('proposals/<int:proposal_id>/launch-to-platform/', launch_to_platform, name='launch-to-platform'),
    path('proposals/<int:proposal_id>/scorecard/', proposal_scorecard, name='proposal-scorecard'),
    path('proposals/<int:proposal_id>/reorder-sections/', bulk_reorder_sections, name='reorder-sections'),
    path('proposals/<int:proposal_id>/analytics/', retrieve_proposal_analytics, name='proposal-analytics'),
    path('proposals/<int:proposal_id>/analytics/csv/', export_proposal_analytics_csv, name='proposal-analytics-csv'),
    path('proposals/dashboard/', proposal_dashboard, name='proposal-dashboard'),
    path('proposals/clients/', list_clients, name='list-clients'),
    path('proposals/alerts/', proposal_alerts, name='proposal-alerts'),
    path('proposals/alerts/create/', create_proposal_alert, name='create-proposal-alert'),
    path('proposals/alerts/<int:alert_id>/dismiss/', dismiss_proposal_alert, name='dismiss-proposal-alert'),
    path('proposals/<int:proposal_id>/log-activity/', log_activity, name='log-activity'),
    path('proposals/bulk-action/', bulk_action, name='bulk-action'),

    # Proposals — section editing
    path('proposals/sections/<int:section_id>/update/', update_proposal_section, name='update-proposal-section'),
    path('proposals/sections/<int:section_id>/sync-preview/', preview_sync_section, name='section-sync-preview'),
    path('proposals/sections/<int:section_id>/apply-sync/', apply_sync_section, name='section-apply-sync'),

    # Contract & documents — admin
    path('proposals/<int:proposal_id>/contract/save-and-negotiate/', save_contract_and_negotiate, name='save-contract-and-negotiate'),
    path('proposals/<int:proposal_id>/contract/update/', update_contract_params, name='update-contract-params'),
    path('proposals/<int:proposal_id>/contract/pdf/', download_contract_pdf, name='download-contract-pdf'),
    path('proposals/<int:proposal_id>/contract/draft-pdf/', download_draft_contract_pdf, name='download-draft-contract-pdf'),
    path('proposals/<int:proposal_id>/documents/', list_proposal_documents, name='list-proposal-documents'),
    path('proposals/<int:proposal_id>/documents/upload/', upload_proposal_document, name='upload-proposal-document'),
    path('proposals/<int:proposal_id>/documents/send/', send_documents_to_client, name='send-documents-to-client'),
    path('proposals/<int:proposal_id>/documents/<int:doc_id>/delete/', delete_proposal_document, name='delete-proposal-document'),

    # Branded email — admin
    path('proposals/<int:proposal_id>/branded-email/send/', send_branded_email, name='send-branded-email'),
    path('proposals/<int:proposal_id>/branded-email/defaults/', get_branded_email_defaults, name='branded-email-defaults'),
    path('proposals/<int:proposal_id>/branded-email/history/', list_branded_emails, name='list-branded-emails'),

    # Proposal email — admin (logged as activity)
    path('proposals/<int:proposal_id>/proposal-email/send/', send_proposal_email, name='send-proposal-email'),
    path('proposals/<int:proposal_id>/proposal-email/defaults/', get_proposal_email_defaults, name='proposal-email-defaults'),
    path('proposals/<int:proposal_id>/proposal-email/history/', list_proposal_emails, name='list-proposal-emails'),

    path('proposals/company-settings/', get_company_settings, name='get-company-settings'),
    path('proposals/contract-template/default/', get_default_contract_template, name='get-default-contract-template'),

    # Proposals — default config
    path('proposals/defaults/', proposal_defaults, name='proposal-defaults'),
    path('proposals/defaults/reset/', reset_proposal_defaults, name='reset-proposal-defaults'),

    # Email deliverability
    path('email-deliverability/', email_deliverability_dashboard, name='email-deliverability-dashboard'),

    # Email templates
    path('email-templates/', email_template_list, name='email-template-list'),
    path('email-templates/<str:template_key>/', email_template_detail, name='email-template-detail'),
    path('email-templates/<str:template_key>/preview/', email_template_preview, name='email-template-preview'),
    path('email-templates/<str:template_key>/reset/', email_template_reset, name='email-template-reset'),

    # Blog — admin CRUD (must come before slug catch-all)
    path('blog/admin/', list_admin_blog_posts, name='list-admin-blog-posts'),
    path('blog/admin/create/', create_blog_post, name='create-blog-post'),
    path('blog/admin/create-from-json/', create_blog_post_from_json, name='create-blog-post-from-json'),
    path('blog/admin/json-template/', get_blog_json_template, name='blog-json-template'),
    path('blog/admin/<int:post_id>/detail/', retrieve_admin_blog_post, name='retrieve-admin-blog-post'),
    path('blog/admin/<int:post_id>/update/', update_blog_post, name='update-blog-post'),
    path('blog/admin/<int:post_id>/delete/', delete_blog_post, name='delete-blog-post'),
    path('blog/admin/<int:post_id>/duplicate/', duplicate_blog_post, name='duplicate-blog-post'),
    path('blog/admin/<int:post_id>/upload-cover/', upload_blog_cover_image, name='upload-blog-cover-image'),
    path('blog/admin/calendar/', blog_calendar, name='blog-calendar'),
    path('blog/admin/<int:post_id>/publish-linkedin/', publish_to_linkedin, name='publish-to-linkedin'),

    # LinkedIn OAuth
    path('linkedin/auth-url/', linkedin_auth_url, name='linkedin-auth-url'),
    path('linkedin/callback/', linkedin_callback, name='linkedin-callback'),
    path('linkedin/status/', linkedin_status, name='linkedin-status'),

    # Blog — public
    path('blog/', list_blog_posts, name='list-blog-posts'),
    path('blog/sitemap-data/', blog_sitemap_data, name='blog-sitemap-data'),
    path('blog/<slug:slug>/', retrieve_blog_post, name='retrieve-blog-post'),

    # ── Standalone emails (generic branded, not proposal-tied) ────
    path('emails/send/', send_standalone_email, name='send-standalone-email'),
    path('emails/defaults/', get_standalone_email_defaults, name='standalone-email-defaults'),
    path('emails/history/', list_standalone_emails, name='list-standalone-emails'),

    # ── Documents ──────────────────────────────────────────────────
    path('documents/', list_documents, name='list-documents'),
    path('documents/create/', create_document, name='create-document'),
    path('documents/create-from-markdown/', create_document_from_markdown, name='create-document-from-markdown'),
    path('documents/upload-markdown/', upload_document_markdown, name='upload-document-markdown'),
    path('documents/<int:document_id>/detail/', retrieve_document, name='retrieve-document'),
    path('documents/<int:document_id>/update/', update_document, name='update-document'),
    path('documents/<int:document_id>/delete/', delete_document, name='delete-document'),
    path('documents/<int:document_id>/duplicate/', duplicate_document, name='duplicate-document'),
    path('documents/<int:document_id>/pdf/', download_document_pdf, name='download-document-pdf'),

    # Portfolio — admin CRUD (must come before slug catch-all)
    path('portfolio/admin/', list_admin_portfolio_works, name='list-admin-portfolio-works'),
    path('portfolio/admin/create/', create_portfolio_work, name='create-portfolio-work'),
    path('portfolio/admin/create-from-json/', create_portfolio_work_from_json, name='create-portfolio-work-from-json'),
    path('portfolio/admin/json-template/', get_portfolio_json_template, name='portfolio-json-template'),
    path('portfolio/admin/<int:work_id>/detail/', retrieve_admin_portfolio_work, name='retrieve-admin-portfolio-work'),
    path('portfolio/admin/<int:work_id>/update/', update_portfolio_work, name='update-portfolio-work'),
    path('portfolio/admin/<int:work_id>/delete/', delete_portfolio_work, name='delete-portfolio-work'),
    path('portfolio/admin/<int:work_id>/duplicate/', duplicate_portfolio_work, name='duplicate-portfolio-work'),
    path('portfolio/admin/<int:work_id>/upload-cover/', upload_portfolio_cover_image, name='upload-portfolio-cover-image'),

    # Portfolio — public
    path('portfolio/', list_portfolio_works, name='list-portfolio-works-public'),
    path('portfolio/sitemap-data/', portfolio_sitemap_data, name='portfolio-sitemap-data'),
    path('portfolio/<slug:slug>/', retrieve_portfolio_work, name='retrieve-portfolio-work'),
]
