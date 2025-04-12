from django.urls import path
from api.collection.views import (
    MandateListView, MandateCreateView, MandateUpdateView, MandateDeleteView,
    CollectionListView, CollectionCreateView, CollectionUpdateView, CollectionDeleteView,
)

urlpatterns = [
    # Rutas para Mandates
    path('mandates/', MandateListView.as_view(), name='mandate-list'),
    path('mandates/create/', MandateCreateView.as_view(), name='mandate-create'),
    path('mandates/<pk>/update/', MandateUpdateView.as_view(), name='mandate-update'),
    path('mandates/<pk>/delete/', MandateDeleteView.as_view(), name='mandate-delete'),

    # Rutas para Collections
    path('collections/', CollectionListView.as_view(), name='collection-list'),
    path('collections/create/', CollectionCreateView.as_view(), name='collection-create'),
    path('collections/<pk>/update/', CollectionUpdateView.as_view(), name='collection-update'),
    path('collections/<pk>/delete/', CollectionDeleteView.as_view(), name='collection-delete'),
]