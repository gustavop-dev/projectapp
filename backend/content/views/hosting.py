from rest_framework.response import Response
from rest_framework import status
from content.models import Hosting
from content.serializers import HostingSerializer
from rest_framework.decorators import api_view

@api_view(['GET'])
def hosting_list(request):
    """
    API view to retrieve a list of Hosting entries.
    """
    hostings = Hosting.objects.all()
    serializer = HostingSerializer(hostings, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
