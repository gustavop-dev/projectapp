from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Component, Contact, Design, Model3D, UISectionCategory, Section, Example, Product, Category, Item

class ComponentAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Component model.
    Display all fields of the Component model.
    """
    list_display = ('title_en', 'title_es', 'image')
    filter_horizontal = ('examples',)  # Improved UI for ManyToMany field


class UISectionCategoryAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the UISectionCategory model.
    Display all fields of the UISectionCategory model.
    """
    list_display = ('title_en', 'title_es', 'description_en', 'description_es')
    filter_horizontal = ('sections',)  # Improved UI for ManyToMany field


class ContactAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Contact model.
    Display all fields of the Contact model.
    """
    list_display = ('email', 'subject', 'message')


class DesignAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Design model.
    Display all fields of the Design model.
    """
    list_display = ('title_en', 'title_es', 'cover_image', 'detail_image')  # Changed to cover_image


class Model3DAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Model3D model.
    Display all fields of the Model3D model.
    """
    list_display = ('title_en', 'title_es', 'image', 'file')


class ProductAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Product model.
    Display all fields of the Product model.
    """
    list_display = ('title_en', 'title_es', 'price', 'development_time_en', 'image')
    filter_horizontal = ('categories',)  # Improved UI for ManyToMany field


class CategoryAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Category model.
    Display all fields of the Category model.
    """
    list_display = ('name_en', 'name_es')
    filter_horizontal = ('items',)  # Improved UI for ManyToMany field


class ItemAdmin(admin.ModelAdmin):
    """
    Custom admin configuration for the Item model.
    Display all fields of the Item model.
    """
    list_display = ('name_en', 'name_es')


# Custom AdminSite to organize models by sections
class ProjectAppAdminSite(admin.AdminSite):
    site_header = 'ProjectApp Administration'
    site_title = 'ProjectApp Admin'
    index_title = 'Welcome to the ProjectApp Control Panel'

    def get_app_list(self, request):
        app_dict = self._build_app_dict(request)
        # Custom structure for the admin index
        custom_app_list = [
            {
                'name': _('Component Management'),
                'app_label': 'component_management',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] in ['Component', 'UISectionCategory', 'Section', 'Example']
                ]
            },
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
                'name': _('Product Management'),
                'app_label': 'product_management',
                'models': [
                    model for model in app_dict.get('content', {}).get('models', [])
                    if model['object_name'] in ['Product', 'Category', 'Item']
                ]
            }
        ]
        return custom_app_list


# Create an instance of the custom AdminSite
admin_site = ProjectAppAdminSite(name='myadmin')

# Register models with the custom AdminSite
admin_site.register(Component, ComponentAdmin)
admin_site.register(UISectionCategory, UISectionCategoryAdmin)
admin_site.register(Section)
admin_site.register(Example)
admin_site.register(Contact, ContactAdmin)
admin_site.register(Design, DesignAdmin)
admin_site.register(Model3D, Model3DAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Item, ItemAdmin)
