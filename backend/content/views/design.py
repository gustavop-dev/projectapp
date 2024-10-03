from rest_framework.response import Response
from rest_framework import status
from content.models import Design
from content.serializers.design import DesignSerializer
from rest_framework.decorators import api_view

@api_view(['GET'])
def design_list(request):
    """
    API view to retrieve a list of Design entries.
    """
    designs = Design.objects.all()
    serializer = DesignSerializer(designs, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
