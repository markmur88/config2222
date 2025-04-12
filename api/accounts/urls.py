from django.urls import path
from api.accounts.views import AccountListView, AccountCreateView, AccountUpdateView, AccountDeleteView, AccountListCreate, AccountDetail

urlpatterns = [
    path('api/', AccountListCreate.as_view(), name='account-list-create'),
    path('api/<int:pk>/', AccountDetail.as_view(), name='account-detail'),
    
    path('', AccountListView.as_view(), name='account_list'),
    path('create/', AccountCreateView.as_view(), name='account_create'),
    path('<uuid:pk>/update/', AccountUpdateView.as_view(), name='account_update'),
    path('<uuid:pk>/delete/', AccountDeleteView.as_view(), name='account_delete'),
] 