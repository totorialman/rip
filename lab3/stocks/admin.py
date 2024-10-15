from django.contrib import admin
from .models import Vmachine_Request, Vmachine_Service, Vmachine_Request_Service

admin.site.register(Vmachine_Service)
admin.site.register(Vmachine_Request)
admin.site.register(Vmachine_Request_Service)
# Register your models here.
