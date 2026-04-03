from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Contact, PortfolioWork,
    BusinessProposal, ProposalSection, ProposalRequirementGroup, ProposalRequirementItem,
    BlogPost, ProposalViewEvent, ProposalSectionView, ProposalChangeLog,
    ProposalDefaultConfig, EmailTemplateConfig,
    Document,
    DocumentType,
    IssuerProfile,
    CompanySettings,
    ProposalDocument,
    ContractTemplate,
)

class PortfolioWorkAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the PortfolioWork model.
    """
    list_display = ('title_en', 'title_es', 'slug', 'is_published', 'order', 'published_at', 'created_at')
    list_filter = ('is_published',)
    search_fields = ('title_es', 'title_en', 'excerpt_es', 'excerpt_en')
    prepopulated_fields = {'slug': ('title_es',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Español', {
            'fields': ('title_es', 'excerpt_es', 'content_json_es'),
        }),
        ('English', {
            'fields': ('title_en', 'excerpt_en', 'content_json_en'),
        }),
        (None, {
            'fields': ('slug', 'cover_image', 'cover_image_url', 'project_url', 'category_title_es', 'category_title_en', 'order'),
        }),
        ('SEO', {
            'fields': ('meta_title_es', 'meta_title_en', 'meta_description_es', 'meta_description_en', 'meta_keywords_es', 'meta_keywords_en'),
            'classes': ('collapse',),
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

class ContactAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Contact model.
    Display specific fields of the Contact model.
    """
    list_display = ('email', 'subject', 'message')

class BlogPostAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the BlogPost model.
    """
    list_display = ('title_es', 'title_en', 'slug', 'category', 'is_featured', 'is_published', 'published_at', 'created_at')
    list_filter = ('is_published', 'is_featured', 'category')
    search_fields = ('title_es', 'title_en', 'excerpt_es', 'excerpt_en', 'content_es', 'content_en')
    prepopulated_fields = {'slug': ('title_es',)}
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Español', {
            'fields': ('title_es', 'excerpt_es', 'content_es', 'content_json_es'),
        }),
        ('English', {
            'fields': ('title_en', 'excerpt_en', 'content_en', 'content_json_en'),
        }),
        (None, {
            'fields': ('slug', 'cover_image', 'cover_image_url', 'cover_image_credit', 'cover_image_credit_url', 'category', 'read_time_minutes', 'is_featured', 'author'),
        }),
        ('SEO', {
            'fields': ('meta_title_es', 'meta_title_en', 'meta_description_es', 'meta_description_en', 'meta_keywords_es', 'meta_keywords_en'),
            'classes': ('collapse',),
        }),
        ('Sources', {
            'fields': ('sources',),
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


class ProposalSectionInline(admin.TabularInline):
    """
    Inline admin for proposal sections within BusinessProposalAdmin.
    Content JSON is edited in the Nuxt admin frontend, not here.
    """
    model = ProposalSection
    extra = 0
    fields = ('section_type', 'title', 'order', 'is_enabled', 'is_wide_panel')
    ordering = ('order',)


class ProposalRequirementGroupInline(admin.TabularInline):
    """
    Inline admin for requirement groups within BusinessProposalAdmin.
    """
    model = ProposalRequirementGroup
    extra = 0
    fields = ('group_id', 'title', 'description', 'order')
    ordering = ('order',)


class BusinessProposalAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the BusinessProposal model.
    """
    list_display = (
        'title', 'client_name', 'status', 'is_active', 'total_investment',
        'currency', 'expires_at', 'view_count', 'created_at',
    )
    list_filter = ('status', 'currency', 'is_active')
    search_fields = ('title', 'client_name', 'client_email')
    readonly_fields = (
        'uuid', 'view_count', 'first_viewed_at', 'sent_at',
        'responded_at', 'revisit_alert_sent_at',
        'reminder_sent_at', 'created_at', 'updated_at',
    )
    inlines = [ProposalSectionInline, ProposalRequirementGroupInline]
    fieldsets = (
        ('Identity', {
            'fields': ('uuid', 'title', 'client_name', 'client_email', 'slug', 'deliverable'),
        }),
        ('Financial', {
            'fields': ('total_investment', 'currency'),
        }),
        ('Status & Lifecycle', {
            'fields': (
                'status', 'is_active', 'expires_at',
                'reminder_days', 'urgency_reminder_days',
                'discount_percent', 'reminder_sent_at', 'urgency_email_sent_at',
            ),
        }),
        ('Tracking', {
            'fields': (
                'view_count', 'first_viewed_at', 'sent_at',
                'responded_at', 'revisit_alert_sent_at',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


class ProposalDefaultConfigAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ProposalDefaultConfig model.
    """
    list_display = ('language', 'updated_at', 'created_at')
    list_filter = ('language',)
    readonly_fields = ('created_at', 'updated_at')


class EmailTemplateConfigAdmin(admin.ModelAdmin):
    """
    Admin configuration for the EmailTemplateConfig model.
    """
    list_display = ('template_key', 'is_active', 'updated_at', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('template_key',)
    readonly_fields = ('created_at', 'updated_at')


class ProposalRequirementItemAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the ProposalRequirementItem model.
    """
    list_display = ('name', 'group', 'icon', 'order')
    list_filter = ('group__proposal',)
    search_fields = ('name', 'description')


class DocumentAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Document model.
    """
    list_display = (
        'title', 'slug', 'status', 'language', 'cover_type',
        'include_portada', 'include_subportada', 'include_contraportada',
        'client_name', 'created_at',
    )
    list_filter = ('status', 'language', 'cover_type', 'include_portada', 'include_subportada', 'include_contraportada')
    search_fields = ('title', 'client_name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    fieldsets = (
        ('Identity', {
            'fields': ('uuid', 'title', 'slug', 'client_name'),
        }),
        ('Content', {
            'fields': ('content_markdown', 'content_json'),
        }),
        ('Settings', {
            'fields': ('status', 'language', 'cover_type'),
        }),
        ('Portadas', {
            'fields': ('include_portada', 'include_subportada', 'include_contraportada'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


class ProjectAppAdminSite(admin.AdminSite):
    """
    Custom AdminSite configuration to organize models by sections.
    """
    site_header = 'ProjectApp Administration'
    site_title = 'ProjectApp Admin'
    index_title = 'Welcome to the ProjectApp Control Panel'

    def get_app_list(self, request):
        app_dict = self._build_app_dict(request)
        custom_app_list = [
            {
                'name': _('Contact Management'),
                'app_label': 'contact_management',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] == 'Contact'
                ]
            },
            {
                'name': _('Portfolio Works Management'),
                'app_label': 'portfolio_works_management',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] == 'PortfolioWork'
                ]
            },
            {
                'name': _('Business Proposals'),
                'app_label': 'business_proposals',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] in [
                        'BusinessProposal', 'ProposalSection',
                        'ProposalRequirementGroup', 'ProposalRequirementItem',
                        'ProposalViewEvent', 'ProposalSectionView',
                        'ProposalChangeLog', 'ProposalDefaultConfig',
                        'EmailTemplateConfig',
                    ]
                ]
            },
            {
                'name': _('Blog'),
                'app_label': 'blog',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] == 'BlogPost'
                ]
            },
            {
                'name': _('Documents'),
                'app_label': 'documents',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] == 'Document'
                ]
            },
        ]
        return custom_app_list

admin_site = ProjectAppAdminSite(name='myadmin')

admin_site.register(Contact, ContactAdmin)
admin_site.register(PortfolioWork, PortfolioWorkAdmin)
admin_site.register(BusinessProposal, BusinessProposalAdmin)
admin_site.register(ProposalSection)
admin_site.register(ProposalRequirementGroup)
admin_site.register(ProposalRequirementItem, ProposalRequirementItemAdmin)
admin_site.register(BlogPost, BlogPostAdmin)
admin_site.register(ProposalViewEvent)
admin_site.register(ProposalSectionView)
admin_site.register(ProposalChangeLog)
admin_site.register(ProposalDefaultConfig, ProposalDefaultConfigAdmin)
admin_site.register(EmailTemplateConfig, EmailTemplateConfigAdmin)
admin_site.register(Document, DocumentAdmin)
admin_site.register(DocumentType, admin.ModelAdmin)
admin_site.register(IssuerProfile, admin.ModelAdmin)
admin_site.register(CompanySettings, admin.ModelAdmin)
admin_site.register(ProposalDocument, admin.ModelAdmin)
admin_site.register(ContractTemplate, admin.ModelAdmin)