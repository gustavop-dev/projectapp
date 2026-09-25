from rest_framework import serializers

from content.models import CommunicationFolder


class CommunicationFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationFolder
        fields = ('id', 'name', 'parent', 'client', 'project', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
