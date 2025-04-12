# filepath: /home/markmur88/Documentos/GitHub/swiftapi3/api/core/middleware.py
from threading import local

_user = local()

class CurrentUserMiddleware:
    """
    Middleware para almacenar el usuario actual en una variable de contexto.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user if request.user.is_authenticated else None
        response = self.get_response(request)
        return response

    @staticmethod
    def get_current_user():
        return getattr(_user, 'value', None)