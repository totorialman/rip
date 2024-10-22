from django.contrib import admin
from stocks import views
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
)
from django.urls import include, path
from rest_framework import routers


router = routers.DefaultRouter()
router.register(
    r"vmachine-rent-list", VmachineRequestViewSet
)
router.register(
    r"vmachine-rent-vmachines",
    VmachineRequestServiceViewSet,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("register/", UserRegistration.as_view()),
    path("register/<int:pk>/", UserRegistration.as_view()),
    path("vmachines/", VmachineServiceList.as_view()),
    path("create-rent-vmachine/", create_rent_vmachine),
    path("create-vmachine/", create_vmachine),
    path("vmachines/<int:pk>/", VmachineServiceDetail.as_view()),
    path(
        "vmachines/<int:pk>/upload-image/",
        VmachineServiceDetail.as_view(),
    ),
    path(
        "add-vmachine-to-rent/<int:request_id>/",
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
        "rental-list/<int:pk>/remove-vmachine/",
        VmachineRequestViewSet.as_view({"delete": "remove_service"}),
    ),
    path(
        "rental-list/<int:pk>/update-vmachine/",
        VmachineRequestViewSet.as_view({"put": "update_service_relation"}),
    ),
]
