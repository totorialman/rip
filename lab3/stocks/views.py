from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.utils import timezone
from stocks.models import AuthUser, User
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from stocks.minio import add_url 
from stocks.minio import delete_file_from_minio
from rest_framework import viewsets
from datetime import datetime
from stocks.permissions import IsAdmin, IsManager
from .models import Vmachine_Request, Vmachine_Service, Vmachine_Request_Service, CustomUser
from .serializers import VmachineRequestSerializer, VmachineRequestServiceSerializer, VmachineServiceSerializer, UserSerializer
from django.utils import timezone
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from django.db import transaction
import redis
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes, authentication_classes
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
import uuid
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes



session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator



@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    username = request.data["username"] 
    password = request.data["password"]
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)

        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)

        

        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")

@swagger_auto_schema(method='delete', request_body=UserSerializer)
@api_view(["DELETE"])
@permission_classes([AllowAny])
@authentication_classes([])
def logout_view(request):
    session_id = request.COOKIES.get('session_id')
    
    # Удаляем запись из Redis, если session_id существует
    if session_id:
        session_storage.delete(session_id)

    # Удаляем сессию Django
    logout(request)
    
    # Удаляем куки sessionid
    response = Response({'status': 'Success'})
    response.delete_cookie('session_id')  # Удаляем куки session_id

    return response


class UserViewSet(viewsets.ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    
    def create(self, request):
        """
        Функция регистрации новых пользователей
        Если пользователя c указанным в request email ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(username=request.data['username']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(username=serializer.data['username'],
                                     password=serializer.data['password'],
                                     is_superuser=serializer.data['is_superuser'],
                                     is_staff=serializer.data['is_staff'])
            
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    


class VmachineRequestViewSet(viewsets.ModelViewSet):
    queryset = Vmachine_Request.objects.exclude(status='deleted')
    serializer_class = VmachineRequestSerializer

    @action(detail=True, methods=['delete'])
    def remove_service(self, request, pk=None):
        service_id = request.data.get('service_id')
        if not service_id:
            return Response({"error": "service_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        service_relation = get_object_or_404(Vmachine_Request_Service, request_id=pk, service_id=service_id)
        service_relation.delete()
        return Response({"detail": "Service has been removed from the request."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['put'])
    def update_service_relation(self, request, pk=None):
        service_id = request.data.get('service_id')
        quantity = request.data.get('quantity')
        order = request.data.get('order')
        if not service_id:
            return Response({"error": "service_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        service_relation = get_object_or_404(Vmachine_Request_Service, request_id=pk, service_id=service_id)
        if quantity is not None:
            service_relation.quantity = quantity
        if order is not None:
            service_relation.order = order
        
        service_relation.save()
        return Response({"detail": "Service relation has been updated.", "data": {
            "service_id": service_relation.service_id,
            "quantity": service_relation.quantity,
            "order": service_relation.order
        }}, status=status.HTTP_200_OK)

    def calculate_final_price(self, request_id):
        services = Vmachine_Request_Service.objects.filter(request_id=request_id)
        total_price = 0
        for service in services:
            total_price += service.service.price * service.quantity
        return total_price


    def update_status_moder(self, request, pk=None):
        instance = Vmachine_Request.objects.get(pk=pk)
        status_update = request.data.get('status')  
        if instance.status not in ['draft', 'formed']:
            return Response({"error": "Request is not in draft or formed status."}, status=status.HTTP_400_BAD_REQUEST)

        if status_update not in ['completed', 'rejected']:
            return Response({"status": ["Недопустимый статус. Используйте 'completed' или 'rejected'."]}, status=status.HTTP_400_BAD_REQUEST)

        moderator = request.user  # Текущий пользователь
        instance.moderator = moderator
        if status_update == 'completed':
            instance.completed_at = datetime.now()
            final_price = self.calculate_final_price(instance.id)
            instance.final_price = final_price

        instance.status = status_update
        instance.save()  
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['put'])
    def update_status(self, request, pk=None):
        instance = get_object_or_404(Vmachine_Request, pk=pk)
        if instance.status != 'draft':
            return Response({"error": "Request is not in draft status."}, status=status.HTTP_400_BAD_REQUEST)
        full_name = instance.full_name
        email = instance.email
        from_date = instance.from_date
        if not full_name or not email or not from_date:
            return Response({"error": "Full name, email, and from_date are required."}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = 'formed'
        instance.formed_at = timezone.now()
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)  
    
    def update(self, request, pk=None):
        instance = Vmachine_Request.objects.get(pk=pk)  
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    
    
    @permission_classes([IsAdmin]) 
    def get_list(self, request, pk=None):
        vmachine_requests = Vmachine_Request.objects.filter(creator=request.user)
        request_serializer = self.get_serializer(vmachine_requests, many=True)
        response_data = []
        for vmachine_request in vmachine_requests:
            request_services = Vmachine_Request_Service.objects.filter(request=vmachine_request)
            services_serializer = VmachineRequestServiceSerializer(request_services, many=True)
            response_data.append({
                'rent': request_serializer.data,  
                'vmachines': services_serializer.data  
            })
        
        return Response(response_data, status=status.HTTP_200_OK)

    def list(self, request):
        queryset = self.get_queryset()  
        serializer = self.get_serializer(queryset, many=True)  
        return Response(serializer.data)  


    def perform_create(self, serializer):
        default_user = AuthUser.objects.first().username
        request_instance = serializer.save(
            creator=default_user,
            created_at=timezone.now(),
            status='draft'
        )
        url = self.request.FILES.get("url")
        if url:
            url_result = add_url(request_instance, url)
            if 'error' in url_result:  
                return Response(url_result, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        instance = serializer.save()
        if 'url' in self.request.FILES:
            url = self.request.FILES['url']
            url_result = add_url(instance, url)
            if 'error' in url_result:  
                return Response(url_result, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = Vmachine_Request.objects.exclude(status__in=['deleted', 'draft'])
        

        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status_filter = self.request.GET.get('status')
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')  
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)  
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')  
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)  
            queryset = queryset.filter(created_at__lte=end_date)

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if not queryset.exists():
            return []  
        return queryset

    @action(detail=True, methods=['put'])
    def form(self, request, pk=None):
        instance = self.get_object()
        if not instance.full_name or not instance.email:
            return Response({"error": "Full name and email are required."}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = 'formed'
        instance.formed_at = timezone.now()
        instance.save()
        return Response({"status": "Request has been formed."})

    @action(detail=True, methods=['put'])
    def complete(self, request, pk=None):
        instance = self.get_object()
        instance.status = 'completed'
        instance.completed_at = timezone.now()
        instance.moderator = User.objects.first()  
        instance.save()
        return Response({"status": "Request has been completed."})

    @action(detail=True, methods=['put'])
    def reject(self, request, pk=None):
        instance = self.get_object()
        instance.status = 'rejected'
        instance.moderator = User.objects.first() 
        instance.save()
        return Response({"status": "Request has been rejected."})
    
    
    @action(detail=True, methods=['delete'])
    def delete_rent(self, request, pk=None):
        instance = get_object_or_404(Vmachine_Request, pk=pk)
        instance.status = 'deleted'
        instance.formed_at = timezone.now()
        instance.save()
        return Response({"detail": "Request has been deleted."}, status=status.HTTP_204_NO_CONTENT)

class VmachineRequestServiceViewSet(viewsets.ModelViewSet):
    queryset = Vmachine_Request_Service.objects.all()
    serializer_class = VmachineRequestServiceSerializer

    @action(detail=True, methods=['put'])
    def update_service(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def delete_service(self, request, pk=None):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserRegistration(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"id": user.id, "username": user.username}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    

@api_view(['PUT'])
def put_user(request, pk=None):
        try:
            user = User.objects.get(pk=pk)  
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user, data=request.data, partial=True)  
        if serializer.is_valid():
            serializer.save()  
            return Response({"id": user.id, "username": user.username}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class VmachineServiceDetail(APIView):

    
    def get(self, request, pk):
        service = get_object_or_404(Vmachine_Service, pk=pk)
        serializer = VmachineServiceSerializer(service)
        return Response(serializer.data)
    
    
    def put(self, request, pk):
        service = get_object_or_404(Vmachine_Service, pk=pk)
        serializer = VmachineServiceSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
   
    def delete(self, request, pk):
        service = get_object_or_404(Vmachine_Service, pk=pk)
        if service.url:  
            delete_file_from_minio(service.url)  
        service.delete()  
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @swagger_auto_schema(request_body=VmachineServiceSerializer)
    def post(self, request, pk):
        service = get_object_or_404(Vmachine_Service, pk=pk)
        url_file = request.FILES.get("url")
        if url_file:
            url_result = add_url(service, url_file)  
            if isinstance(url_result, dict) and 'error' in url_result:
                return Response(url_result, status=status.HTTP_400_BAD_REQUEST)

            service.url = url_result
            service.save()
            return Response(VmachineServiceSerializer(service).data, status=status.HTTP_200_OK)
        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

class VmachineServiceList(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    @method_permission_classes((IsAdmin,))
    def get(self, request):
        
        services = Vmachine_Service.objects.filter(status='active')
        vmachine_price = request.query_params.get('vmachine_price', None)
        if vmachine_price:
            try:
                price_limit = float(vmachine_price)
                services = services.filter(price__lte=price_limit)
            except ValueError:
                return Response({"error": "Invalid price value"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VmachineServiceSerializer(services, many=True)
        first_draft_request = Vmachine_Request.objects.filter(status='draft').first()
        rent_id = first_draft_request.id if first_draft_request else None 
        vmachine_count = Vmachine_Request_Service.objects.filter(request=first_draft_request).count()
        response_data = {
            'vmachines': serializer.data,
            'rent_id': rent_id,
            'vmachine_count': vmachine_count
        }
        return Response(response_data)

def clone_custom_users_to_auth_user():
    # Получаем всех пользователей из CustomUser
    custom_users = CustomUser.objects.all()
    User = get_user_model()
    for custom_user in custom_users:
        # Проверяем, существует ли пользователь с таким же username в auth_user
        if not User.objects.filter(username=custom_user.username).exists():
            # Создаем нового пользователя в auth_user
            User.objects.create_user(
                username=custom_user.username,
                password=custom_user.password,  # Или сгенерируйте временный пароль
                email='custom_user.email',
                is_staff=custom_user.is_staff,
                is_superuser=custom_user.is_superuser,
                # Добавьте другие поля, если нужно
            )
        else:
            print(f"Пользователь с именем {custom_user.username} уже существует в auth_user.")

@csrf_exempt
@swagger_auto_schema(method='post', request_body=VmachineRequestServiceSerializer)
@api_view(["POST"])
@permission_classes([IsAdmin])
def create_rent_vmachine(request):
    # Проверка, разрешен ли доступ
    request_data = request.data.copy()
    current_user = request.user

    # Проверка на существование текущего пользователя
    if not CustomUser.objects.filter(id=current_user.id).exists():
        return Response({'error': 'Creator user does not exist.'}, status=400)

    # Проверка наличия черновика заявки
    draft_request = Vmachine_Request.objects.filter(creator=current_user, status='draft').first()

    if draft_request:
        # Обработка существующей заявки
        service_id = request_data.get('service')
        quantity = request_data.get('quantity', 1)
        
        existing_service = Vmachine_Request_Service.objects.filter(request=draft_request, service_id=service_id).first()
        if existing_service:
            existing_service.quantity += quantity
            existing_service.save()
            return Response({
                "service": {
                    "id": existing_service.id,
                    "quantity": existing_service.quantity,
                    "is_main": existing_service.is_main,
                    "request": existing_service.request.id,
                    "service": existing_service.service.id
                }
            }, status=status.HTTP_200_OK)
        else:
            # Создание новой услуги в заявке
            request_service_data = {
                'request': draft_request.id,
                'service': service_id,
                'quantity': quantity,
                'is_main': request_data.get('is_main', False)
            }
            service_serializer = VmachineRequestServiceSerializer(data=request_service_data)
            if service_serializer.is_valid():
                service_instance = service_serializer.save()
                return Response({
                    "vmachine": service_serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response(service_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Создание новой заявки
        request_data['creator'] = current_user.id  # Убедитесь, что используете id текущего пользователя
        request_data['created_at'] = timezone.now()
        request_data['status'] = 'draft'

        serializer = VmachineRequestSerializer(data=request_data)
        if serializer.is_valid():
            request_instance = serializer.save(creator=current_user)
            url = request.FILES.get("url")
            if url:
                url_result = add_url(request_instance, url)
                if isinstance(url_result, dict) and 'error' in url_result:
                    return Response(url_result, status=status.HTTP_400_BAD_REQUEST)

                request_instance.url = url_result
                request_instance.save()

            # Обработка услуг в новой заявке
            service_id = request_data.get('service')
            quantity = request_data.get('quantity', 1)
            request_service_data = {
                'rent': request_instance.id,
                'vmachine': service_id,
                'quantity': quantity,
                'is_main': request_data.get('is_main', False)
            }

            service_serializer = VmachineRequestServiceSerializer(data=request_service_data)
            if service_serializer.is_valid():
                service_serializer.save()
                return Response({
                    "vmachine": service_serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response(service_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=VmachineServiceSerializer)
@api_view(['POST'])
def create_vmachine(request):
    request_data = request.data.copy()
    request_data['url'] = ' '
    serializer = VmachineServiceSerializer(data=request_data)
    if serializer.is_valid():
        stock = serializer.save()  
        url_file = request.FILES.get("url")  
        if url_file:
            url_result = add_url(stock, url_file)  
            if isinstance(url_result, dict) and 'error' in url_result:
                return Response(url_result, status=status.HTTP_400_BAD_REQUEST)
            stock.url = url_result  
            stock.save()
        return Response(VmachineServiceSerializer(stock).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=VmachineRequestServiceSerializer)
@api_view(['POST'])
def add_vmachine_to_rent(request, request_id):
    try:
        vmachine_request = Vmachine_Request.objects.get(id=request_id)
    except Vmachine_Request.DoesNotExist:
        return Response({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)
    service_id = request.data.get('service_id')
    quantity = request.data.get('quantity', 1)
    is_main = request.data.get('is_main', False)
    try:
        service = Vmachine_Service.objects.get(id=service_id)
    except Vmachine_Service.DoesNotExist:
        return Response({"error": "Service not found"}, status=status.HTTP_404_NOT_FOUND)

    request_service_data = {
        'request': vmachine_request.id,
        'service': service.id,
        'quantity': quantity,
        'is_main': is_main
    }
    
    serializer = VmachineRequestServiceSerializer(data=request_service_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


