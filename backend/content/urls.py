from django.urls import path
from content.views.accounting import (
    accounting_dashboard,
    list_income_records, create_income_record, retrieve_income_record,
    update_income_record, delete_income_record,
    list_expense_records, create_expense_record, retrieve_expense_record,
    update_expense_record, delete_expense_record,
    list_hosting_records, create_hosting_record, retrieve_hosting_record,
    update_hosting_record, delete_hosting_record,
    list_pocket_movements, create_pocket_movement, retrieve_pocket_movement,
    update_pocket_movement, delete_pocket_movement,
    list_recurring_payments, create_recurring_payment,
    retrieve_recurring_payment, update_recurring_payment,
    delete_recurring_payment,
    list_ads_spend_records, create_ads_spend_record,
    retrieve_ads_spend_record, update_ads_spend_record,
    delete_ads_spend_record,
    list_card_snapshots, create_card_snapshot, retrieve_card_snapshot,
    update_card_snapshot, delete_card_snapshot,
    list_accounting_change_logs,
    get_accounting_settings, update_accounting_settings,
)
from content.views.accounting_export import (
    export_accounting_records, export_accounting_workbook,
)
from content.views.collection_accounts_panel import (
    cancel_collection_account_view,
    collection_account_pdf,
    list_collection_accounts,
    mark_collection_account_paid_view,
    resend_collection_account,
    retrieve_collection_account,
    send_hosting_collection_account,
)
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
from content.views.hour_packages import (
    list_admin_hour_packages, create_hour_package,
    retrieve_admin_hour_package, update_hour_package,
    delete_hour_package,
)
from content.views.proposal import (
    retrieve_public_proposal, retrieve_public_proposal_by_slug,
    download_proposal_pdf,
    list_proposals, retrieve_proposal, create_proposal,
    create_proposal_from_json, get_proposal_json_template,
    export_proposal_json, update_proposal_from_json,
    update_proposal, delete_proposal, duplicate_proposal, send_proposal,
    send_multi_proposal, preview_proposal_email,
    resend_proposal, toggle_proposal_active, bulk_action,
    update_proposal_section, bulk_reorder_sections,
    create_proposal_section, delete_proposal_section,
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
    send_discount_offer,
    get_company_settings,
    get_default_contract_template,
    list_proposal_documents, upload_proposal_document,
    delete_proposal_document,
    send_branded_email, get_branded_email_defaults, list_branded_emails,
    send_proposal_email, get_proposal_email_defaults, list_proposal_emails,
    generate_email_markdown_attachment,
    update_project_stage, complete_project_stage,
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
from content.views.mcp_blog import (
    generate_mcp_connector_token,
    list_mcp_connectors,
    mcp_endpoint,
    update_mcp_connector,
)
from content.views.linkedin import (
    linkedin_auth_url, linkedin_callback, linkedin_status,
    publish_to_linkedin,
    list_linkedin_posts, create_linkedin_post,
    update_linkedin_post, delete_linkedin_post,
    publish_linkedin_post,
)
from content.views.standalone_email import (
    send_standalone_email, get_standalone_email_defaults, list_standalone_emails,
)
from content.views.document import (
    list_documents, create_document, create_document_from_markdown,
    upload_document_markdown, retrieve_document, update_document,
    delete_document, duplicate_document, download_document_pdf,
)
from content.views.document_folder import (
    list_document_folders, create_document_folder,
    update_document_folder, delete_document_folder,
    reorder_document_folders,
)
from content.views.document_tag import (
    list_document_tags, create_document_tag,
    update_document_tag, delete_document_tag,
)
from content.views.proposal_clients import (
    list_proposal_clients, search_proposal_clients, retrieve_proposal_client,
    create_proposal_client, update_proposal_client, delete_proposal_client,
)
from content.views.task import (
    list_tasks, create_task, update_task, reorder_task, delete_task,
    duplicate_task,
    list_task_assignees,
    archive_task, unarchive_task, list_archived_tasks,
    list_task_comments, create_task_comment, delete_task_comment,
    list_task_alerts, create_task_alert, delete_task_alert,
)
from content.views.diagnostic_template import (
    list_diagnostic_templates, get_diagnostic_template,
)
from content.views.diagnostic import (
    list_diagnostics, create_diagnostic, retrieve_diagnostic,
    update_diagnostic, delete_diagnostic, bulk_diagnostic_action,
    diagnostic_scorecard,
    list_diagnostic_sections, update_diagnostic_section,
    bulk_update_diagnostic_sections, reset_diagnostic_section,
    list_diagnostic_activity, create_diagnostic_activity,
    diagnostic_analytics, export_diagnostic_analytics_csv,
    send_initial, mark_in_analysis, send_final,
    list_diagnostic_attachments, upload_diagnostic_attachment,
    delete_diagnostic_attachment, send_diagnostic_attachments,
    update_confidentiality_params, generate_confidentiality_pdf_view,
    download_confidentiality_pdf, download_draft_confidentiality_pdf,
    send_diagnostic_email, get_diagnostic_email_defaults,
    list_diagnostic_emails, generate_diagnostic_email_markdown_attachment,
    retrieve_public_diagnostic, retrieve_public_diagnostic_by_slug,
    track_public_diagnostic,
    track_diagnostic_section_view, respond_public_diagnostic,
    download_public_diagnostic_pdf,
    diagnostic_defaults, reset_diagnostic_defaults,
)

urlpatterns = [
    path('contacts/', contact_list, name='contact-list'),
    path('new-contact/', new_contact, name='new-contact'),

    # Proposals — public
    path('proposals/<uuid:proposal_uuid>/', retrieve_public_proposal, name='retrieve-public-proposal'),
    path('proposals/by-slug/<slug:proposal_slug>/', retrieve_public_proposal_by_slug, name='retrieve-public-proposal-by-slug'),
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
    path('proposals/<int:proposal_id>/send-multi/', send_multi_proposal, name='send-multi-proposal'),
    path('proposals/<int:proposal_id>/email-preview/', preview_proposal_email, name='preview-proposal-email'),
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

    # Proposals — client profiles (real UserProfile entities, replaces grouped list_clients)
    path('proposals/client-profiles/', list_proposal_clients, name='list-proposal-clients'),
    path('proposals/client-profiles/search/', search_proposal_clients, name='search-proposal-clients'),
    path('proposals/client-profiles/create/', create_proposal_client, name='create-proposal-client'),
    path('proposals/client-profiles/<int:client_id>/', retrieve_proposal_client, name='retrieve-proposal-client'),
    path('proposals/client-profiles/<int:client_id>/update/', update_proposal_client, name='update-proposal-client'),
    path('proposals/client-profiles/<int:client_id>/delete/', delete_proposal_client, name='delete-proposal-client'),
    path('proposals/alerts/', proposal_alerts, name='proposal-alerts'),
    path('proposals/alerts/create/', create_proposal_alert, name='create-proposal-alert'),
    path('proposals/alerts/<int:alert_id>/dismiss/', dismiss_proposal_alert, name='dismiss-proposal-alert'),
    path('proposals/<int:proposal_id>/log-activity/', log_activity, name='log-activity'),
    path('proposals/bulk-action/', bulk_action, name='bulk-action'),

    # Proposals — section editing
    path('proposals/<int:proposal_id>/sections/create/', create_proposal_section, name='create-proposal-section'),
    path('proposals/sections/<int:section_id>/update/', update_proposal_section, name='update-proposal-section'),
    path('proposals/sections/<int:section_id>/delete/', delete_proposal_section, name='delete-proposal-section'),
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
    path('proposals/<int:proposal_id>/discount-offer/send/', send_discount_offer, name='send-discount-offer'),
    path('proposals/<int:proposal_id>/documents/<int:doc_id>/delete/', delete_proposal_document, name='delete-proposal-document'),

    # Branded email — admin
    path('proposals/<int:proposal_id>/branded-email/send/', send_branded_email, name='send-branded-email'),
    path('proposals/<int:proposal_id>/branded-email/defaults/', get_branded_email_defaults, name='branded-email-defaults'),
    path('proposals/<int:proposal_id>/branded-email/history/', list_branded_emails, name='list-branded-emails'),

    # Proposal email — admin (logged as activity)
    path('proposals/<int:proposal_id>/proposal-email/send/', send_proposal_email, name='send-proposal-email'),
    path('proposals/<int:proposal_id>/proposal-email/defaults/', get_proposal_email_defaults, name='proposal-email-defaults'),
    path('proposals/<int:proposal_id>/proposal-email/history/', list_proposal_emails, name='list-proposal-emails'),
    path('proposals/<int:proposal_id>/proposal-email/markdown-attachment/', generate_email_markdown_attachment, name='generate-email-markdown-attachment'),

    # Project schedule (Cronograma admin tab)
    path('proposals/<int:proposal_id>/stages/<str:stage_key>/', update_project_stage, name='update-project-stage'),
    path('proposals/<int:proposal_id>/stages/<str:stage_key>/complete/', complete_project_stage, name='complete-project-stage'),

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

    # MCP (Model Context Protocol) — token-authenticated remote connectors.
    # Both slash variants: a POST to the unslashed URL must not fall through
    # to the SPA catch-all (403 CSRF) — connector URLs get hand-copied and
    # the trailing slash is the first thing that gets lost.
    path('mcp/<slug:slug>/<str:token>/', mcp_endpoint, name='mcp-endpoint'),
    path('mcp/<slug:slug>/<str:token>', mcp_endpoint, name='mcp-endpoint-noslash'),
    path('mcp-connectors/', list_mcp_connectors, name='list-mcp-connectors'),
    path('mcp-connectors/<slug:slug>/', update_mcp_connector, name='update-mcp-connector'),
    path('mcp-connectors/<slug:slug>/generate-token/', generate_mcp_connector_token, name='generate-mcp-connector-token'),
    path('blog/admin/<int:post_id>/publish-linkedin/', publish_to_linkedin, name='publish-to-linkedin'),

    # LinkedIn OAuth
    path('linkedin/auth-url/', linkedin_auth_url, name='linkedin-auth-url'),
    path('linkedin/callback/', linkedin_callback, name='linkedin-callback'),
    path('linkedin/status/', linkedin_status, name='linkedin-status'),

    # Freeform LinkedIn posts (panel module)
    path('linkedin/posts/', list_linkedin_posts, name='list-linkedin-posts'),
    path('linkedin/posts/create/', create_linkedin_post, name='create-linkedin-post'),
    path('linkedin/posts/<int:post_id>/update/', update_linkedin_post, name='update-linkedin-post'),
    path('linkedin/posts/<int:post_id>/delete/', delete_linkedin_post, name='delete-linkedin-post'),
    path('linkedin/posts/<int:post_id>/publish/', publish_linkedin_post, name='publish-linkedin-post'),

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

    # Document folders (flat, inline-managed)
    path('document-folders/', list_document_folders, name='list-document-folders'),
    path('document-folders/create/', create_document_folder, name='create-document-folder'),
    path('document-folders/reorder/', reorder_document_folders, name='reorder-document-folders'),
    path('document-folders/<int:folder_id>/update/', update_document_folder, name='update-document-folder'),
    path('document-folders/<int:folder_id>/delete/', delete_document_folder, name='delete-document-folder'),

    # Kanban tasks (admin panel)
    path('tasks/', list_tasks, name='list-tasks'),
    path('tasks/create/', create_task, name='create-task'),
    path('tasks/assignees/', list_task_assignees, name='list-task-assignees'),
    path('tasks/archived/', list_archived_tasks, name='list-archived-tasks'),
    path('tasks/<int:task_id>/update/', update_task, name='update-task'),
    path('tasks/<int:task_id>/reorder/', reorder_task, name='reorder-task'),
    path('tasks/<int:task_id>/delete/', delete_task, name='delete-task'),
    path('tasks/<int:task_id>/duplicate/', duplicate_task, name='duplicate-task'),
    path('tasks/<int:task_id>/archive/', archive_task, name='archive-task'),
    path('tasks/<int:task_id>/unarchive/', unarchive_task, name='unarchive-task'),
    path('tasks/<int:task_id>/comments/', list_task_comments, name='list-task-comments'),
    path('tasks/<int:task_id>/comments/create/', create_task_comment, name='create-task-comment'),
    path('tasks/<int:task_id>/comments/<int:comment_id>/delete/', delete_task_comment, name='delete-task-comment'),
    path('tasks/<int:task_id>/alerts/', list_task_alerts, name='list-task-alerts'),
    path('tasks/<int:task_id>/alerts/create/', create_task_alert, name='create-task-alert'),
    path('tasks/<int:task_id>/alerts/<int:alert_id>/delete/', delete_task_alert, name='delete-task-alert'),

    # Document tags (M2M, inline-managed)
    path('document-tags/', list_document_tags, name='list-document-tags'),
    path('document-tags/create/', create_document_tag, name='create-document-tag'),
    path('document-tags/<int:tag_id>/update/', update_document_tag, name='update-document-tag'),
    path('document-tags/<int:tag_id>/delete/', delete_document_tag, name='delete-document-tag'),

    # ── Web App Diagnostics ───────────────────────────────────────
    # Public (UUID-based)
    path('diagnostics/public/<uuid:diagnostic_uuid>/', retrieve_public_diagnostic, name='retrieve-public-diagnostic'),
    path('diagnostics/public/by-slug/<slug:diagnostic_slug>/', retrieve_public_diagnostic_by_slug, name='retrieve-public-diagnostic-by-slug'),
    path('diagnostics/public/<uuid:diagnostic_uuid>/track/', track_public_diagnostic, name='track-public-diagnostic'),
    path('diagnostics/public/<uuid:diagnostic_uuid>/track-section/', track_diagnostic_section_view, name='track-diagnostic-section-view'),
    path('diagnostics/public/<uuid:diagnostic_uuid>/respond/', respond_public_diagnostic, name='respond-public-diagnostic'),
    path('diagnostics/public/<uuid:diagnostic_uuid>/pdf/', download_public_diagnostic_pdf, name='download-public-diagnostic-pdf'),

    # Admin CRUD
    path('diagnostics/', list_diagnostics, name='list-diagnostics'),
    path('diagnostics/create/', create_diagnostic, name='create-diagnostic'),
    path('diagnostics/bulk-action/', bulk_diagnostic_action, name='bulk-diagnostic-action'),
    path('diagnostics/<int:diagnostic_id>/detail/', retrieve_diagnostic, name='retrieve-diagnostic'),
    path('diagnostics/<int:diagnostic_id>/update/', update_diagnostic, name='update-diagnostic'),
    path('diagnostics/<int:diagnostic_id>/delete/', delete_diagnostic, name='delete-diagnostic'),
    path('diagnostics/<int:diagnostic_id>/scorecard/', diagnostic_scorecard, name='diagnostic-scorecard'),
    path('diagnostics/<int:diagnostic_id>/send-initial/', send_initial, name='send-initial-diagnostic'),
    path('diagnostics/<int:diagnostic_id>/mark-in-analysis/', mark_in_analysis, name='mark-in-analysis-diagnostic'),
    path('diagnostics/<int:diagnostic_id>/send-final/', send_final, name='send-final-diagnostic'),

    # Sections (JSON-driven content)
    path('diagnostics/<int:diagnostic_id>/sections/', list_diagnostic_sections, name='list-diagnostic-sections'),
    path('diagnostics/<int:diagnostic_id>/sections/bulk-update/', bulk_update_diagnostic_sections, name='bulk-update-diagnostic-sections'),
    path('diagnostics/<int:diagnostic_id>/sections/<int:section_id>/update/', update_diagnostic_section, name='update-diagnostic-section'),
    path('diagnostics/<int:diagnostic_id>/sections/<int:section_id>/reset/', reset_diagnostic_section, name='reset-diagnostic-section'),

    # Activity (change log)
    path('diagnostics/<int:diagnostic_id>/activity/', list_diagnostic_activity, name='list-diagnostic-activity'),
    path('diagnostics/<int:diagnostic_id>/activity/create/', create_diagnostic_activity, name='create-diagnostic-activity'),

    # Analytics
    path('diagnostics/<int:diagnostic_id>/analytics/', diagnostic_analytics, name='diagnostic-analytics'),
    path('diagnostics/<int:diagnostic_id>/analytics/csv/', export_diagnostic_analytics_csv, name='diagnostic-analytics-csv'),

    # Attachments (files uploaded to a diagnostic)
    path('diagnostics/<int:diagnostic_id>/attachments/', list_diagnostic_attachments, name='list-diagnostic-attachments'),
    path('diagnostics/<int:diagnostic_id>/attachments/upload/', upload_diagnostic_attachment, name='upload-diagnostic-attachment'),
    path('diagnostics/<int:diagnostic_id>/attachments/send/', send_diagnostic_attachments, name='send-diagnostic-attachments'),
    path('diagnostics/<int:diagnostic_id>/attachments/<int:attachment_id>/delete/', delete_diagnostic_attachment, name='delete-diagnostic-attachment'),

    # Acuerdo de Confidencialidad (NDA)
    path('diagnostics/<int:diagnostic_id>/confidentiality/params/', update_confidentiality_params, name='diagnostic-update-confidentiality-params'),
    path('diagnostics/<int:diagnostic_id>/confidentiality/generate/', generate_confidentiality_pdf_view, name='diagnostic-generate-confidentiality'),
    path('diagnostics/<int:diagnostic_id>/confidentiality/pdf/', download_confidentiality_pdf, name='diagnostic-download-confidentiality'),
    path('diagnostics/<int:diagnostic_id>/confidentiality/draft-pdf/', download_draft_confidentiality_pdf, name='diagnostic-download-draft-confidentiality'),

    # Email composer (history + send)
    path('diagnostics/<int:diagnostic_id>/email/send/', send_diagnostic_email, name='send-diagnostic-email'),
    path('diagnostics/<int:diagnostic_id>/email/defaults/', get_diagnostic_email_defaults, name='diagnostic-email-defaults'),
    path('diagnostics/<int:diagnostic_id>/email/history/', list_diagnostic_emails, name='list-diagnostic-emails'),
    path('diagnostics/<int:diagnostic_id>/email/markdown-attachment/', generate_diagnostic_email_markdown_attachment, name='generate-diagnostic-email-markdown-attachment'),

    # Diagnostics — default config (admin)
    path('diagnostics/defaults/', diagnostic_defaults, name='diagnostic-defaults'),
    path('diagnostics/defaults/reset/', reset_diagnostic_defaults, name='reset-diagnostic-defaults'),

    # Diagnostic markdown templates (static .md files exposed for sellers)
    path('diagnostic-templates/', list_diagnostic_templates, name='list-diagnostic-templates'),
    path('diagnostic-templates/<slug:slug>/', get_diagnostic_template, name='get-diagnostic-template'),

    # Portfolio — admin CRUD (must come before slug catch-all)
    path('portfolio/admin/', list_admin_portfolio_works, name='list-admin-portfolio-works'),
    path('portfolio/admin/create/', create_portfolio_work, name='create-portfolio-work'),
    path('portfolio/admin/create-from-json/', create_portfolio_work_from_json, name='create-portfolio-work-from-json'),
    path('portfolio/admin/json-template/', get_portfolio_json_template, name='portfolio-json-template'),
    path('portfolio/admin/<int:work_id>/detail/', retrieve_admin_portfolio_work, name='retrieve-admin-portfolio-work'),
    path('portfolio/admin/<int:work_id>/update/', update_portfolio_work, name='update-portfolio-work'),
    path('portfolio/admin/<int:work_id>/delete/', delete_portfolio_work, name='delete-portfolio-work'),
    path('portfolio/admin/<int:work_id>/duplicate/', duplicate_portfolio_work, name='duplicate-portfolio-work'),

    # Hour packages — admin catalog CRUD (per-nationality pricing)
    path('hour-packages/admin/', list_admin_hour_packages, name='list-admin-hour-packages'),
    path('hour-packages/admin/create/', create_hour_package, name='create-hour-package'),
    path('hour-packages/admin/<int:package_id>/detail/', retrieve_admin_hour_package, name='retrieve-admin-hour-package'),
    path('hour-packages/admin/<int:package_id>/update/', update_hour_package, name='update-hour-package'),
    path('hour-packages/admin/<int:package_id>/delete/', delete_hour_package, name='delete-hour-package'),
    path('portfolio/admin/<int:work_id>/upload-cover/', upload_portfolio_cover_image, name='upload-portfolio-cover-image'),

    # Portfolio — public
    path('portfolio/', list_portfolio_works, name='list-portfolio-works-public'),
    path('portfolio/sitemap-data/', portfolio_sitemap_data, name='portfolio-sitemap-data'),
    path('portfolio/<slug:slug>/', retrieve_portfolio_work, name='retrieve-portfolio-work'),

    # ── Accounting module (panel, superuser-only) ──────────────────
    path('accounting/dashboard/', accounting_dashboard, name='accounting-dashboard'),

    path('accounting/incomes/', list_income_records, name='list-income-records'),
    path('accounting/incomes/create/', create_income_record, name='create-income-record'),
    path('accounting/incomes/<int:record_id>/', retrieve_income_record, name='retrieve-income-record'),
    path('accounting/incomes/<int:record_id>/update/', update_income_record, name='update-income-record'),
    path('accounting/incomes/<int:record_id>/delete/', delete_income_record, name='delete-income-record'),

    path('accounting/expenses/', list_expense_records, name='list-expense-records'),
    path('accounting/expenses/create/', create_expense_record, name='create-expense-record'),
    path('accounting/expenses/<int:record_id>/', retrieve_expense_record, name='retrieve-expense-record'),
    path('accounting/expenses/<int:record_id>/update/', update_expense_record, name='update-expense-record'),
    path('accounting/expenses/<int:record_id>/delete/', delete_expense_record, name='delete-expense-record'),

    path('accounting/hostings/', list_hosting_records, name='list-hosting-records'),
    path('accounting/hostings/create/', create_hosting_record, name='create-hosting-record'),
    path('accounting/hostings/<int:record_id>/', retrieve_hosting_record, name='retrieve-hosting-record'),
    path('accounting/hostings/<int:record_id>/update/', update_hosting_record, name='update-hosting-record'),
    path('accounting/hostings/<int:record_id>/delete/', delete_hosting_record, name='delete-hosting-record'),
    path(
        'accounting/hostings/<int:record_id>/send-collection-account/',
        send_hosting_collection_account,
        name='send-hosting-collection-account',
    ),

    path('accounting/collection-accounts/', list_collection_accounts, name='list-collection-accounts'),
    path('accounting/collection-accounts/<int:doc_id>/', retrieve_collection_account, name='retrieve-collection-account'),
    path('accounting/collection-accounts/<int:doc_id>/pdf/', collection_account_pdf, name='collection-account-pdf'),
    path('accounting/collection-accounts/<int:doc_id>/resend/', resend_collection_account, name='resend-collection-account'),
    path('accounting/collection-accounts/<int:doc_id>/mark-paid/', mark_collection_account_paid_view, name='mark-collection-account-paid'),
    path('accounting/collection-accounts/<int:doc_id>/cancel/', cancel_collection_account_view, name='cancel-collection-account'),

    path('accounting/pocket/', list_pocket_movements, name='list-pocket-movements'),
    path('accounting/pocket/create/', create_pocket_movement, name='create-pocket-movement'),
    path('accounting/pocket/<int:record_id>/', retrieve_pocket_movement, name='retrieve-pocket-movement'),
    path('accounting/pocket/<int:record_id>/update/', update_pocket_movement, name='update-pocket-movement'),
    path('accounting/pocket/<int:record_id>/delete/', delete_pocket_movement, name='delete-pocket-movement'),

    path('accounting/recurring/', list_recurring_payments, name='list-recurring-payments'),
    path('accounting/recurring/create/', create_recurring_payment, name='create-recurring-payment'),
    path('accounting/recurring/<int:record_id>/', retrieve_recurring_payment, name='retrieve-recurring-payment'),
    path('accounting/recurring/<int:record_id>/update/', update_recurring_payment, name='update-recurring-payment'),
    path('accounting/recurring/<int:record_id>/delete/', delete_recurring_payment, name='delete-recurring-payment'),

    path('accounting/ads/', list_ads_spend_records, name='list-ads-spend-records'),
    path('accounting/ads/create/', create_ads_spend_record, name='create-ads-spend-record'),
    path('accounting/ads/<int:record_id>/', retrieve_ads_spend_record, name='retrieve-ads-spend-record'),
    path('accounting/ads/<int:record_id>/update/', update_ads_spend_record, name='update-ads-spend-record'),
    path('accounting/ads/<int:record_id>/delete/', delete_ads_spend_record, name='delete-ads-spend-record'),

    path('accounting/card-snapshots/', list_card_snapshots, name='list-card-snapshots'),
    path('accounting/card-snapshots/create/', create_card_snapshot, name='create-card-snapshot'),
    path('accounting/card-snapshots/<int:record_id>/', retrieve_card_snapshot, name='retrieve-card-snapshot'),
    path('accounting/card-snapshots/<int:record_id>/update/', update_card_snapshot, name='update-card-snapshot'),
    path('accounting/card-snapshots/<int:record_id>/delete/', delete_card_snapshot, name='delete-card-snapshot'),

    path('accounting/change-logs/', list_accounting_change_logs, name='list-accounting-change-logs'),

    path('accounting/settings/', get_accounting_settings, name='get-accounting-settings'),
    path('accounting/settings/update/', update_accounting_settings, name='update-accounting-settings'),

    path('accounting/export/', export_accounting_records, name='export-accounting-records'),
    path('accounting/export/workbook/', export_accounting_workbook, name='export-accounting-workbook'),
]
