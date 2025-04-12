from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status
from api.authentication.serializers import JWTTokenSerializer
from django.urls import reverse

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Si deseas mantener la autenticación basada en sesiones
            login(request, user)
            
            # Lógica adicional para generar tokens JWT
            tokens = JWTTokenSerializer.get_tokens_for_user(user)
            #return Response(tokens, status=status.HTTP_200_OK)
            return redirect('dashboard')

        return render(request, 'login.html', {'error': 'Credenciales inválidas'})
    

@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        return render(request, 'dashboard.html')

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('home')

@method_decorator(login_required, name='dispatch')
class AuthIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/auth/index.html')

@method_decorator(login_required, name='dispatch')
class CoreIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/core/index.html')

@method_decorator(login_required, name='dispatch')
class AccountsIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/accounts/index.html')

@method_decorator(login_required, name='dispatch')
class TransactionsIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/transactions/index.html')

@method_decorator(login_required, name='dispatch')
class TransfersIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/transfers/index.html')

@method_decorator(login_required, name='dispatch')
class CollectionIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/collection/index.html')

@method_decorator(login_required, name='dispatch')
class SCTIndexView(View):
    def get(self, request):
        return render(request, 'partials/navGeneral/sct/index.html')