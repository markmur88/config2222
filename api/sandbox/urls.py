from django.urls import path
from api.sandbox.views import (
    BankConnectionTest, IncomingCollectionView, AccountBalanceView, SepaTransferView,
    IncomingCollectionListView, IncomingCollectionCreateView
)

urlpatterns = [
    path("test-banks/", BankConnectionTest.as_view(), name="test-banks"),
    path("incoming_collections/", IncomingCollectionView.as_view(), name="incoming-collections"),
    path("accounts/<str:account_id>/balance/", AccountBalanceView.as_view(), name="sandbox-balance"),
    path("sepa/transfer/", SepaTransferView.as_view(), name="sandbox-sepa-transfer"),

]
