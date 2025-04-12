import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("django")

class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        logger.error(f"Error en {request.path}: {str(exception)}", exc_info=True)
        return None
