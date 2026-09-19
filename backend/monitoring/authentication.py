from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import Credential


class IngestAuthentication(BaseAuthentication):
    """Machine credentials cannot authenticate to administrative endpoints."""

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if len(parts) != 2 or parts[0].lower() != b'bearer':
            raise AuthenticationFailed('Credencial de monitoreo requerida.')
        try:
            token = parts[1].decode('ascii')
        except UnicodeDecodeError:
            raise AuthenticationFailed('Credencial inválida.')
        credential = Credential.objects.filter(token_hash=Credential.hash_token(token), revoked_at__isnull=True).first()
        if credential is None:
            raise AuthenticationFailed('Credencial inválida o revocada.')
        return (None, credential)

    def authenticate_header(self, request):
        return 'Bearer'
