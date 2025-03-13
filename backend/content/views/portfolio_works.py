from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from content.models import PortfolioWork
from content.serializers import PortfolioWorkSerializer

@api_view(['GET'])
def portfolio_works_list(request):
    """
    List all portfolio works or create a new portfolio work.
    """
    portfolio_works = PortfolioWork.objects.all()
    serializer = PortfolioWorkSerializer(portfolio_works, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
    