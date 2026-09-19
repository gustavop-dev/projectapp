from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .authentication import IngestAuthentication
from .models import Case, CaseActivity, Report, Resource, Source
from .serializers import (
    ActivitySerializer, CaseSerializer, DeliverySerializer, FilterSerializer,
    IngestSerializer, NoteSerializer, ReportSerializer, ResourceSerializer,
    SourceSerializer, StateSerializer,
)
from .services import change_state, ingest


def admin_api(methods):
    def decorate(view):
        return api_view(methods)(authentication_classes([SessionAuthentication])(permission_classes([IsAdminUser])(view)))
    return decorate


def validated(serializer_class, data):
    serializer = serializer_class(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def paginated(queryset, serializer_class, page):
    size = 25
    total = queryset.count()
    return {'results': serializer_class(queryset[(page - 1) * size:page * size], many=True).data, 'count': total, 'page': page, 'page_size': size}


@api_view(['POST'])
@authentication_classes([IngestAuthentication])
@permission_classes([AllowAny])
def receive(request):
    if len(request.body) > 128 * 1024:
        return Response({'detail': 'Registro demasiado extenso.'}, status=413)
    receipt, created = ingest(request.auth, validated(IngestSerializer, request.data))
    return Response({'id': receipt.pk, 'case_id': receipt.case_id, 'report_id': receipt.report_id, 'duplicate': not created}, status=201 if created else 200)


@admin_api(['GET'])
def catalog(request):
    return Response({'resources': ResourceSerializer(Resource.objects.all(), many=True).data, 'sources': SourceSerializer(Source.objects.select_related('resource'), many=True).data})


def filtered(request, model):
    data = validated(FilterSerializer, request.query_params)
    query = model.objects.select_related('source__resource__server')
    for parameter, field in [('resource', 'source__resource_id'), ('source', 'source_id'), ('kind', 'source__resource__kind')]:
        if parameter in data:
            query = query.filter(**{field: data[parameter]})
    if model is Case:
        for parameter in ['state', 'severity']:
            if parameter in data:
                query = query.filter(**{parameter: data[parameter]})
    if data.get('search'):
        query = query.filter(title__icontains=data['search'])
    date_field = 'last_seen_at' if model is Case else 'observed_at'
    for parameter, lookup in [('since', 'gte'), ('until', 'lte')]:
        if parameter in data:
            query = query.filter(**{f'{date_field}__date__{lookup}': data[parameter]})
    return query, data['page']


@admin_api(['GET'])
def cases(request):
    query, page = filtered(request, Case)
    return Response(paginated(query, CaseSerializer, page))


@admin_api(['GET'])
def case_detail(request, pk):
    case = get_object_or_404(Case.objects.select_related('source__resource__server'), pk=pk)
    page = validated(FilterSerializer, request.query_params)['page']
    return Response({**CaseSerializer(case).data, 'evidence': case.evidence, 'activities': paginated(case.activities.all(), ActivitySerializer, page), 'deliveries': paginated(case.deliveries.all(), DeliverySerializer, page)})


@admin_api(['POST'])
def case_state(request, pk):
    case = change_state(pk, request.user, validated(StateSerializer, request.data))
    return Response(CaseSerializer(case).data)


@admin_api(['POST'])
def case_note(request, pk):
    case = get_object_or_404(Case, pk=pk)
    data = validated(NoteSerializer, request.data)
    activity = CaseActivity.objects.create(case=case, actor=request.user, actor_name=request.user.get_username(), kind='note', text=data['text'])
    return Response(ActivitySerializer(activity).data, status=201)


@admin_api(['GET'])
def reports(request):
    query, page = filtered(request, Report)
    return Response(paginated(query, ReportSerializer, page))


@admin_api(['GET'])
def report_detail(request, pk):
    report = get_object_or_404(Report.objects.select_related('source__resource__server'), pk=pk)
    return Response({**ReportSerializer(report).data, 'text': report.text})


@admin_api(['PATCH'])
def resource_link(request, pk):
    from accounts.models import Project
    from rest_framework import serializers

    class LinkSerializer(serializers.Serializer):
        project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), allow_null=True)

    resource = get_object_or_404(Resource, pk=pk, kind='project')
    data = validated(LinkSerializer, request.data)
    project = data['project']
    if project and Resource.objects.filter(project=project).exclude(pk=pk).exists():
        return Response({'detail': 'El proyecto ya está vinculado a otro recurso.'}, status=409)
    resource.project = project
    resource.save(update_fields=['project'])
    return Response(ResourceSerializer(resource).data)
