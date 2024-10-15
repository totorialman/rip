from stocks.models import Stock
from stocks.models import AuthUser
from rest_framework import serializers
from .models import Vmachine_Request, Vmachine_Service, Vmachine_Request_Service
from django.contrib.auth.models import User


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ["pk", "company_name", "price", "is_growing", "date_modified", "url"]


class FullStockSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Stock
        fields = ["pk", "company_name", "price", "is_growing", "date_modified", "url", "user"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class VmachineRequestSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)  # Показываем только для чтения
    moderator = UserSerializer(read_only=True)

    class Meta:
        model = Vmachine_Request
        fields = ['id', 'creator', 'created_at', 'status', 'moderator']
        read_only_fields = ['created_at', 'creator', 'moderator']


class VmachineServiceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Vmachine_Service
        fields = ['id', 'name', 'price', 'description', 'description_tech', 'vcpu', 'ram', 'ssd', 'status','url']


class VmachineRequestServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vmachine_Request_Service
        fields = '__all__'


class UserDetailSerializer(serializers.ModelSerializer):
    stock_set = StockSerializer(many=True, read_only=True)

    class Meta:
        model = AuthUser
        fields = ["id", "first_name", "last_name", "stock_set"]
