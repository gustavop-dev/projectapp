# myapp/views.py
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Models3D, Designs, CategoriesDevelopment
from .serializers import ContactSerializer, Models3DSerializer, DesignsSerializer, CategoriesDevelopmentSerializer

@api_view(['POST'])
def create_contact(request):
    if request.method == 'POST':
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_models3d(request):
    try:
        models = Models3D.objects.all()
        serializer = Models3DSerializer(models, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def get_designs(request):
    designs = Designs.objects.all()
    serializer = DesignsSerializer(designs, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def get_categories_development(request):
    categories = CategoriesDevelopment.objects.all()
    serializer = CategoriesDevelopmentSerializer(categories, many=True, context={'request': request})
    return Response(serializer.data)