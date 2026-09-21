from pathlib import Path
from rest_framework import serializers
from content.models import ProjectBrandAsset


class ProjectBrandAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectBrandAsset
        fields = ('id', 'project', 'title', 'category', 'filename', 'size', 'created_at')
        read_only_fields = fields


class ProjectBrandAssetUploadSerializer(serializers.ModelSerializer):
    # Files are opaque downloads, never rendered inline or served from MEDIA_URL.
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.zip',
                          '.ai', '.eps', '.psd', '.fig', '.sketch', '.docx', '.pptx',
                          '.txt', '.md', '.json', '.ttf', '.otf', '.woff', '.woff2'}

    class Meta:
        model = ProjectBrandAsset
        fields = ('title', 'category', 'file')

    def validate_file(self, value):
        if value.size > 25 * 1024 * 1024:
            raise serializers.ValidationError('El archivo no puede superar 25 MB.')
        if Path(value.name).suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError('Formato de archivo no permitido.')
        return value

    def create(self, validated_data):
        upload = validated_data['file']
        return super().create({**validated_data, 'filename': upload.name, 'size': upload.size})
