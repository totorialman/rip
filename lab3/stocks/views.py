from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from stocks.serializers import StockSerializer
from stocks.serializers import FullStockSerializer
from stocks.models import Stock
from stocks.models import AuthUser
# Правильный импорт
from stocks.serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from stocks.minio import add_pic 

def user():
    try:
        user1 = AuthUser.objects.get(id=1)
    except:
        user1 = AuthUser(id=1, first_name="Иван", last_name="Иванов", password=1234, username="user1")
        user1.save()
    return user1

class StockList(APIView):
    model_class = Stock
    serializer_class = StockSerializer

    def get(self, request, format=None):
        stocks = self.model_class.objects.all()
        serializer = self.serializer_class(stocks, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            stock=serializer.save()
            user1 = user()
            # Назначаем создателем акции польователя user1
            stock.user = user1
            stock.save()
            pic = request.FILES.get("pic")
            pic_result = add_pic(stock, pic)
            if 'error' in pic_result.data:    
                return pic_result
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StockDetail(APIView):
    model_class = Stock
    serializer_class = FullStockSerializer

    def get(self, request, pk, format=None):
        stock = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(stock)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        stock = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(stock, data=request.data, partial=True)
        if 'pic' in serializer.initial_data:
            pic_result = add_pic(stock, serializer.initial_data['pic'])
            if 'error' in pic_result.data:
                return pic_result
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        stock = get_object_or_404(self.model_class, pk=pk)
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['Put'])
def put_detail(request, pk, format=None):
    stock = get_object_or_404(self.model_class, pk=pk)
    serializer = self.serializer_class(stock, data=request.data, partial=True)
    if 'pic' in serializer.initial_data:
        pic_result = add_pic(stock, serializer.initial_data['pic'])
        if 'error' in pic_result.data:
            return pic_result
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UsersList(APIView):
    model_class = AuthUser
    serializer_class = UserSerializer

    def get(self, request, format=None):
        user = self.model_class.objects.all()
        serializer = self.serializer_class(user, many=True)
        return Response(serializer.data)