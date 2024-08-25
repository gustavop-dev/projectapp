from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Models3D, Designs, CategoriesDevelopment
from .serializers import ContactSerializer, Models3DSerializer, DesignsSerializer, CategoriesDevelopmentSerializer

@api_view(['POST'])
def create_contact(request):
    """
    Handle POST requests to create a new contact message.

    Args:
        request (HttpRequest): The HTTP request containing the contact data.

    Returns:
        Response: A JSON response with the created contact data and HTTP 201 status on success,
                  or the errors and HTTP 400 status if validation fails.
    """
    if request.method == 'POST':
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def get_models3d(request):
    """
    Handle GET requests to retrieve all 3D models.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        Response: A JSON response with all 3D models data and HTTP 200 status on success,
                  or an error message with HTTP 500 status if an exception occurs.
    """
    try:
        models = Models3D.objects.all()
        serializer = Models3DSerializer(models, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def get_designs(request):
    """
    Handle GET requests to retrieve all designs.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        Response: A JSON response with all designs data and HTTP 200 status on success.
    """
    designs = Designs.objects.all()
    serializer = DesignsSerializer(designs, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def get_categories_development(request):
    """
    Handle GET requests to retrieve all development categories.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        Response: A JSON response with all development categories data and HTTP 200 status on success.
    """
    categories = CategoriesDevelopment.objects.all()
    serializer = CategoriesDevelopmentSerializer(categories, many=True, context={'request': request})
    return Response(serializer.data)
