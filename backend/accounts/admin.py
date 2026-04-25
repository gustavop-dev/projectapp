from django import forms
from django.contrib import admin

from content.admin import admin_site

from accounts.services.credential_cipher import encrypt_password

from .models import (
    UserProfile,
    VerificationCode,
    Project,
    Requirement,
    RequirementComment,
    RequirementHistory,
    ChangeRequest,
    ChangeRequestComment,
    BugReport,
    BugComment,
    Deliverable,
    DataModelEntity,
    ProjectDataModelEntity,
    DeliverableVersion,
    DeliverableFile,
    DeliverableClientFolder,
    DeliverableClientUpload,
    Notification,
    HostingSubscription,
    Payment,
    PaymentHistory,
)


class ProjectAdminForm(forms.ModelForm):
    admin_password = forms.CharField(
        label='Contraseña admin',
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text='Déjalo vacío para mantener la contraseña actual.',
    )

    class Meta:
        model = Project
        exclude = ('admin_password_encrypted',)


class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = ('name', 'client', 'status', 'production_url', 'admin_url', 'updated_at')
    list_filter = ('status',)
    search_fields = ('name', 'client__email', 'production_url', 'admin_url')
    fieldsets = (
        (None, {'fields': ('name', 'description', 'client', 'status', 'progress')}),
        ('Fechas', {'fields': ('start_date', 'estimated_end_date', 'hosting_start_date')}),
        ('Datos financieros', {
            'classes': ('collapse',),
            'fields': ('payment_milestones', 'hosting_tiers'),
        }),
        ('Accesos rápidos', {
            'fields': (
                'production_url', 'staging_url', 'admin_url', 'repository_url',
                'admin_username', 'admin_password',
            ),
        }),
    )

    def save_model(self, request, obj, form, change):
        plain = form.cleaned_data.get('admin_password')
        if plain:
            obj.admin_password_encrypted = encrypt_password(plain)
        super().save_model(request, obj, form, change)


admin_site.register(UserProfile)
admin_site.register(VerificationCode)
admin_site.register(Project, ProjectAdmin)
admin_site.register(Requirement)
admin_site.register(RequirementComment)
admin_site.register(RequirementHistory)
admin_site.register(ChangeRequest)
admin_site.register(ChangeRequestComment)
admin_site.register(BugReport)
admin_site.register(BugComment)
admin_site.register(Deliverable)
admin_site.register(DataModelEntity)
admin_site.register(ProjectDataModelEntity)
admin_site.register(DeliverableVersion)
admin_site.register(DeliverableFile)
admin_site.register(DeliverableClientFolder)
admin_site.register(DeliverableClientUpload)
admin_site.register(Notification)
admin_site.register(HostingSubscription)
admin_site.register(Payment)
admin_site.register(PaymentHistory)
