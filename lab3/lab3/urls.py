from django.contrib import admin
from stocks import views
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path(r'stocks/', views.StockList.as_view(), name='stocks-list'),
    path(r'stocks/<int:pk>/', views.StockDetail.as_view(), name='stocks-detail'),
    path(r'stocks/<int:pk>/', views.StockDetail.as_view(), name='stocks-detail'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path(r'users/', views.UsersList.as_view(), name='users-list'),
]