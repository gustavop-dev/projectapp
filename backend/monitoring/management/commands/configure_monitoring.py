"""Explicit deploy-time provisioning; never invoked by migrations or imports."""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from monitoring.models import Credential, Resource, Source


class SourceInput(serializers.Serializer):
    key = serializers.SlugField(max_length=80)
    name = serializers.CharField(max_length=120)
    expected_interval = serializers.IntegerField(min_value=60, max_value=2678400)
    enabled = serializers.BooleanField(default=True)


class ResourceInput(serializers.Serializer):
    key = serializers.SlugField(max_length=100)
    name = serializers.CharField(max_length=160)
    sources = SourceInput(many=True)


class ManifestInput(serializers.Serializer):
    server = ResourceInput()
    projects = ResourceInput(many=True)


class Command(BaseCommand):
    help = 'Importar inventario no secreto; emitir o revocar credenciales de ingestión.'

    def add_arguments(self, parser):
        parser.add_argument('--manifest', type=Path)
        parser.add_argument('--issue', help='Etiqueta para una nueva credencial; el token sale una sola vez.')
        parser.add_argument('--revoke', type=int)

    @transaction.atomic
    def handle(self, *args, **options):
        if options['revoke'] is not None:
            if not Credential.objects.filter(pk=options['revoke']).update(revoked_at=timezone.now()):
                raise CommandError('Credencial desconocida.')
            return
        if not options['manifest']:
            raise CommandError('--manifest es obligatorio para importar o emitir.')
        try:
            serializer = ManifestInput(data=json.loads(options['manifest'].read_text()))
            serializer.is_valid(raise_exception=True)
        except (ValueError, OSError, serializers.ValidationError) as exc:
            raise CommandError(f'Manifiesto inválido: {exc}') from exc
        manifest = serializer.validated_data
        keys = [manifest['server']['key'], *[p['key'] for p in manifest['projects']]]
        if len(keys) != len(set(keys)):
            raise CommandError('Las claves de recursos deben ser únicas.')
        resources = []
        server = None
        for index, item in enumerate([manifest['server'], *manifest['projects']]):
            kind = 'server' if index == 0 else 'project'
            existing = Resource.objects.filter(key=item['key']).first()
            if existing and (existing.kind != kind or existing.server_id != (server.pk if server else None)):
                raise CommandError('El recurso existe con otra identidad; revisar la migración manualmente.')
            resource, _ = Resource.objects.update_or_create(key=item['key'], defaults={'name': item['name'], 'kind': kind, 'server': server, 'environment': 'production'})
            resources.append(resource)
            for source in item['sources']:
                Source.objects.update_or_create(resource=resource, key=source['key'], defaults={k: v for k, v in source.items() if k != 'key'})
            if server is None:
                server = resource
        if options['issue']:
            credential, token = Credential.issue(options['issue'])
            credential.resources.set(resources)
            self.stdout.write(token)
        else:
            self.stdout.write(f'Inventario importado: {len(resources)} recursos.')
