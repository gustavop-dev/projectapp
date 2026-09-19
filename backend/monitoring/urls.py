from django.urls import path

from . import views

urlpatterns = [
    path('v1/ingest/', views.receive),
    path('catalog/', views.catalog),
    path('resources/<int:pk>/', views.resource_link),
    path('cases/', views.cases),
    path('cases/<int:pk>/', views.case_detail),
    path('cases/<int:pk>/state/', views.case_state),
    path('cases/<int:pk>/notes/', views.case_note),
    path('reports/', views.reports),
    path('reports/<int:pk>/', views.report_detail),
]
