from django.urls import path, include
from django.contrib import admin
from api.views import (
    HomeView, LoginView, DashboardView, LogoutView,
    AuthIndexView, CoreIndexView, AccountsIndexView, SCTIndexView,
    TransactionsIndexView, TransfersIndexView, CollectionIndexView
)

urlpatterns = [
    # Asegúrate de que solo haya un namespace 'admin'
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('app/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('app/api/auth/index.html', AuthIndexView.as_view(), name='auth_index'),
    path('app/core/index.html', CoreIndexView.as_view(), name='core_index'),
    path('app/accounts/index.html', AccountsIndexView.as_view(), name='accounts_index'),
    path('app/transactions/index.html', TransactionsIndexView.as_view(), name='transactions_index'),
    path('app/transfers/index.html', TransfersIndexView.as_view(), name='transfers_index'),
    path('app/collection/index.html', CollectionIndexView.as_view(), name='collection_index'),
    path('app/sct/index.html', SCTIndexView.as_view(), name='sct_index'),
]