"""
Endpoints del panel admin para gestionar pestañas de filtros guardados.

Estas pestañas antes vivían en `localStorage` del navegador y se perdían al
limpiar caché. Ahora se persisten por usuario en la tabla
`accounts_savedfiltertab`, accesibles desde cualquier dispositivo.

Misma autenticación del panel: sesión Django + CSRF (o JWT), permiso
`IsAdminUser` (Django `is_staff`).
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from accounts.models import SavedFilterTab
from accounts.serializers import SavedFilterTabSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def saved_filter_tabs_collection(request):
    """Listar (GET ?view=<view>) o crear (POST) pestañas del usuario actual."""
    if request.method == 'GET':
        qs = SavedFilterTab.objects.filter(user=request.user)
        view = request.query_params.get('view')
        if view:
            qs = qs.filter(view=view)
        serializer = SavedFilterTabSerializer(qs, many=True)
        return Response(serializer.data)

    serializer = SavedFilterTabSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def saved_filter_tab_detail(request, tab_id):
    """Actualizar (PATCH) o eliminar (DELETE) una pestaña del usuario actual."""
    tab = get_object_or_404(SavedFilterTab, id=tab_id, user=request.user)

    if request.method == 'DELETE':
        tab.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = SavedFilterTabSerializer(
        tab, data=request.data, partial=True, context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
