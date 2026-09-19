import json
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from accounts.models import Project

from .models import Case, CaseActivity, Delivery, Report, Resource, Source


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'key', 'name', 'kind', 'server', 'project', 'environment', 'enabled']


class ResourceLinkSerializer(serializers.Serializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), allow_null=True)


class SourceSerializer(serializers.ModelSerializer):
    health = serializers.CharField(read_only=True)
    resource_name = serializers.CharField(source='resource.name')

    class Meta:
        model = Source
        fields = ['id', 'resource', 'resource_name', 'key', 'name', 'enabled', 'expected_interval', 'last_seen_at', 'last_received_at', 'last_error', 'health']


class CaseSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer(source='source.resource', read_only=True)
    source_name = serializers.CharField(source='source.name')

    class Meta:
        model = Case
        fields = ['id', 'source', 'source_name', 'resource', 'resource_snapshot', 'title', 'severity', 'state', 'condition', 'first_seen_at', 'last_seen_at', 'closed_at', 'detections', 'version']


class ReportSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer(source='source.resource', read_only=True)
    source_name = serializers.CharField(source='source.name')

    class Meta:
        model = Report
        fields = ['id', 'source', 'source_name', 'resource', 'resource_snapshot', 'title', 'observed_at']


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseActivity
        fields = ['id', 'actor_name', 'kind', 'text', 'from_state', 'to_state', 'created_at']


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['id', 'kind', 'observed_at', 'received_at', 'evidence', 'report']


class IngestSerializer(serializers.Serializer):
    schema_version = serializers.ChoiceField(choices=[1])
    external_id = serializers.RegexField(r'^[A-Za-z0-9._:-]+$', max_length=128)
    server = serializers.SlugField(max_length=100)
    resource = serializers.SlugField(max_length=100)
    source = serializers.SlugField(max_length=80)
    observed_at = serializers.DateTimeField()
    kind = serializers.ChoiceField(choices=['detection', 'recovery', 'report', 'heartbeat'])
    fingerprint = serializers.CharField(max_length=200, required=False)
    title = serializers.CharField(max_length=240, required=False)
    severity = serializers.ChoiceField(choices=Case.SEVERITIES, default='info')
    evidence = serializers.DictField(required=False, default=dict)
    text = serializers.CharField(max_length=100000, required=False, allow_blank=True)
    enabled = serializers.BooleanField(required=False)
    error = serializers.CharField(max_length=500, required=False, allow_blank=True)
    report_id = serializers.CharField(max_length=128, required=False)

    def validate_observed_at(self, value):
        if value > timezone.now() + timedelta(minutes=5):
            raise serializers.ValidationError('La observación está en el futuro.')
        return value

    def validate_evidence(self, value):
        # A deliberately small, flat vocabulary. No arbitrary headers, SQL or HTTP bodies.
        allowed = {'metric', 'value', 'unit', 'threshold', 'service', 'route', 'query_count', 'duration_ms', 'rule', 'path', 'result', 'count', 'sample_percent', 'message'}
        if set(value) - allowed or any(not isinstance(v, (str, int, float, bool, type(None))) for v in value.values()):
            raise serializers.ValidationError('Evidencia no admitida.')
        try:
            size = len(json.dumps(value, allow_nan=False))
        except ValueError as exc:
            raise serializers.ValidationError('Los valores deben ser finitos.') from exc
        if size > 8000:
            raise serializers.ValidationError('Evidencia demasiado extensa.')
        return value

    def validate(self, data):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError('El registro contiene campos desconocidos.')
        if data['kind'] in ('detection', 'recovery') and not data.get('fingerprint'):
            raise serializers.ValidationError({'fingerprint': 'Requerido.'})
        if data['kind'] in ('detection', 'report') and not data.get('title'):
            raise serializers.ValidationError({'title': 'Requerido.'})
        if data['kind'] == 'report' and 'text' not in data:
            raise serializers.ValidationError({'text': 'Requerido.'})
        if data['kind'] == 'heartbeat' and 'enabled' not in data:
            raise serializers.ValidationError({'enabled': 'Requerido.'})
        return data


class StateSerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=Case.STATES)
    version = serializers.IntegerField(min_value=1)
    note = serializers.CharField(max_length=4000, required=False, allow_blank=True)


class NoteSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=4000)


class FilterSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)
    resource = serializers.IntegerField(min_value=1, required=False)
    source = serializers.IntegerField(min_value=1, required=False)
    kind = serializers.ChoiceField(choices=['project', 'server'], required=False)
    state = serializers.ChoiceField(choices=Case.STATES, required=False)
    severity = serializers.ChoiceField(choices=Case.SEVERITIES, required=False)
    search = serializers.CharField(max_length=200, required=False, allow_blank=True)
    since = serializers.DateField(required=False)
    until = serializers.DateField(required=False)
