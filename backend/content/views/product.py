from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from content.models import Product
from content.serializers.product import ProductSerializer

@api_view(['GET'])
def product_list(request):
    """
    API view to retrieve a list of products.
    """
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)