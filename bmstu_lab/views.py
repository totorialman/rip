from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from .models import Vmachine_Service,Vmachine_Request,Vmachine_Request_Service
from datetime import date 
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.db import connection
from django.db.models import F

def GetVmachines(request):
    max_price_str = request.GET.get('vmachine_max_price', '100000')

    try:
        max_price = int(max_price_str)
    except ValueError:
        max_price = 100000


    filtered_vmachines = Vmachine_Service.objects.filter(price__lte=max_price, status='active').order_by('id')

    current_request = Vmachine_Request.objects.filter(status='draft').first()

    vmachine_order_count = Vmachine_Request_Service.objects.filter(request=current_request).count() if current_request else 0

    if request.method == 'POST':
        current_request = add_service_to_request(request, current_request)
        return HttpResponseRedirect(request.path_info)

    context = {
        'vmachines': filtered_vmachines,
        'vmachines_max_price': max_price,
        'current_request': current_request,  
        'vmachine_order_count': vmachine_order_count,  # Количество услуг в черновике или 0
    }

    return render(request, 'vmachines.html', context)


def add_service_to_request(request, current_request): 
    service_id = request.POST.get('service_id')
    if service_id:
        try:
            service = Vmachine_Service.objects.get(id=service_id)

            if not current_request:
                current_request = Vmachine_Request.objects.create(status='draft')

            # Проверка, есть ли услуга уже в текущей заявке
            request_service, created = Vmachine_Request_Service.objects.get_or_create(
                request=current_request,
                service=service
            )

            if not created:
                # Увеличиваем количество напрямую через ORM
                Vmachine_Request_Service.objects.filter(id=request_service.id).update(quantity=F('quantity') + 1)

        except Vmachine_Service.DoesNotExist:
            pass 

    return current_request


def GetVmachine(request, id):
    vmachine = get_object_or_404(Vmachine_Service, id=id)

    # Получаем текущую корзину (заявку), если она есть
    current_request = Vmachine_Request.objects.filter(status='draft').first()

    
    vmachine_order_count = Vmachine_Request_Service.objects.filter(request=current_request).count() if current_request else 0

    context = {
        'vmachine': vmachine,
        'data': {
            'vmachine': {'id': id},
        },
        'current_request': current_request,
        'vmachine_order_count': vmachine_order_count,  
    }

    return render(request, 'vmachine.html', context)




def GetVmachineOrder(request, id):
    current_request = Vmachine_Request.objects.filter(id=id).first()
    if not current_request:
        return HttpResponseRedirect('/')
    
    allowed_statuses = ['draft', 'formed', 'completed']
    if current_request.status not in allowed_statuses:
        return HttpResponseRedirect('/')

    request_services = Vmachine_Request_Service.objects.filter(request=current_request)

    if not request_services.exists():
        return HttpResponse(status=204)

    items = []
    total_price = 0

    for request_service in request_services:
        vmachine = request_service.service  # Получаем услугу из заявки
        total = vmachine.price * request_service.quantity

        vmachine_info = {
            'id': vmachine.id,
            'name': vmachine.name,
            'price': vmachine.price,
            'quantity': request_service.quantity,
            'total': total,
            'url': vmachine.url,
        }
        items.append(vmachine_info)
        total_price += total

    
    context = {
        'items': items,
        'total_price': total_price,
        'current_request': current_request,
        'full_name': current_request.full_name,
        'email': current_request.email,
        'from_date': current_request.from_date,
    }

    return render(request, 'vmachine-order.html', context)



def delete_request(request):
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id
            FROM vmachine_request
            WHERE status = 'draft'
            ORDER BY created_at
            LIMIT 1
        """)
        row = cursor.fetchone()

    if row:
        request_id = row[0]

        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE vmachine_request
                SET status = 'deleted'
                WHERE id = %s
            """, [request_id])

    return HttpResponseRedirect('http://localhost:8000/')