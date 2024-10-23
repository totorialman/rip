from stocks.models import AuthUser
from rest_framework import serializers
from .models import Vmachine_Request, Vmachine_Service, Vmachine_Request_Service, CustomUser
from django.contrib.auth.models import User
from collections import OrderedDict


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'is_staff', 'is_superuser']


class VmachineRequestSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source='creator.username',read_only=True)  
    moderator = serializers.CharField(source='moderator.username',read_only=True)
    
    class Meta:
        model = Vmachine_Request
        fields = [
            'id',             
            'status',
            'created_at',
            'formed_at',
            'completed_at',
            'creator',
            'moderator',
            'full_name',
            'email',
            'from_date',
            'final_price',
        ]
        read_only_fields = ['created_at', 'creator', 'moderator']
    def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields


class VmachineServiceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Vmachine_Service
        fields = ['id', 'name', 'price', 'description', 'description_tech', 'vcpu', 'ram', 'ssd', 'status','url']
    def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields

class VmachineRequestServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vmachine_Request_Service
        fields = '__all__'
    def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields



