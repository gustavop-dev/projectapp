from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Contact, Design, Model3D, Product, Category, Item, Hosting, PortfolioWork

class PortfolioWorkAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the PortfolioWork model.
    Display specific fields of the PortfolioWork model.
    """
    list_display = ('title_en', 'title_es', 'cover_image', 'project_url', 'category_title_en')

class ContactAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Contact model.
    Display specific fields of the Contact model.
    """
    list_display = ('email', 'subject', 'message')

class DesignAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Design model.
    Display specific fields of the Design model.
    """
    list_display = ('title_en', 'title_es', 'cover_image', 'detail_image')

class Model3DAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Model3D model.
    Display specific fields of the Model3D model.
    """
    list_display = ('title_en', 'title_es', 'image', 'file')

class ProductAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Product model.
    Display specific fields of the Product model.
    """
    list_display = ('title_en', 'title_es', 'price', 'development_time_en', 'image')
    filter_horizontal = ('categories',)

class CategoryAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Category model.
    Display specific fields of the Category model.
    """
    list_display = ('name_en', 'name_es')
    filter_horizontal = ('items',)

class ItemAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Item model.
    Display specific fields of the Item model.
    """
    list_display = ('name_en', 'name_es')

class HostingAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Hosting model.
    Display specific fields of the Hosting model.
    """
    list_display = ('title_en', 'title_es', 'semi_annually_price', 'annual_price', 'cpu_cores_en', 'ram_en', 'storage_en', 'bandwidth_en')

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
                'name': _('Design Management'),
                'app_label': 'design_management',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] == 'Design'
                ]
            },
            {
                'name': _('Model3D Management'),
                'app_label': 'model3d_management',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] == 'Model3D'
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
                'name': _('Product Management'),
                'app_label': 'product_management',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] in ['Product', 'Category', 'Item']
                ]
            },
            {
                'name': _('Hosting Management'),
                'app_label': 'hosting_management',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] == 'Hosting'
                ]
            }
        ]
        return custom_app_list

admin_site = ProjectAppAdminSite(name='myadmin')

admin_site.register(Contact, ContactAdmin)
admin_site.register(Design, DesignAdmin)
admin_site.register(Model3D, Model3DAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Item, ItemAdmin)
admin_site.register(Hosting, HostingAdmin)
admin_site.register(PortfolioWork, PortfolioWorkAdmin)