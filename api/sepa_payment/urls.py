# apps/sepa_payment/urls.py
from django.urls import path
from api.sepa_payment import views

app_name = 'sepa_payment'

urlpatterns = [
    path('', views.index, name='index_sepa_payment'),
    path('transfer/', views.create_transfer, name='create_transfer'),
    path('transfer/<str:payment_id>/status/', views.transfer_status, name='transfer_status'),
    path('transfers/', views.list_transfers, name='list_transfers'),
]