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
from accounts.services import saved_filter_tab_service


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def saved_filter_tabs_collection(request):
    """Listar (GET ?view=<view>) o crear (POST) pestañas del usuario actual.

    En GET con ``view``, si el usuario aún no tiene pestañas para esa vista
    se siembran los defaults del registry (``accounts.default_filter_tabs``).
    Borrar todas las pestañas de una vista equivale a "restaurar defaults".
    """
    if request.method == 'GET':
        view = request.query_params.get('view')
        if view:
            saved_filter_tab_service.seed_default_tabs(request.user, view)
        qs = SavedFilterTab.objects.filter(user=request.user)
        if view:
            qs = qs.filter(view=view)
        serializer = SavedFilterTabSerializer(qs, many=True)
        return Response(serializer.data)

    serializer = SavedFilterTabSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def saved_filter_tabs_reset(request):
    """Restaurar los defaults de una vista: borra las pestañas del usuario
    para ``view`` y vuelve a sembrar el registry. Devuelve la lista fresca
    (vacía si la vista no tiene defaults en el registry)."""
    view = request.data.get('view')
    valid_views = {choice for choice, _label in SavedFilterTab.VIEW_CHOICES}
    if view not in valid_views:
        return Response(
            {'view': 'Vista no válida.'}, status=status.HTTP_400_BAD_REQUEST,
        )
    SavedFilterTab.objects.filter(user=request.user, view=view).delete()
    saved_filter_tab_service.seed_default_tabs(request.user, view)
    qs = SavedFilterTab.objects.filter(user=request.user, view=view)
    return Response(SavedFilterTabSerializer(qs, many=True).data)


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
