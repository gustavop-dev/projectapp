"""Query and bounded-retention contracts for the monitoring module."""

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APIClient

from monitoring.models import Case, CaseActivity, Report, Resource, Source


MAX_CASE_LIST_QUERIES = 6


@pytest.fixture
def staff_client(db):
    user = get_user_model().objects.create_user(username='monitoring-query-staff', is_staff=True)
    client = APIClient()
    client.force_login(user)
    return client


@pytest.fixture
def monitored_source(db):
    server = Resource.objects.create(key='srv1681495', name='VPS de producción', kind='server')
    resource = Resource.objects.create(key='projectapp', name='ProjectApp', kind='project', server=server)
    return Source.objects.create(resource=resource, key='silk', name='Silk')


@pytest.fixture
def twenty_six_cases(db):
    now = timezone.now()
    server = Resource.objects.create(key='srv1681495', name='VPS de producción', kind='server')
    cases = []
    for number in range(26):
        resource = Resource.objects.create(
            key=f'project-{number}', name=f'Proyecto {number}', kind='project', server=server,
        )
        source = Source.objects.create(resource=resource, key='integrity', name='Integridad')
        cases.append(Case(
            source=source,
            fingerprint=f'backup:{number}',
            fingerprint_hash=f'{number:064x}',
            title=f'Backup atrasado {number}',
            severity='warning',
            first_seen_at=now,
            last_seen_at=now,
            evidence={'message': 'detalle que no pertenece al listado'},
            detections=1,
        ))
    return Case.objects.bulk_create(cases)


@pytest.mark.django_db
def test_case_list_limits_results_to_page_size(staff_client, twenty_six_cases):
    """Falla si el listado devuelve más de la página administrativa de 25 casos."""
    response = staff_client.get('/api/monitoring/cases/')

    assert response.status_code == 200
    assert response.json()['count'] == 26
    assert len(response.json()['results']) == 25


@pytest.mark.django_db
def test_case_list_query_budget_is_stable_for_single_source(staff_client, twenty_six_cases):
    """Falla si filtrar un origen reduce el número de filas pero aumenta las consultas."""
    with CaptureQueriesContext(connection) as full_queries:
        staff_client.get('/api/monitoring/cases/')
    with CaptureQueriesContext(connection) as filtered_queries:
        filtered_response = staff_client.get(f'/api/monitoring/cases/?source={twenty_six_cases[0].source_id}')

    assert filtered_response.json()['count'] == 1
    assert len(full_queries) == len(filtered_queries)
    assert len(full_queries) <= MAX_CASE_LIST_QUERIES


@pytest.mark.django_db
def test_case_list_defers_evidence_from_select(staff_client, twenty_six_cases):
    """Falla si el listado carga el JSON de evidencia reservado al detalle del caso."""
    with CaptureQueriesContext(connection) as queries:
        staff_client.get('/api/monitoring/cases/')

    case_select = next(
        query['sql'] for query in queries
        if 'monitoring_case' in query['sql'] and 'SELECT' in query['sql'] and 'COUNT(' not in query['sql']
    )

    assert '"evidence"' not in case_select


@pytest.mark.django_db
@freeze_time('2024-03-01T12:00:00Z')
def test_report_list_defers_large_report_text(staff_client, monitored_source):
    """Falla si el listado carga o expone el texto completo de los informes técnicos."""
    Report.objects.create(
        source=monitored_source,
        title='Informe de consultas lentas',
        observed_at=timezone.now(),
        text='x' * 50_000,
    )

    with CaptureQueriesContext(connection) as queries:
        response = staff_client.get('/api/monitoring/reports/')

    report_select = next(
        query['sql'] for query in queries
        if 'monitoring_report' in query['sql'] and 'SELECT' in query['sql'] and 'COUNT(' not in query['sql']
    )
    assert response.status_code == 200
    assert response.json()['results'][0]['title'] == 'Informe de consultas lentas'
    assert 'text' not in response.json()['results'][0]
    assert '"text"' not in report_select


@pytest.mark.django_db
def test_monitoring_history_indexes_cover_list_prefixes():
    """Falla si una migración pierde los índices que sostienen los listados ordenados."""
    with connection.cursor() as cursor:
        case_constraints = connection.introspection.get_constraints(cursor, Case._meta.db_table)
        activity_constraints = connection.introspection.get_constraints(cursor, CaseActivity._meta.db_table)

    case_indexes = {tuple(value['columns']) for value in case_constraints.values() if value['index']}
    activity_indexes = {tuple(value['columns']) for value in activity_constraints.values() if value['index']}
    assert {('state', 'last_seen_at'), ('severity', 'last_seen_at'), ('last_seen_at', 'id')} <= case_indexes
    assert ('case_id', 'created_at') in activity_indexes
