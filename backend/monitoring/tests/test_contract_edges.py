"""Boundary contracts that keep monitoring inventory and follow-up isolated."""

import json
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.dateparse import parse_datetime
from freezegun import freeze_time
from rest_framework.test import APIClient

from accounts.models import Project
from monitoring.models import Case, Credential, Delivery, Resource, Source
from monitoring.tests.test_followup_api import regular_user, staff_client, staff_user
from monitoring.tests.test_ingest import (
    OBSERVED_AT,
    detection_payload,
    machine_client,
    machine_credential,
    monitored_resource,
    monitored_source,
)


INGEST_URL = '/api/monitoring/v1/ingest/'


def manifest_data():
    return {
        'server': {
            'key': 'srv1681495', 'name': 'VPS de producción',
            'sources': [{'key': 'integrity', 'name': 'Integridad', 'expected_interval': 300}],
        },
        'projects': [{
            'key': 'projectapp', 'name': 'ProjectApp',
            'sources': [{'key': 'silk', 'name': 'Silk', 'expected_interval': 600}],
        }],
    }


def manifest_path(tmp_path, data=None):
    path = tmp_path / 'monitoring-manifest.json'
    path.write_text(json.dumps(data or manifest_data()))
    return path


def project_for_link(username):
    user = get_user_model().objects.create_user(username=username)
    return Project.objects.create(name=f'Proyecto {username}', client=user)


@pytest.mark.django_db
def test_detection_links_the_report_from_its_own_source(machine_client, monitored_source, detection_payload):
    """Falla si una detección no conserva el informe técnico que la originó."""
    report = machine_client.post(
        INGEST_URL,
        detection_payload(
            external_id='silk:report:weekly', kind='report', title='Informe Silk',
            text='Una consulta lenta.', omit=('fingerprint',),
        ),
        format='json',
    )
    detection = machine_client.post(
        INGEST_URL,
        detection_payload(external_id='silk:detection:linked', report_id='silk:report:weekly'),
        format='json',
    )

    receipt = Delivery.objects.get(source=monitored_source, external_id='silk:detection:linked')
    assert report.status_code == 201
    assert detection.status_code == 201
    assert receipt.report_id == report.json()['report_id']
    assert receipt.case_id == detection.json()['case_id']


@pytest.mark.django_db
def test_foreign_source_report_reference_rolls_back_detection(machine_client, machine_credential, monitored_resource, monitored_source, detection_payload):
    """Falla si un reporte de otro origen puede enlazarse o deja una recepción parcial."""
    foreign_resource = Resource.objects.create(
        key='mimittos-project', name='Mimittos', kind='project', server=monitored_resource.server,
    )
    foreign_source = Source.objects.create(resource=foreign_resource, key='silk', name='Silk')
    credential, _ = machine_credential
    credential.resources.add(foreign_resource)
    foreign_report = machine_client.post(
        INGEST_URL,
        detection_payload(
            external_id='foreign:silk:report', resource=foreign_resource.key,
            kind='report', title='Informe externo', text='No compartir.', omit=('fingerprint',),
        ),
        format='json',
    )
    rejected = machine_client.post(
        INGEST_URL,
        detection_payload(external_id='silk:detection:foreign-report', report_id='foreign:silk:report'),
        format='json',
    )

    assert foreign_report.status_code == 201
    assert rejected.status_code == 404
    assert Delivery.objects.filter(source=monitored_source).count() == 0
    assert Case.objects.filter(source=monitored_source).count() == 0
    assert Delivery.objects.filter(source=foreign_source).count() == 1


@pytest.mark.django_db
def test_case_kind_filter_separates_resource_scopes(staff_client, monitored_resource):
    """Falla si las pestañas de proyectos y servidor muestran los mismos casos."""
    project_source = Source.objects.create(resource=monitored_resource, key='silk', name='Silk')
    server_source = Source.objects.create(resource=monitored_resource.server, key='integrity', name='Integridad')
    observed_at = parse_datetime(OBSERVED_AT)
    project_case = Case.objects.create(
        source=project_source, fingerprint='silk:slow', fingerprint_hash='1' * 64,
        title='Consulta lenta', severity='warning', first_seen_at=observed_at, last_seen_at=observed_at,
    )
    server_case = Case.objects.create(
        source=server_source, fingerprint='integrity:disk', fingerprint_hash='2' * 64,
        title='Disco alto', severity='critical', first_seen_at=observed_at, last_seen_at=observed_at,
    )

    projects = staff_client.get('/api/monitoring/cases/?kind=project')
    server = staff_client.get('/api/monitoring/cases/?kind=server')

    assert projects.status_code == 200
    assert [item['id'] for item in projects.json()['results']] == [project_case.pk]
    assert server.status_code == 200
    assert [item['id'] for item in server.json()['results']] == [server_case.pk]


@pytest.mark.django_db
def test_manifest_rejects_existing_resource_with_different_identity(tmp_path):
    """Falla si un manifiesto puede convertir un proyecto existente en el servidor inventariado."""
    existing = Resource.objects.create(key='srv1681495', name='No cambiar', kind='project')

    with pytest.raises(CommandError, match='otra identidad'):
        call_command('configure_monitoring', '--manifest', str(manifest_path(tmp_path)))

    existing.refresh_from_db()
    assert existing.kind == 'project'
    assert existing.name == 'No cambiar'
    assert Resource.objects.count() == 1


@pytest.mark.django_db
def test_manifest_issue_stores_only_credential_hash(tmp_path):
    """Falla si emitir una credencial no cubre el inventario completo o guarda el secreto plano."""
    stdout = StringIO()
    stderr = StringIO()

    call_command(
        'configure_monitoring', '--manifest', str(manifest_path(tmp_path)), '--issue', 'collector',
        stdout=stdout, stderr=stderr,
    )

    credential = Credential.objects.get(label='collector')
    token = stdout.getvalue().strip()
    assert set(credential.resources.values_list('key', flat=True)) == {'srv1681495', 'projectapp'}
    assert credential.token_hash == Credential.hash_token(token)
    assert token not in credential.token_hash
    assert f'id={credential.pk}' in stderr.getvalue()


@pytest.mark.django_db
def test_manifest_refresh_preserves_live_source_state(tmp_path):
    """Falla si reimportar inventario borra el estado operativo recibido del colector."""
    server = Resource.objects.create(key='srv1681495', name='VPS de producción', kind='server')
    resource = Resource.objects.create(key='projectapp', name='ProjectApp', kind='project', server=server)
    seen_at = parse_datetime('2024-01-02T09:00:00Z')
    source = Source.objects.create(
        resource=resource, key='silk', name='Silk anterior', expected_interval=300,
        enabled=False, last_seen_at=seen_at, last_error='esperando reporte',
    )

    call_command('configure_monitoring', '--manifest', str(manifest_path(tmp_path)))

    source.refresh_from_db()
    assert source.name == 'Silk'
    assert source.expected_interval == 600
    assert source.enabled is False
    assert source.last_seen_at == seen_at
    assert source.last_error == 'esperando reporte'


@pytest.mark.django_db
def test_revoked_credential_cannot_create_an_ingest_delivery(machine_client, machine_credential, monitored_source, detection_payload):
    """Falla si revocar una credencial desde el comando deja activo su token de máquina."""
    credential, _ = machine_credential
    call_command('configure_monitoring', '--revoke', str(credential.pk))

    response = machine_client.post(INGEST_URL, detection_payload(), format='json')

    assert response.status_code == 401
    assert Delivery.objects.filter(source=monitored_source).count() == 0


@pytest.mark.django_db
def test_oversized_machine_delivery_is_rejected_before_persistence(machine_client, monitored_source):
    """Falla si un cuerpo mayor a 128 KiB puede ocupar la cola de seguimiento."""
    response = machine_client.generic(
        'POST', INGEST_URL, b'x' * (128 * 1024 + 1), content_type='application/json',
    )

    assert response.status_code == 413
    assert Delivery.objects.filter(source=monitored_source).count() == 0


@pytest.mark.django_db
@freeze_time('2024-01-02T12:00:00Z')
@pytest.mark.parametrize(
    ('enabled', 'last_seen_at', 'last_error', 'expected'),
    [
        (True, None, '', 'no_data'),
        (True, parse_datetime('2024-01-02T11:55:00Z'), '', 'current'),
        (True, parse_datetime('2024-01-02T11:49:00Z'), '', 'stale'),
        (True, parse_datetime('2024-01-02T11:55:00Z'), 'collector failed', 'stale'),
        (False, parse_datetime('2024-01-02T11:55:00Z'), '', 'disabled'),
    ],
)
def test_source_health_classifies_freshness(enabled, last_seen_at, last_error, expected, monitored_source):
    """Falla si el catálogo confunde origen sin datos, vencido, fallido o deshabilitado."""
    monitored_source.enabled = enabled
    monitored_source.last_seen_at = last_seen_at
    monitored_source.last_error = last_error
    monitored_source.save(update_fields=['enabled', 'last_seen_at', 'last_error'])

    assert monitored_source.health == expected


@pytest.mark.django_db
def test_staff_can_link_then_clear_project_resource(staff_client, monitored_resource):
    """Falla si el panel no puede vincular y luego desvincular el proyecto del recurso."""
    project = project_for_link('monitoring-link-owner')

    linked = staff_client.patch(
        f'/api/monitoring/resources/{monitored_resource.pk}/', {'project': project.pk}, format='json',
    )
    cleared = staff_client.patch(
        f'/api/monitoring/resources/{monitored_resource.pk}/', {'project': None}, format='json',
    )

    monitored_resource.refresh_from_db()
    assert linked.status_code == 200
    assert linked.json()['project'] == project.pk
    assert cleared.status_code == 200
    assert monitored_resource.project_id is None


@pytest.mark.django_db
def test_second_resource_cannot_claim_linked_project(staff_client, monitored_resource):
    """Falla si dos recursos terminan vinculados al mismo proyecto de plataforma."""
    project = project_for_link('monitoring-conflict-owner')
    monitored_resource.project = project
    monitored_resource.save(update_fields=['project'])
    other_resource = Resource.objects.create(
        key='other-project', name='Otro proyecto', kind='project', server=monitored_resource.server,
    )

    response = staff_client.patch(
        f'/api/monitoring/resources/{other_resource.pk}/', {'project': project.pk}, format='json',
    )

    other_resource.refresh_from_db()
    assert response.status_code == 409
    assert other_resource.project_id is None
    assert Resource.objects.get(pk=monitored_resource.pk).project_id == project.pk


@pytest.mark.django_db
def test_non_staff_user_cannot_link_monitoring_resource(regular_user, monitored_resource):
    """Falla si una sesión no administrativa puede cambiar el inventario de recursos."""
    client = APIClient()
    client.force_login(regular_user)
    project = project_for_link('monitoring-non-staff-owner')

    response = client.patch(
        f'/api/monitoring/resources/{monitored_resource.pk}/', {'project': project.pk}, format='json',
    )

    assert response.status_code == 403
    monitored_resource.refresh_from_db()
    assert monitored_resource.project_id is None
