from rest_framework.response import Response
from rest_framework import status
from content.models import UISectionCategory
from content.serializers.component import UISectionCategorySerializer
from rest_framework.decorators import api_view

@api_view(['GET'])
def uisectioncategory_list(request):
    """
    API view to retrieve a list of UISectionCategory.
    """
    categories = UISectionCategory.objects.all()
    serializer = UISectionCategorySerializer(categories, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
