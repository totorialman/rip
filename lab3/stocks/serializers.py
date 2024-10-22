from stocks.models import AuthUser
from rest_framework import serializers
from .models import Vmachine_Request, Vmachine_Service, Vmachine_Request_Service
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

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


class VmachineServiceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Vmachine_Service
        fields = ['id', 'name', 'price', 'description', 'description_tech', 'vcpu', 'ram', 'ssd', 'status','url']

class VmachineRequestServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vmachine_Request_Service
        fields = '__all__'



