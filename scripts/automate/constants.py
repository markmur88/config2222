import logging
from send.utils import generate_uuid

# Generar un nuevo paymentId dinámicamente
paymentId = generate_uuid()  

logger = logging.getLogger(__name__)
logger.info(f"Nuevo paymentId generado: {paymentId}")