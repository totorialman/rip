from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.utils import timezone
from stocks.serializers import StockSerializer, FullStockSerializer, UserSerializer
from stocks.models import Stock, AuthUser
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from stocks.minio import add_url 
from stocks.minio import delete_file_from_minio
from rest_framework import viewsets
from datetime import datetime
from .models import Vmachine_Request, Vmachine_Service, Vmachine_Request_Service
from .serializers import VmachineRequestSerializer, VmachineRequestServiceSerializer, VmachineServiceSerializer

# ViewSet для работы с заявками
class VmachineRequestViewSet(viewsets.ModelViewSet):
    queryset = Vmachine_Request.objects.exclude(status='deleted')
    serializer_class = VmachineRequestSerializer


    def retrieve(self, request, pk=None):
        # Получаем объект заявки
        vmachine_request = get_object_or_404(Vmachine_Request, pk=pk)

        # Сериализуем заявку
        request_serializer = self.get_serializer(vmachine_request)

        # Получаем связанные услуги
        request_services = Vmachine_Request_Service.objects.filter(request=vmachine_request)
        print(request_services)
        # Сериализуем услуги
        services_serializer = VmachineRequestServiceSerializer(request_services, many=True)

        # Собираем данные для ответа
        response_data = {
            'request': request_serializer.data,  # Поля заявки
            'services': services_serializer.data  # Список услуг
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def get_queryset(self):
        # Исключаем заявки со статусами 'deleted' и 'draft'
        return Vmachine_Request.objects.exclude(status__in=['deleted', 'draft'])

    def list(self, request):
        queryset = self.get_queryset()  # Получаем отфильтрованный queryset
        serializer = self.get_serializer(queryset, many=True)  # Сериализуем данные
        return Response(serializer.data)  # Возвращаем сериализованные данные

    def retrieve1(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        default_user = AuthUser.objects.first()
        request_instance = serializer.save(
            creator=default_user,
            created_at=timezone.now(),
            status='draft'
        )

        url = self.request.FILES.get("url")
        if url:
            url_result = add_url(request_instance, url)
            if 'error' in url_result:  # Проверяем, есть ли ошибка
                return Response(url_result, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        instance = serializer.save()

        if 'url' in self.request.FILES:
            url = self.request.FILES['url']
            url_result = add_url(instance, url)
            if 'error' in url_result:  # Проверяем, есть ли ошибка
                return Response(url_result, status=status.HTTP_400_BAD_REQUEST)


    def get_queryset(self):
    # Возвращаем все заявки, исключая статусы 'deleted' и 'draft'
        queryset = Vmachine_Request.objects.exclude(status__in=['deleted', 'draft'])
        
        # Если нет заявок, возвращаем пустой queryset
        if not queryset.exists():
            return []  # Возвращаем пустой список, если заявок нет
        
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
        instance.moderator = AuthUser.objects.first()  # Фиктивный модератор
        instance.save()
        return Response({"status": "Request has been completed."})

    @action(detail=True, methods=['put'])
    def reject(self, request, pk=None):
        instance = self.get_object()
        instance.status = 'rejected'
        instance.moderator = AuthUser.objects.first()  # Фиктивный модератор
        instance.save()
        return Response({"status": "Request has been rejected."})

    @action(detail=True, methods=['delete'])
    def delete_request(self, request, pk=None):
        instance = self.get_object()
        instance.status = 'deleted'
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ViewSet для работы с услугами заявок
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


# API для регистрации пользователя
class UserRegistration(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"id": user.id, "username": user.username}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API для получения/редактирования услуги
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
        
        # Удаляем файл из MinIO, если URL файла существует
        if service.url:  # Предполагается, что поле url содержит ссылку на файл
            delete_file_from_minio(service.url)  # Удаляем файл из MinIO

        service.delete()  # Удаляем объект услуги
        return Response(status=status.HTTP_204_NO_CONTENT)
     # Добавьте метод upload_image
    def post(self, request, pk):
        service = get_object_or_404(Vmachine_Service, pk=pk)

        url_file = request.FILES.get("url")
        if url_file:
            url_result = add_url(service, url_file)  # Ваша функция загрузки в MinIO
            if isinstance(url_result, dict) and 'error' in url_result:
                return Response(url_result, status=status.HTTP_400_BAD_REQUEST)

            service.url = url_result
            service.save()
            return Response(VmachineServiceSerializer(service).data, status=status.HTTP_200_OK)

        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

# API для списка услуг
class VmachineServiceList(APIView):
    def get(self, request):
        # Получаем все активные услуги
        services = Vmachine_Service.objects.filter(status='active')

        # Проверяем, есть ли параметр 'vmachine_price' в запросе
        vmachine_price = request.query_params.get('vmachine_price', None)
        
        if vmachine_price:
            try:
                # Преобразуем параметр vmachine_price в число
                price_limit = float(vmachine_price)
                # Фильтруем услуги, цена которых меньше или равна переданной цене
                services = services.filter(price__lte=price_limit)
            except ValueError:
                # Если переданное значение не является числом, возвращаем ошибку
                return Response({"error": "Invalid price value"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VmachineServiceSerializer(services, many=True)

        
        first_draft_request = Vmachine_Request.objects.filter(status='draft').first()
        draft_request_id = first_draft_request.id if first_draft_request else None  # ID первого черновика или None

        response_data = {
            'services': serializer.data,
            'draft_request_id': draft_request_id  
        }
        return Response(response_data)



# API для профиля пользователя
class UserProfile(APIView):
    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Vmachine_Request, Vmachine_Request_Service, AuthUser
from .serializers import VmachineRequestSerializer, VmachineRequestServiceSerializer
from django.utils import timezone

@api_view(['GET', 'POST'])
def create_request(request):
    if request.method == 'GET':
        # Фильтрация по параметрам
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        status_filter = request.GET.get('status')

        queryset = Vmachine_Request.objects.all()

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        serializer = VmachineRequestSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Логика создания новой заявки
    request_data = request.data.copy()
    default_user = AuthUser.objects.all()[0]
    draft_request = Vmachine_Request.objects.filter(status='draft').first()

    if draft_request:
        service_id = request_data.get('service')
        quantity = request_data.get('quantity', 1)
        existing_service = Vmachine_Request_Service.objects.filter(request=draft_request, service_id=service_id).first()

        if existing_service:
            existing_service.quantity += quantity
            existing_service.save()
            return Response({"service": existing_service.id}, status=status.HTTP_200_OK)
        else:
            request_service_data = {
                'request': draft_request.id,
                'service': service_id,
                'quantity': quantity,
                'is_main': request_data.get('is_main', False)
            }
            service_serializer = VmachineRequestServiceSerializer(data=request_service_data)
            if service_serializer.is_valid():
                service_instance = service_serializer.save()
                return Response({"service": service_serializer.data}, status=status.HTTP_201_CREATED)
            return Response(service_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        request_data['creator'] = default_user
        request_data['created_at'] = timezone.now()
        request_data['status'] = 'draft'
        serializer = VmachineRequestSerializer(data=request_data)

        if serializer.is_valid():
            request_instance = serializer.save(creator=default_user)
            url = request.FILES.get("url")
            if url:
                url_result = add_url(request_instance, url)
                if isinstance(url_result, dict) and 'error' in url_result:
                    return Response(url_result, status=status.HTTP_400_BAD_REQUEST)
                request_instance.url = url_result
                request_instance.save()

            service_id = request_data.get('service')
            quantity = request_data.get('quantity', 1)
            request_service_data = {
                'request': request_instance.id,
                'service': service_id,
                'quantity': quantity,
                'is_main': request_data.get('is_main', False)
            }

            service_serializer = VmachineRequestServiceSerializer(data=request_service_data)
            if service_serializer.is_valid():
                service_serializer.save()
                return Response({"service": service_serializer.data}, status=status.HTTP_201_CREATED)
            return Response(service_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# API для создания услуги

@api_view(['POST'])
def create_service(request):
    request_data = request.data.copy()
    
    request_data['url'] = 'fff'
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



# API для добавления услуги к заявке
@api_view(['POST'])
def add_service_to_request(request, request_id):
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


# API для работы с акциями (Stock)
class StockList(APIView):
    def get(self, request):
        stocks = Stock.objects.all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StockSerializer(data=request.data)
        if serializer.is_valid():
            stock = serializer.save()

            url = request.FILES.get("url")
            if url:
                url_result = add_url(stock, url)
                if 'error' in url_result.data:
                    return Response(url_result.data, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StockDetail(APIView):
    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        serializer = StockSerializer(stock)
        return Response(serializer.data)

    def put(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        serializer = StockSerializer(stock, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


