from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    """Generate JWT access + refresh tokens with custom claims."""
    refresh = RefreshToken.for_user(user)

    profile = getattr(user, 'profile', None)
    if profile:
        refresh['role'] = profile.role
        refresh['is_onboarded'] = profile.is_onboarded
        refresh['email'] = user.email

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def get_verification_token_for_user(user):
    """
    Generate a short-lived signed token used during the verification step.
    This is NOT a full access token — just proves the user passed step 1 (temp password).
    """
    refresh = RefreshToken.for_user(user)
    refresh['purpose'] = 'verification'
    refresh['email'] = user.email
    return str(refresh.access_token)
