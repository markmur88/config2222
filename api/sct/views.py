from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.sct.models import (
    SepaCreditTransferRequest, SepaCreditTransferResponse, 
    SepaCreditTransferDetailsResponse, SepaCreditTransferUpdateScaRequest
)
from api.sct.serializers import (
    SepaCreditTransferRequestSerializer, SepaCreditTransferResponseSerializer, 
    SepaCreditTransferDetailsResponseSerializer, SepaCreditTransferUpdateScaRequestSerializer
)
from django.conf import settings
import os
import logging
from rest_framework.exceptions import APIException
from api.sct.services import deutsche_bank_transfer, process_bank_transfer, process_bank_transfer11
from api.sct.generate_xml import generate_sepa_xml
from api.sct.generate_pdf import generar_pdf_transferencia
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from api.sct.forms import SepaCreditTransferRequestForm
from uuid import uuid4
from datetime import date
from django.http import FileResponse, HttpResponseNotFound

logger = logging.getLogger("bank_services")
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = "idempotency_key"
ERROR_KEY = "error"


class SepaCreditTransferCreateView(APIView):
    model = SepaCreditTransferRequest
    fields = '__all__'
    
    def get(self, request):
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            transfer = serializer.save(transaction_status="PDNG")
            response_data = {
                "transaction_status": transfer.transaction_status,
                "payment_id": str(transfer.payment_id),  # Ensure UUID is serialized as string
                "auth_id": str(transfer.auth_id),        # Ensure UUID is serialized as string
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SepaCreditTransferCreateView2(APIView):
    model = SepaCreditTransferRequest
    fields = '__all__'
    
    def get(self, request):
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            transfer = serializer.save(transaction_status="PDNG")
            sepa_xml = generate_sepa_xml(transfer)
            media_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.payment_id}.xml")
            
            with open(media_path, "w") as xml_file:
                xml_file.write(sepa_xml)

            response_data = {
                "transaction_status": "PDNG",
                "payment_id": transfer.payment_id,
                "sepa_xml": sepa_xml
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SepaCreditTransferDetailsView(APIView):
    """
    View para obtener los detalles de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferDetailsResponse.objects.get(payment_id=payment_id)
            serializer = SepaCreditTransferDetailsResponseSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferDetailsResponse.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class SepaCreditTransferStatusView(APIView):
    """
    View para obtener el estado de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferResponse.objects.get(payment_id=payment_id)
            serializer = SepaCreditTransferResponseSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferResponse.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class SepaCreditTransferCancelView(APIView):
    """
    View para cancelar una transferencia SEPA.
    """
    def delete(self, request, payment_id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=payment_id)
            transfer.delete()
            return Response({"message": "Transfer cancelled successfully"}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class SepaCreditTransferUpdateScaView(APIView):
    """
    View para actualizar el segundo factor de autenticación (SCA) de una transferencia SEPA.
    """
    def patch(self, request, payment_id):
        try:
            transfer = SepaCreditTransferUpdateScaRequest.objects.get(id=payment_id)
            serializer = SepaCreditTransferUpdateScaRequestSerializer(transfer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "SCA updated successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SepaCreditTransferUpdateScaRequest.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class SepaCreditTransferListView(APIView):
    """
    View para listar todas las transferencias SEPA.
    """
    def get(self, request):
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SepaCreditTransferDownloadXmlView(APIView):
    """
    View para generar y descargar el archivo XML de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=payment_id)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.id}.xml")

            # Generar el archivo XML si no existe
            if not os.path.exists(xml_path):
                sepa_xml = generate_sepa_xml(transfer)
                with open(xml_path, "w") as xml_file:
                    xml_file.write(sepa_xml)

            # Descargar el archivo XML
            if os.path.exists(xml_path):
                return FileResponse(open(xml_path, "rb"), content_type="application/xml", as_attachment=True, filename=f"sepa_{transfer.id}.xml")
            
            return HttpResponseNotFound("Archivo XML no encontrado.")
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transferencia con ID {payment_id} no encontrada.")
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al generar/descargar el archivo XML: {str(e)}", exc_info=True)
            return Response({"error": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SepaCreditTransferDownloadPdfView(APIView):
    """
    View para descargar el archivo PDF de una transferencia SEPA.
    """
    def get(self, request, payment_id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=payment_id)
            pdf_path = os.path.join(settings.MEDIA_ROOT, f"transferencia_{transfer.id}.pdf")
            if not os.path.exists(pdf_path):
                return Response({"error": "PDF file not found"}, status=status.HTTP_404_NOT_FOUND)

            with open(pdf_path, "rb") as pdf_file:
                pdf_content = pdf_file.read()
            return Response({"pdf_content": pdf_content}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)


class SCTList55View(CreateView, ListView):
    model = SepaCreditTransferRequest
    form_class = SepaCreditTransferRequestForm
    template_name = "api/SCT/sct_list5.html"
    success_url = reverse_lazy('sct_list5')

    def get_initial(self):
        """
        Genera valores iniciales para los campos idempotency_key, payment_id,
        payment_identification_end_to_end_id y requested_execution_date.
        """
        initial = super().get_initial()
        initial['idempotency_key'] = uuid4()
        initial['payment_id'] = uuid4()
        initial['auth_id'] = uuid4()
        initial['payment_identification_end_to_end_id'] = uuid4()
        initial['requested_execution_date'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transfers'] = SepaCreditTransferRequest.objects.all()
        return context

    def form_valid(self, form):
        # Guardar la transferencia
        transfer = form.save()

        # # Procesar la transferencia
        process_view = ProcessTransferView11()
        process_view.post(self.request, idempotency_key=transfer.idempotency_key)

        return super().form_valid(form)


class SCTList5View(CreateView, ListView):
    model = SepaCreditTransferRequest
    form_class = SepaCreditTransferRequestForm
    template_name = "api/SCT/sct_list5.html"
    success_url = reverse_lazy('sct_list5')

    def get_initial(self):
        initial = super().get_initial()
        initial['idempotency_key'] = uuid4()
        initial['payment_id'] = uuid4()
        initial['auth_id'] = uuid4()
        initial['payment_identification_end_to_end_id'] = uuid4()
        initial['requested_execution_date'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transfers'] = SepaCreditTransferRequest.objects.all()
        return context

    def form_valid(self, form):
        # Guardar la transferencia
        transfer = form.save()

        # Procesar la transferencia
        process_view = ProcessTransferView12()
        response = process_view.post(self.request, idempotency_key=transfer.idempotency_key)

        # Verificar si hubo un error
        if response.status_code != 200:
            form.add_error(None, "Error al procesar la transferencia.")
            return self.form_invalid(form)

        return super().form_valid(form)
    
    
class DownloadXmlView(APIView):
    """
    View para descargar el archivo XML de una transferencia SEPA.
    """
    def get(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            xml_filename = f"sepa_{transfer.idempotency_key}.xml"
            xml_path = os.path.join(settings.MEDIA_ROOT, xml_filename)

            # Generar el archivo XML si no existe
            if not os.path.exists(xml_path):
                try:
                    xml_path = generate_sepa_xml(transfer)
                except Exception as e:
                    logger.error(f"Error al generar el archivo XML: {str(e)}", exc_info=True)
                    return Response({"error": "Error al generar el archivo XML."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Descargar el archivo XML
            if os.path.exists(xml_path):
                return FileResponse(open(xml_path, "rb"), content_type="application/xml", as_attachment=True, filename=xml_filename)
            
            return HttpResponseNotFound("Archivo XML no encontrado.")
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transferencia con ID {idempotency_key} no encontrada.")
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error inesperado al procesar la solicitud: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la solicitud."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DownloadPdfView(APIView):
    """
    View para descargar el archivo PDF de una transferencia SEPA.
    """
    def get(self, request, id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=id)
            pdf_path = os.path.join(settings.MEDIA_ROOT, f"transferencia_{transfer.id}.pdf")

            # Generar el archivo PDF si no existe
            if not os.path.exists(pdf_path):
                pdf_path = generar_pdf_transferencia(transfer)

            # Descargar el archivo PDF
            if os.path.exists(pdf_path):
                return FileResponse(open(pdf_path, "rb"), content_type="application/pdf", as_attachment=True, filename=f"transferencia_{transfer.id}.pdf")
            
            return HttpResponseNotFound("Archivo PDF no encontrado.")
        except SepaCreditTransferRequest.DoesNotExist:
            return HttpResponseNotFound("Transferencia no encontrada.")
        except Exception as e:
            logger.error(f"Error al generar/descargar el archivo PDF: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la solicitud."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelTransferView(APIView):
    """
    View para cancelar una transferencia SEPA.
    """
    def post(self, request, id):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=id)
            transfer.delete()
            return Response({"message": "Transferencia cancelada exitosamente."}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)





class ProcessTransferView1(APIView):
    def get(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            idempotency_key = transfer.idempotency_key
            bank_response = process_bank_transfer(idempotency_key, transfer)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            transfer.transaction_status = "ACCP"
            transfer.save()
            return Response({"message": "Transferencia procesada exitosamente.", "bank_response": bank_response}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView11(APIView):
    def get(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            idempotency_key = transfer.idempotency_key
            bank_response = process_bank_transfer(idempotency_key, transfer)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            transfer.transaction_status = "ACCP"
            transfer.save()
            # Generar el archivo XML
            sepa_xml = generate_sepa_xml(transfer)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)

            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response": bank_response,
                "xml_path": xml_path
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView2(APIView):
    def get(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            idempotency_key = transfer.idempotency_key
            bank_response = process_bank_transfer(idempotency_key, transfer)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            transfer.transaction_status = "ACCP"
            transfer.save()
            sepa_xml = generate_sepa_xml(transfer)
            if not os.path.exists(sepa_xml):
                return Response({"error": "No se pudo generar el archivo XML."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            with open(sepa_xml, "r", encoding="utf-8") as xml_file:
                xml_content = xml_file.read()
            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response": bank_response,
                "xml_content": xml_content
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView3(APIView):
    def get(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, idempotency_key):
        idempotency_key = request.data.get("idempotency_key")
        if not idempotency_key:
            serializer = SepaCreditTransferRequestSerializer(data=request.data)
            if serializer.is_valid():
                transfer = serializer.save(transaction_status="PDNG")
                idempotency_key = transfer.idempotency_key
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            bank_response = process_bank_transfer(idempotency_key, transfer)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            transfer.transaction_status = "ACCP"
            transfer.save()
            sepa_xml = generate_sepa_xml(transfer)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)
            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response": bank_response,
                "xml_path": xml_path
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView4(APIView):
    def get(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key=None):
        # Obtener idempotency_key desde los datos o el argumento
        if not idempotency_key:
            idempotency_key = request.data.get("idempotency_key")
        
        if not idempotency_key:
            serializer = SepaCreditTransferRequestSerializer(data=request.data)
            if serializer.is_valid():
                #transfer = serializer.save(transaction_status="PDNG")
                transfer = serializer.save(transaction_status="ACCP")
                idempotency_key = transfer.idempotency_key
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            bank_response = process_bank_transfer(transfer, idempotency_key)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
            transfer.transaction_status = "ACCP"
            transfer.save()

            # Generar el archivo XML
            sepa_xml = generate_sepa_xml(transfer)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)

            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response": bank_response,
                "xml_path": xml_path
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView12(APIView):
    def get(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key):
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)

            # Procesar con process_bank_transfer
            bank_response_1 = process_bank_transfer(idempotency_key, transfer)

            # Verificar si hubo un error en el primer procesamiento
            if "error" in bank_response_1:
                return Response({"error": bank_response_1["error"]}, status=status.HTTP_400_BAD_REQUEST)

            # Procesar con process_bank_transfer1
            bank_response_2 = process_bank_transfer11(transfer, idempotency_key)

            # Verificar si hubo un error en el segundo procesamiento
            if "error" in bank_response_2:
                return Response({"error": bank_response_2["error"]}, status=status.HTTP_400_BAD_REQUEST)

            # Actualizar el estado de la transferencia
            transfer.transaction_status = "ACCP"
            transfer.save()

            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response_1": bank_response_1,
                "bank_response_2": bank_response_2
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)