from django.urls import path
from api.authentication.views import LoginView, UserProfileView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login_api'),
    path('profile/', UserProfileView.as_view(), name='profile_api'),
]
