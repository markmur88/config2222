from django.urls import path
from api.core.views import IBANListView, IBANCreateView, IBANUpdateView, IBANDeleteView, DebtorListView, DebtorCreateView, DebtorUpdateView, DebtorDeleteView

urlpatterns = [
    
    path('ibans/', IBANListView.as_view(), name='iban-list'),
    path('ibans/create/', IBANCreateView.as_view(), name='iban-create'),
    path('ibans/<uuid:pk>/update/', IBANUpdateView.as_view(), name='iban-update'),
    path('ibans/<uuid:pk>/delete/', IBANDeleteView.as_view(), name='iban-delete'),
    
    path('debtors/', DebtorListView.as_view(), name='debtor-list'),
    path('debtors/create/', DebtorCreateView.as_view(), name='debtor-create'),
    path('debtors/<uuid:pk>/update/', DebtorUpdateView.as_view(), name='debtor-update'),
    path('debtors/<uuid:pk>/delete/', DebtorDeleteView.as_view(), name='debtor-delete'),
]
