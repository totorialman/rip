from django.contrib import admin
from stocks import views
from stocks.views import UserRegistration
from stocks.views import (
    VmachineRequestViewSet,
    VmachineRequestServiceViewSet,
    UserRegistration,
    VmachineServiceList,
    create_request,
    create_service,
    add_service_to_request,
    VmachineServiceDetail,
)
from django.urls import include, path
from rest_framework import routers


router = routers.DefaultRouter()
router.register(
    r"vmachine-requests", VmachineRequestViewSet, basename="vmachine-request"
)
router.register(
    r"vmachine-request-services",
    VmachineRequestServiceViewSet,
    basename="vmachine-request-service",
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("register/", UserRegistration.as_view(), name="user-register"),
    path("register/<int:pk>/", UserRegistration.as_view(), name="user-update"),
    path("services/", VmachineServiceList.as_view(), name="service-list"),
    path("create-request/", create_request, name="create-request"),
    path("create-service/", create_service, name="create-service"),
    path("services/<int:pk>/", VmachineServiceDetail.as_view(), name="service-detail"),
    path(
        "services/<int:pk>/upload-image/",
        VmachineServiceDetail.as_view(),
        name="upload-image",
    ),
    path(
        "add-service-to-request/<int:request_id>/",
        add_service_to_request,
        name="add-service-to-request",
    ),
    path("", include(router.urls)),
    path(
        "requests/<int:pk>/",
        VmachineRequestViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "delete_request"}
        ),
        name="request-detail",
    ),
    path(
        "requests-formed/<int:pk>/",
        VmachineRequestViewSet.as_view(
            {
                "put": "update_status",
            }
        ),
        name="request-detail_2",
    ),
    path(
        "requests/<int:pk>/status/",
        VmachineRequestViewSet.as_view({"put": "update_status_moder"}),
        name="request-status-update",
    ),
    path(
        "requests/<int:pk>/remove-service/",
        VmachineRequestViewSet.as_view({"delete": "remove_service"}),
        name="remove-service",
    ),
    path(
        "requests/<int:pk>/update-service/",
        VmachineRequestViewSet.as_view({"put": "update_service_relation"}),
        name="update-service-relation",
    ),
]
