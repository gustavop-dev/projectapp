"""Explicit model-field review contract for every MCP connector.

``read_write`` means the connector can both return and mutate the field (often
through a service-driven action). ``read_only`` means callers can observe it
but the server owns changes. Every omitted field must sit in ``excluded`` with
an explanation; the contract test therefore turns a new model field into a
required MCP review instead of silent drift.
"""
from dataclasses import dataclass


def _names(value):
    return frozenset(value.split())


def _excluded(reason, value):
    return {field: reason for field in value.split()}


@dataclass(frozen=True)
class McpModelContract:
    model_label: str
    read_only: frozenset
    read_write: frozenset
    excluded: dict

    @property
    def classified_fields(self):
        return self.read_only | self.read_write | frozenset(self.excluded)


def _contract(model_label, *, read_only='', read_write='', excluded=None):
    return McpModelContract(
        model_label=model_label,
        read_only=_names(read_only),
        read_write=_names(read_write),
        excluded=excluded or {},
    )


_AUDIT_INTERNAL = 'Identificador de auditoría o integración administrado por el servidor.'
_PANEL_ONLY = 'Configuración avanzada reservada al panel; no forma parte del contrato MCP.'
_COMMERCIAL_DOCUMENT = 'Campo exclusivo de cuentas de cobro; el MCP sólo opera documentos markdown.'
_PLATFORM_PROFILE = 'Dato del perfil de plataforma fuera del alcance del gestor comercial de clientes.'
_AUTOMATION_STATE = 'Estado interno de automatización; se observa por resultados, no se manipula por MCP.'


MCP_MODEL_CONTRACTS = {
    'blog': (
        _contract(
            'content.BlogPost',
            read_only='id linkedin_post_id linkedin_published_at created_at updated_at',
            read_write=(
                'title_es title_en slug cover_image cover_image_url '
                'cover_image_credit cover_image_credit_url excerpt_es excerpt_en '
                'content_es content_en content_json_es content_json_en sources '
                'category read_time_minutes is_featured author meta_title_es '
                'meta_title_en meta_description_es meta_description_en '
                'meta_keywords_es meta_keywords_en linkedin_summary_es '
                'linkedin_summary_en is_published published_at'
            ),
        ),
    ),
    'documents': (
        _contract(
            'accounts.Project',
            read_only='id name client current_state',
            excluded=(
                _excluded(
                    'Configuración operativa del proyecto reservada al panel; '
                    'el MCP de Documentos sólo referencia proyectos existentes.',
                    'description status state_review_required progress start_date '
                    'estimated_end_date payment_milestones hosting_tiers '
                    'hosting_start_date production_url staging_url admin_url '
                    'repository_url admin_username',
                )
                | _excluded(
                    'Credencial cifrada del sitio del proyecto: nunca debe salir por MCP.',
                    'admin_password_encrypted',
                )
                | _excluded(_AUDIT_INTERNAL, 'created_at updated_at')
            ),
        ),
        _contract(
            'content.Document',
            read_only='id slug status created_at updated_at tags',
            read_write=(
                'folder project client_user title is_client_visible '
                'content_markdown client_name client_email_subject '
                'client_email_body client_whatsapp_message client_custom_notes '
                'language include_portada include_subportada include_contraportada'
            ),
            excluded=(
                _excluded(_AUDIT_INTERNAL, 'uuid created_by updated_by content_json')
                | _excluded(
                    _COMMERCIAL_DOCUMENT,
                    'document_type issuer hosting_record income_record '
                    'source_proposal source_version generated_file '
                    'public_number issue_date due_date city currency subtotal '
                    'discount_total tax_total total notes terms_and_conditions '
                    'template_version metadata commercial_status requires_signature '
                    'signed_at signed_by signature_name signature_ip signature_user_agent',
                )
                | _excluded(_PANEL_ONLY, 'cover_type template_style')
                | _excluded(
                    'Los documentos archivados quedan fuera de circulación para el MCP.',
                    'is_archived archived_at archived_via_folder',
                )
            ),
        ),
        _contract(
            'content.DocumentState',
            read_only=(
                'id name description color group system_key catalog '
                'operational_effect'
            ),
            excluded=_excluded(
                'El catálogo de estados se administra en el panel; MCP aplica estados activos.',
                'normalized_name slug order is_active merged_into created_by '
                'updated_by created_at updated_at incompatibilities '
                'show_in_document_manager',
            ),
        ),
        _contract(
            'content.DocumentFolder',
            read_only='id slug managed_project managed_client created_at updated_at',
            read_write='name parent project client_user order',
            excluded=(
                _excluded(_AUTOMATION_STATE, 'system_key')
                | _excluded(
                    'El archivado de carpetas es una cascada reservada al panel.',
                    'is_archived archived_at archived_via_folder',
                )
            ),
        ),
        _contract(
            'content.DocumentStateEpisode',
            read_only='id opened_by closed_by created_at updated_at',
            read_write='document state opened_at closed_at outcome close_note origin',
            excluded=_excluded(
                'El ciclo de proyectos se administra en el panel; el conector '
                'de documentos sólo opera episodios vinculados a documentos.',
                'project',
            ),
        ),
        _contract(
            'content.DocumentNote',
            read_only='id order created_at updated_at',
            read_write=(
                'document episode title content status resolution_note resolved_at '
                'deleted_at'
            ),
            excluded=_excluded(
                _AUDIT_INTERNAL,
                'created_by resolved_by deleted_by created_at_known',
            ),
        ),
        _contract(
            'content.DocumentNoteEvent',
            excluded=_excluded(
                'Bitácora append-only administrada por el servidor; el MCP '
                'observa el resultado de cada acción, no edita eventos.',
                'id document note event_type actor recorded_at details',
            ),
        ),
    ),
    'clients': (
        _contract(
            'accounts.UserProfile',
            read_only=(
                'id user is_onboarded cedula nit billing_code archived_at '
                'created_at updated_at'
            ),
            read_write='company_name phone',
            excluded=(
                _excluded('El conector siempre opera perfiles con rol cliente.', 'role')
                | _excluded(
                    _PLATFORM_PROFILE,
                    'email_verified email_verified_at date_of_birth gender '
                    'education_level avatar avatar_url theme_color cover_image '
                    'custom_cover_image profile_completed document_navigation_mode',
                )
                | _excluded(_AUDIT_INTERNAL, 'created_by archived_by')
            ),
        ),
    ),
    'tasks': (
        _contract(
            'content.Task',
            read_only='id created_at updated_at',
            read_write=(
                'title description status priority board_type assignee due_date '
                'position is_archived archive_reason'
            ),
            excluded=_excluded(
                _AUTOMATION_STATE,
                'notified_40 notified_70 notified_100 last_overdue_notified_at',
            ),
        ),
        _contract(
            'content.TaskComment',
            read_only='id author created_at',
            read_write='task text',
        ),
        _contract(
            'content.TaskAlert',
            read_only='id sent created_at',
            read_write='task notify_at note',
        ),
    ),
    'accounting': (
        _contract(
            'content.IncomeRecord',
            read_only=(
                'id created_at updated_at pocket_movement reminder_target_date '
                'reminder_last_sent_at reminder_count'
            ),
            read_write=(
                'notes ledger total_amount gustavo_amount carlos_amount concept '
                'kind client project origin period_date period_start period_end '
                'period_cadence destination expected_income reminders_muted '
                'reminders_muted_until'
            ),
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.ExpenseRecord',
            read_only=(
                'id created_at updated_at deduction_type source_income pocket_movement'
            ),
            read_write=(
                'notes ledger total_amount gustavo_amount carlos_amount concept '
                'period_date category'
            ),
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.HostingRecord',
            read_only=(
                'id created_at updated_at expiry_notice_target '
                'expiry_notice_last_sent_at expiry_notice_count billing_requested_at'
            ),
            read_write=(
                'notes client project client_name client_email client_contact_name '
                'client_identification domain_url monthly_value payment_modality '
                'benefit valid_from valid_to cycles_count payment_per_cycle '
                'total_paid is_active'
            ),
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.PocketMovement',
            read_only='id created_at updated_at',
            read_write='notes concept movement_date direction amount',
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.RecurringPayment',
            read_only=(
                'id created_at updated_at cop_equivalent reminder_target_date '
                'reminder_last_sent_at reminders_muted reminders_muted_until '
                'is_archived archived_at'
            ),
            read_write=(
                'notes name price currency payment_method frequency custom_months '
                'billing_day cycle_anchor_date cost_type is_active category order'
            ),
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.AdsSpendRecord',
            read_only='id created_at updated_at',
            read_write='notes spend_date platform origin_card amount',
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.CardBalanceSnapshot',
            read_only='id created_at updated_at',
            read_write='notes snapshot_date card_name available_amount debt_amount',
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.NotificationRecipient',
            read_only='id created_at updated_at',
            read_write='notes email is_active',
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.AccountingSettings',
            read_only=(
                'id card_reminder_cycle_start card_reminder_last_sent_at '
                'statement_reminder_last_sent_at created_at updated_at'
            ),
            read_write=(
                'notifications_enabled card_reminder_enabled '
                'statement_reminder_enabled hosting_expiry_reminder_enabled '
                'payment_calendar_enabled overdue_reminder_frequency '
                'usd_exchange_rate income_default_view_mode '
                'collection_accounts_view_mode collection_accounts_group_by'
            ),
        ),
        _contract(
            'content.CreditCard',
            read_only='id created_at updated_at',
            read_write='notes name credit_limit is_active statements_since',
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.CreditCardStatement',
            read_only='id created_at updated_at',
            read_write=(
                'notes card_name period_date status purchases_total previous_balance '
                'payments_total interest_and_fees closing_balance minimum_payment '
                'due_date pdf_file'
            ),
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.CreditCardTransaction',
            read_only=(
                'id statement transaction_date raw_description original_amount '
                'original_currency installment_number installments_total created_at '
                'updated_at'
            ),
            read_write=(
                'notes merchant_name category amount is_identified is_reversal'
            ),
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
        _contract(
            'content.MerchantAlias',
            read_only='id created_at updated_at',
            read_write='notes match_text merchant_name default_category is_gateway',
            excluded=_excluded(_AUDIT_INTERNAL, 'source_ref created_by'),
        ),
    ),
    'diagnostics': (
        _contract(
            'content.WebAppDiagnostic',
            read_only=(
                'id uuid view_count last_viewed_at initial_sent_at final_sent_at '
                'responded_at created_at updated_at confidentiality_params'
            ),
            read_write=(
                'slug title client client_name client_email client_phone '
                'client_company language status investment_amount currency '
                'payment_terms duration_label size_category radiography expires_at'
            ),
            excluded=_excluded(_AUDIT_INTERNAL, 'created_by'),
        ),
        _contract(
            'content.DiagnosticSection',
            read_only='id diagnostic section_type',
            read_write='title order is_enabled content_json visibility',
        ),
    ),
    'proposals': (
        _contract(
            'content.BusinessProposal',
            read_only=(
                'id uuid slug reminder_sent_at urgency_email_sent_at '
                'last_activity_at view_count first_viewed_at sent_at responded_at '
                'engagement_declining cached_heat_score client deliverable '
                'platform_onboarding_completed_at platform_onboarding_status '
                'created_at updated_at'
            ),
            read_write=(
                'title client_name client_email language total_investment currency '
                'nationality hosting_percent hosting_discount_nine_month '
                'hosting_discount_semiannual hosting_discount_quarterly status '
                'expires_at reminder_days urgency_reminder_days discount_percent '
                'is_active show_contract_terms project_type market_type '
                'project_type_custom market_type_custom client_phone email_intro '
                'email_features email_method_phases email_signed_by selected_modules '
                'contract_params'
            ),
            excluded=(
                _excluded(
                    _AUTOMATION_STATE,
                    'automations_paused revisit_alert_sent_at '
                    'abandonment_email_sent_at investment_interest_email_sent_at '
                    'followup_scheduled_at stakeholder_alert_sent_at '
                    'post_expiration_alert_sent_at calculator_followup_sent_at '
                    'last_automated_email_at',
                )
                | _excluded(
                    'Respuesta privada del cliente; se gestiona en el flujo público.',
                    'rejection_reason rejection_comment',
                )
            ),
        ),
        _contract(
            'content.ProposalSection',
            read_only='id proposal section_type',
            read_write='title order is_enabled content_json is_wide_panel',
        ),
        _contract(
            'content.ProposalShareLink',
            read_only=(
                'id proposal uuid recipient_name recipient_email view_count '
                'first_viewed_at created_at'
            ),
            read_write='shared_by_name shared_by_email',
        ),
    ),
    'linkedin-personal': (
        _contract(
            'content.LinkedInPost',
            read_only=(
                'id status published_at linkedin_post_id error_message created_at updated_at'
            ),
            read_write='commentary scheduled_at',
            excluded=_excluded(
                'El conector personal v1 publica sólo texto; las imágenes quedan en el panel.',
                'image',
            ),
        ),
        _contract(
            'content.LinkedInToken',
            read_only=(
                'id expires_at refresh_token_expires_at member_sub profile_name '
                'profile_picture profile_email obtained_at updated_at'
            ),
            excluded=_excluded(
                'Credencial cifrada: nunca debe salir por MCP.',
                'access_token_encrypted refresh_token_encrypted',
            ),
        ),
    ),
    'communications': (
        _contract(
            'accounts.CommunicationPanelPreference',
            excluded=_excluded(
                'Preferencia personal de interfaz; el MCP opera el registro '
                'conversacional y no la configuración visual de cada cuenta.',
                'id user navigation_mode thread_order page_size default_channel '
                'show_manual_help navigation_width updated_at',
            ),
        ),
        _contract(
            'content.CommunicationThread',
            read_only=(
                'id status last_activity_at closed_at created_at updated_at '
                'managed_project managed_client'
            ),
            read_write='client project title',
            excluded=(
                _excluded(_AUDIT_INTERNAL, 'created_by updated_by')
                | _excluded(
                    'El archivado de hilos es una operación reservada al panel.',
                    'is_archived archived_at',
                )
            ),
        ),
        _contract(
            'content.CommunicationMessage',
            read_only='id status recorded_at updated_at source voided_at void_reason',
            read_write=(
                'thread channel direction subject content occurred_at reply_to documents'
            ),
            excluded=(
                _excluded(_AUDIT_INTERNAL, 'created_by updated_by voided_by')
                | _excluded(
                    'Enlace interno al log de correo; la herramienta registra hechos manuales.',
                    'email_log',
                )
            ),
        ),
        _contract(
            'content.CommunicationAttachment',
            read_only='id created_at',
            read_write='message document',
        ),
        _contract(
            'content.CommunicationMessageDateCorrection',
            read_only=(
                'id message previous_occurred_at corrected_occurred_at reason '
                'corrected_by corrected_at'
            ),
        ),
    ),
}
