from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from content.services.financing_pdf_service import FinancingPdfService
from content.services.financing_program_service import serialize_financing_program


def _language_from_query(request):
    language = request.query_params.get('lang', 'es')
    return language if language in ('es', 'en') else None


def _invalid_language_response():
    return Response(
        {'lang': ['Usa es o en.']},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def public_financing_program(request):
    language = _language_from_query(request)
    if language is None:
        return _invalid_language_response()
    return Response(serialize_financing_program(language=language))


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def public_financing_program_pdf(request):
    language = _language_from_query(request)
    if language is None:
        return _invalid_language_response()

    pdf_bytes = FinancingPdfService.build(language=language)
    filename = (
        'software-financing-program.pdf'
        if language == 'en'
        else 'programa-financiacion-software.pdf'
    )
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Cache-Control'] = 'private, no-store'
    return response
