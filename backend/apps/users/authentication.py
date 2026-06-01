from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .jwt_utils import decode_access_token

User = get_user_model()


class BearerTokenAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith(f'{self.keyword} '):
            return None

        token = auth_header[len(self.keyword) + 1:].strip()
        if not token:
            raise AuthenticationFailed('Invalid authorization header.')

        payload = decode_access_token(token)
        if payload is None:
            raise AuthenticationFailed('Invalid or expired access token.')

        try:
            user = User.objects.get(pk=payload['sub'])
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')

        if not user.is_active or user.is_banned:
            raise AuthenticationFailed('User account is disabled.')

        return user, token
