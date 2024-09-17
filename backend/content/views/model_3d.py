from rest_framework.response import Response
from rest_framework import status
from content.models import Model3D
from content.serializers.model_3d import Model3DSerializer
from rest_framework.decorators import api_view

@api_view(['GET'])
def model3d_list(request):
    """
    API view to retrieve a list of Model3D entries.
    """
    models = Model3D.objects.all()
    serializer = Model3DSerializer(models, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
