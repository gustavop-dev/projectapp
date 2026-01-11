from django.conf import settings
from django.urls import path, include, re_path
from content.admin import admin_site
from django.conf.urls.static import static
from django.views.static import serve
from django.views.generic import TemplateView
import os

urlpatterns = [
    path('admin/', admin_site.urls),
    path('api/', include('content.urls')),

    # Vue routes - Root
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # Legacy routes (for backward compatibility - will be redirected by Vue Router)
    path('web-designs/', TemplateView.as_view(template_name='index.html'), name='webDesigns'),
    path('3d-animations/', TemplateView.as_view(template_name='index.html'), name='3dAnimations'),
    path('about-us/', TemplateView.as_view(template_name='index.html'), name='aboutUs'),
    path('custom-software/', TemplateView.as_view(template_name='index.html'), name='customSoftware'),
    path('e-commerce-prices/', TemplateView.as_view(template_name='index.html'), name='eCommercePrices'),
    re_path(r'^hosting/(?P<plan>[\w-]+)?/?$', TemplateView.as_view(template_name='index.html'), name='hosting'),
    re_path(r'^portfolio-works/(?P<example>[\w-]+)?/?$', TemplateView.as_view(template_name='index.html'), name='portfolioWorks'),
    path('contact/', TemplateView.as_view(template_name='index.html'), name='contact'),
    path('contact-success/', TemplateView.as_view(template_name='index.html'), name='contactSuccess'),
    
    # Spanish Colombia (es-co) locale routes
    path('es-co/', TemplateView.as_view(template_name='index.html'), name='home-es-co'),
    path('es-co/web-designs/', TemplateView.as_view(template_name='index.html'), name='webDesigns-es-co'),
    path('es-co/3d-animations/', TemplateView.as_view(template_name='index.html'), name='3dAnimations-es-co'),
    path('es-co/about-us/', TemplateView.as_view(template_name='index.html'), name='aboutUs-es-co'),
    path('es-co/custom-software/', TemplateView.as_view(template_name='index.html'), name='customSoftware-es-co'),
    path('es-co/e-commerce-prices/', TemplateView.as_view(template_name='index.html'), name='eCommercePrices-es-co'),
    re_path(r'^es-co/hosting/(?P<plan>[\w-]+)?/?$', TemplateView.as_view(template_name='index.html'), name='hosting-es-co'),
    re_path(r'^es-co/portfolio-works/(?P<example>[\w-]+)?/?$', TemplateView.as_view(template_name='index.html'), name='portfolioWorks-es-co'),
    path('es-co/contact/', TemplateView.as_view(template_name='index.html'), name='contact-es-co'),
    path('es-co/contact-success/', TemplateView.as_view(template_name='index.html'), name='contactSuccess-es-co'),
    
    # English United States (en-us) locale routes
    path('en-us/', TemplateView.as_view(template_name='index.html'), name='home-en-us'),
    path('en-us/web-designs/', TemplateView.as_view(template_name='index.html'), name='webDesigns-en-us'),
    path('en-us/3d-animations/', TemplateView.as_view(template_name='index.html'), name='3dAnimations-en-us'),
    path('en-us/about-us/', TemplateView.as_view(template_name='index.html'), name='aboutUs-en-us'),
    path('en-us/custom-software/', TemplateView.as_view(template_name='index.html'), name='customSoftware-en-us'),
    path('en-us/e-commerce-prices/', TemplateView.as_view(template_name='index.html'), name='eCommercePrices-en-us'),
    re_path(r'^en-us/hosting/(?P<plan>[\w-]+)?/?$', TemplateView.as_view(template_name='index.html'), name='hosting-en-us'),
    re_path(r'^en-us/portfolio-works/(?P<example>[\w-]+)?/?$', TemplateView.as_view(template_name='index.html'), name='portfolioWorks-en-us'),
    path('en-us/contact/', TemplateView.as_view(template_name='index.html'), name='contact-en-us'),
    path('en-us/contact-success/', TemplateView.as_view(template_name='index.html'), name='contactSuccess-en-us'),
]

urlpatterns += [
    re_path(r'^spline/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'spline'),
    }),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)