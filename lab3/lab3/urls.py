from django.contrib import admin
from stocks import views
from rest_framework import permissions
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from stocks.views import UserRegistration
from stocks.views import (
    VmachineRequestViewSet,
    VmachineRequestServiceViewSet,
    UserRegistration,
    VmachineServiceList,
    create_rent_vmachine,
    create_vmachine,
    add_vmachine_to_rent,
    VmachineServiceDetail,
    put_user,
    UserViewSet,
)
from django.urls import include, path
from rest_framework import routers

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()

router.register(
    r"rent-vmachines",
    VmachineRequestServiceViewSet,
)
router.register(r'user', views.UserViewSet, basename='user')
urlpatterns = [
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('login/',  views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("admin/", admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path("register/", UserRegistration.as_view()),
    path("register/<int:pk>/", put_user),
    path("vmachines/", VmachineServiceList.as_view()),
    path("create-rent/", create_rent_vmachine),
    path("vmachine/", create_vmachine),
    path("vmachines/<int:pk>/", VmachineServiceDetail.as_view()),
    path(
        "vmachines/<int:pk>/",
        VmachineServiceDetail.as_view(),
    ),
    path("rent-list/", VmachineRequestViewSet.as_view({"get": "get_list"})),
    path(
        "rent-list/<int:request_id>/",
        add_vmachine_to_rent,
    ),
    path("", include(router.urls)),
    path(
        "rental-list/<int:pk>/",
        VmachineRequestViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "delete_rent"}
        ),
    ),
    path(
        "rent-formed/<int:pk>/",
        VmachineRequestViewSet.as_view(
            {
                "put": "update_status",
            }
        ),
    ),
    path(
        "rental-list/<int:pk>/status/",
        VmachineRequestViewSet.as_view({"put": "update_status_moder"}),
    ),
    path(
        "rental-list/<int:pk>/",
        VmachineRequestViewSet.as_view({"delete": "remove_service"}),
    ),
    path(
        "rental-list/<int:pk>/update-vmachine/",
        VmachineRequestViewSet.as_view({"put": "update_service_relation"}),
    ),
]
