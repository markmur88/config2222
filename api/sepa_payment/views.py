# apps/sepa_payment/views.py
import requests
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.paginator import Paginator
from api.sepa_payment.forms import SepaCreditTransferForm
from api.sepa_payment.models import SepaCreditTransfer
from api.sepa_payment.services import SepaPaymentService

def index(request):
    return render(request, 'partials/navGeneral/sepa_payment/index.html')

@require_http_methods(['GET', 'POST'])
def create_transfer(request):
    if request.method == 'POST':
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            try:
                # Crear la transferencia
                service = SepaPaymentService()
                payment_id = service.create_payment(form.cleaned_data)
                
                # Guardar en la base de datos
                transfer = form.save(commit=False)
                transfer.payment_id = payment_id
                transfer.save()
                
                messages.success(request, 'Transferencia creada exitosamente')
                return redirect('sepa_payment:list_transfers')  # Redirigir al listado
            except Exception as e:
                messages.error(request, f'Error al crear la transferencia: {str(e)}')
                return render(request, 'api/sepa_payment/transfer.html', {'form': form})
    else:
        form = SepaCreditTransferForm()
    
    return render(request, 'api/sepa_payment/transfer.html', {'form': form})

def list_transfers(request):
    transfers = SepaCreditTransfer.objects.all().order_by('-created_at')
    paginator = Paginator(transfers, 10)  # Paginación de 10 elementos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'api/sepa_payment/list_transfers.html', {'page_obj': page_obj})

def transfer_status(request, payment_id):
    try:
        transfer = SepaCreditTransfer.objects.get(payment_id=payment_id)
        service = SepaPaymentService()
        
        # Obtener el estado más reciente
        latest_status = transfer.status_history.latest('timestamp')
        
        # Obtener todos los estados para el historial
        status_history = transfer.status_history.all().order('-timestamp')
        
        return render(request, 'api/sepa_payment/status.html', {
            'transfer': transfer,
            'latest_status': latest_status,
            'status_history': status_history,
            'errors': transfer.errors.all()
        })
    except SepaCreditTransfer.DoesNotExist:
        messages.error(request, 'Transferencia no encontrada')
        return redirect('index_sepa_payment')