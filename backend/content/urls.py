# myapp/urls.py
from django.urls import path
from .views import create_contact, get_models3d, get_designs, get_categories_development

urlpatterns = [
    path('contact/', create_contact, name='create_contact'),
    path('models-3d/', get_models3d, name="get_models3d"),
    path('web-designs/', get_designs, name="get_designs"),
    path('categories-development/', get_categories_development, name="get_categories_development"),
]
