from django.urls import path
from content.views.component import uisectioncategory_list
from content.views.contact import contact_list, new_contact
from content.views.design import design_list
from content.views.model_3d import model3d_list
from content.views.product import product_list
from content.views.hosting import hosting_list
from content.views.portfolio_works import portfolio_works_list

urlpatterns = [
    path('ui_section_categories/', uisectioncategory_list, name='uisectioncategory-list'),
    path('contacts/', contact_list, name='contact-list'),
    path('designs/', design_list, name='design-list'),
    path('models3d/', model3d_list, name='model3d-list'),
    path('products/', product_list, name='product-list'),
    path('hostings/', hosting_list, name='hosting-list'),
    path('portfolio_works/', portfolio_works_list, name='portfolio-works-list'),
    path('new-contact/', new_contact, name='new-contact'),
]
