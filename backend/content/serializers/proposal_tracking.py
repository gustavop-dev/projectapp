"""Validation contracts for anonymous proposal engagement heartbeats."""

import math

from django.utils import timezone
from rest_framework import serializers


class ProposalSectionHeartbeatSerializer(serializers.Serializer):
    section_type = serializers.CharField(max_length=50, trim_whitespace=True)
    section_title = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default='',
    )
    subsection_key = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default='',
    )
    time_spent_seconds = serializers.FloatField(
        min_value=0,
        max_value=86_400,
    )
    entered_at = serializers.DateTimeField(required=False, default=timezone.now)

    def validate_time_spent_seconds(self, value):
        if not math.isfinite(value):
            raise serializers.ValidationError('Must be a finite number.')
        return value


class ProposalEngagementSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=64, trim_whitespace=True)
    view_mode = serializers.ChoiceField(
        choices=('executive', 'detailed', 'technical', 'legal', 'unknown'),
        default='unknown',
    )
    is_final = serializers.BooleanField(default=False)
    sections = ProposalSectionHeartbeatSerializer(
        many=True,
        allow_empty=False,
        max_length=100,
    )
