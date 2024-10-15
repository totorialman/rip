from django.contrib import admin
from stocks import views
from stocks.views import UserRegistration
from stocks.views import (
    VmachineRequestViewSet,
    VmachineRequestServiceViewSet,
    UserRegistration,
    VmachineServiceList,
    UserProfile,
    create_request,
    create_service,
    add_service_to_request,
    StockList,
    StockDetail,
    VmachineServiceDetail,
)
from django.urls import include, path
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'vmachine-requests', VmachineRequestViewSet, basename='vmachine-request')
router.register(r'vmachine-request-services', VmachineRequestServiceViewSet, basename='vmachine-request-service')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', UserRegistration.as_view(), name='user-register'),
    path('services/', VmachineServiceList.as_view(), name='service-list'),

    path('profile/', UserProfile.as_view(), name='user-profile'),
    path('create-request/', create_request, name='create-request'),
    path('create-service/', create_service, name='create-service'),
    path('services/<int:pk>/', VmachineServiceDetail.as_view(), name='service-detail'),
    path('services/<int:pk>/upload-image/', VmachineServiceDetail.as_view(), name='upload-image'),
    path('add-service-to-request/<int:request_id>/', add_service_to_request, name='add-service-to-request'),
    
    # Используем маршруты из роутера
    path('', include(router.urls)),
    path('requests/<int:pk>/', VmachineRequestViewSet.as_view({'get': 'retrieve'}), name='request-detail'),

    
    # Маршруты для акций
    path('stocks/', StockList.as_view(), name='stock-list'),
    path('stocks/<int:pk>/', StockDetail.as_view(), name='stock-detail'),
    
]