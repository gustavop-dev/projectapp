from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.services.panel_dashboard_service import build_panel_dashboard


@api_view(['GET'])
@permission_classes([IsAdminUser])
def panel_dashboard(request):
    """Consolidated KPIs for the global panel dashboard.

    Finance data is superuser-only; other admins receive ``finance: null``
    and no finance-derived attention items.
    """
    return Response(
        build_panel_dashboard(include_finance=request.user.is_superuser)
    )
