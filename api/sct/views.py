from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.sct.models import (
    SepaCreditTransferRequest, SepaCreditTransferResponse,
    SepaCreditTransferDetailsResponse, SepaCreditTransferUpdateScaRequest
)
from api.sct.process_transfer import ProcessTransferView11, ProcessTransferView12
from api.sct.serializers import (
    SepaCreditTransferRequestSerializer, SepaCreditTransferResponseSerializer,
    SepaCreditTransferDetailsResponseSerializer, SepaCreditTransferUpdateScaRequestSerializer
)
from django.conf import settings
import os
import logging
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
    """
    View for creating and listing SEPA credit transfers.
    """
    def get(self, request):
        """Get all SEPA credit transfers."""
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new SEPA credit transfer."""
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            transfer = serializer.save(transaction_status="PDNG")
            response_data = {
                "transaction_status": transfer.transaction_status,
                "payment_id": str(transfer.payment_id), # Ensure UUID is serialized as string
                "auth_id": str(transfer.auth_id), # Ensure UUID is serialized as string
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SepaCreditTransferCreateView2(APIView):
    """
    Version 2 of the SEPA Credit Transfer creation view.
    
    This view extends the base SepaCreditTransferCreateView with
    additional features including enhanced validation and metadata.
    """
    
    def get(self, request):
        """Get all SEPA credit transfers with additional metadata."""
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        
        # Add API version and metadata to the response
        response_data = {
            "api_version": "2.0",
            "count": len(serializer.data),
            "transfers": serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new SEPA credit transfer with enhanced validation."""
        # Check for idempotency key in headers
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            return Response(
                {"error": f"{IDEMPOTENCY_HEADER} header is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check for existing transfer with the same idempotency key
        existing_transfer = SepaCreditTransferRequest.objects.filter(
            idempotency_key=idempotency_key
        ).first()
        
        if existing_transfer:
            # Return the existing transfer details
            return Response({
                "message": "Duplicate transfer",
                "transaction_status": existing_transfer.transaction_status,
                "payment_id": str(existing_transfer.payment_id),
                "auth_id": str(existing_transfer.auth_id),
                "api_version": "2.0"
            }, status=status.HTTP_200_OK)
        
        # Validate and create the transfer
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Save the transfer with the idempotency key
            transfer = serializer.save(
                transaction_status="PDNG",
                idempotency_key=idempotency_key
            )
            
            # Try to generate SEPA XML for validation
            try:
                generate_sepa_xml(transfer)
                
                # Return success response
                response_data = {
                    "transaction_status": transfer.transaction_status,
                    "payment_id": str(transfer.payment_id),
                    "auth_id": str(transfer.auth_id),
                    "api_version": "2.0",
                    "created_at": transfer.created_at.isoformat() if hasattr(transfer, 'created_at') else None
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                # XML generation failed - log and return error
                logger.error(f"Error validating transfer XML: {str(e)}", exc_info=True)
                
                # Clean up the invalid transfer
                transfer.delete()
                
                return Response({
                    "error": "Transfer data could not be validated for SEPA compliance",
                    "details": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SepaCreditTransferCreateWithXmlView(APIView):
    """
    View for creating SEPA credit transfers with XML generation.
    """
    def get(self, request):
        """Get all SEPA credit transfers."""
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new SEPA credit transfer and generate XML."""
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            transfer = serializer.save(transaction_status="PDNG")
            try:
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
            except Exception as e:
                logger.error(f"Error generating XML: {str(e)}", exc_info=True)
                return Response({"error": f"Error generating XML: {str(e)}"},
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SepaCreditTransferDetailsView(APIView):
    """
    View to get details of a SEPA credit transfer.
    """
    def get(self, request, payment_id):
        """Get details of a specific SEPA transfer."""
        try:
            transfer = SepaCreditTransferDetailsResponse.objects.get(payment_id=payment_id)
            serializer = SepaCreditTransferDetailsResponseSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferDetailsResponse.DoesNotExist:
            logger.error(f"Transfer with payment_id {payment_id} not found")
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching transfer details: {str(e)}", exc_info=True)
            return Response({"error": f"Unexpected error: {str(e)}"},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SepaCreditTransferStatusView(APIView):
    """
    View to get the status of a SEPA credit transfer.
    """
    def get(self, request, payment_id):
        """Get status of a specific SEPA transfer."""
        try:
            transfer = SepaCreditTransferResponse.objects.get(payment_id=payment_id)
            serializer = SepaCreditTransferResponseSerializer(transfer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferResponse.DoesNotExist:
            logger.error(f"Transfer with payment_id {payment_id} not found")
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error fetching transfer status: {str(e)}", exc_info=True)
            return Response({"error": f"Unexpected error: {str(e)}"},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SepaCreditTransferCancelView(APIView):
    """
    View to cancel a SEPA credit transfer.
    """
    def delete(self, request, payment_id):
        """Cancel a specific SEPA transfer."""
        try:
            transfer = SepaCreditTransferRequest.objects.get(payment_id=payment_id)
            transfer.delete()
            logger.info(f"Transfer with payment_id {payment_id} cancelled successfully")
            return Response({"message": "Transfer cancelled successfully"}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transfer with payment_id {payment_id} not found for cancellation")
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error cancelling transfer: {str(e)}", exc_info=True)
            return Response({"error": f"Unexpected error: {str(e)}"},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SepaCreditTransferUpdateScaView(APIView):
    """
    View to update the second factor authentication (SCA) of a SEPA credit transfer.
    """
    def patch(self, request, payment_id):
        """Update SCA of a specific SEPA transfer."""
        try:
            transfer = SepaCreditTransferUpdateScaRequest.objects.get(payment_id=payment_id)
            serializer = SepaCreditTransferUpdateScaRequestSerializer(transfer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "SCA updated successfully"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SepaCreditTransferUpdateScaRequest.DoesNotExist:
            logger.error(f"Transfer with payment_id {payment_id} not found for SCA update")
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating SCA: {str(e)}", exc_info=True)
            return Response({"error": f"Unexpected error: {str(e)}"},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SepaCreditTransferListView(APIView):
    """
    View to list all SEPA credit transfers.
    """
    def get(self, request):
        """Get all SEPA credit transfers."""
        try:
            transfers = SepaCreditTransferRequest.objects.all()
            serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error listing transfers: {str(e)}", exc_info=True)
            return Response({"error": f"Unexpected error: {str(e)}"},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SepaCreditTransferDownloadXmlView(APIView):
    """
    View to generate and download the XML file of a SEPA credit transfer.
    """
    def get(self, request, payment_id):
        """Generate and download XML file for a specific SEPA transfer."""
        try:
            transfer = SepaCreditTransferRequest.objects.get(payment_id=payment_id)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.payment_id}.xml")
            # Generate the XML file if it doesn't exist
            if not os.path.exists(xml_path):
                sepa_xml = generate_sepa_xml(transfer)
                with open(xml_path, "w") as xml_file:
                    xml_file.write(sepa_xml)
            # Download the XML file
            if os.path.exists(xml_path):
                return FileResponse(
                    open(xml_path, "rb"),
                    content_type="application/xml",
                    as_attachment=True,
                    filename=f"sepa_{transfer.payment_id}.xml"
                )
            return HttpResponseNotFound("XML file not found.")
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transfer with payment_id {payment_id} not found")
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generating/downloading XML file: {str(e)}", exc_info=True)
            return Response({"error": f"Unexpected error: {str(e)}"},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SepaCreditTransferDownloadPdfView(APIView):
    """
    View to download the PDF file of a SEPA credit transfer.
    """
    def get(self, request, payment_id):
        """Download PDF file for a specific SEPA transfer."""
        try:
            transfer = SepaCreditTransferRequest.objects.get(payment_id=payment_id)
            pdf_path = os.path.join(settings.MEDIA_ROOT, f"transferencia_{transfer.payment_id}.pdf")
            # Generate the PDF if it doesn't exist (add this functionality if needed)
            if not os.path.exists(pdf_path):
                pdf_path = generar_pdf_transferencia(transfer)
            # Download the PDF file
            if os.path.exists(pdf_path):
                return FileResponse(
                    open(pdf_path, "rb"),
                    content_type="application/pdf",
                    as_attachment=True,
                    filename=f"transferencia_{transfer.payment_id}.pdf"
                )
            return HttpResponseNotFound("PDF file not found.")
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transfer with payment_id {payment_id} not found")
            return Response({"error": "Transfer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error downloading PDF file: {str(e)}", exc_info=True)
            return Response({"error": f"Unexpected error: {str(e)}"},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SCTList55View(CreateView, ListView):
    """
    View for creating and listing SEPA credit transfers with web interface.
    Uses ProcessTransferView11 for processing.
    """
    model = SepaCreditTransferRequest
    form_class = SepaCreditTransferRequestForm
    template_name = "api/SCT/sct_list5.html"
    success_url = reverse_lazy('sct_list5')
    
    def get_initial(self) -> dict:
        """Initialize form with UUIDs and today's date."""
        initial = super().get_initial()
        initial['idempotency_key'] = uuid4()
        initial['payment_id'] = uuid4()
        initial['auth_id'] = uuid4()
        initial['payment_identification_end_to_end_id'] = uuid4()
        initial['requested_execution_date'] = date.today()
        return initial
    
    def get_context_data(self, **kwargs):
        """Add transfers to context data."""
        context = super().get_context_data(**kwargs)
        context['transfers'] = SepaCreditTransferRequest.objects.all()
        return context
    
    def form_valid(self, form):
        """Process transfer after form validation."""
        try:
            # Save the transfer
            transfer = form.save()
            
            # Process the transfer
            process_view = ProcessTransferView11()
            process_view.post(self.request, idempotency_key=transfer.idempotency_key)
            
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
            form.add_error(None, f"Error processing transfer: {str(e)}")
            return self.form_invalid(form)

class SCTList5View(CreateView, ListView):
    """
    View for creating and listing SEPA credit transfers with web interface.
    Uses ProcessTransferView12 for processing.
    """
    model = SepaCreditTransferRequest
    form_class = SepaCreditTransferRequestForm
    template_name = "api/SCT/sct_list5.html"
    success_url = reverse_lazy('sct_list5')
    
    def get_queryset(self):
        """Define the queryset that will be used as object_list."""
        return SepaCreditTransferRequest.objects.all()
    
    def get_initial(self) -> dict:
        """Initialize form with UUIDs and today's date."""
        initial = super().get_initial()
        initial['idempotency_key'] = uuid4()
        initial['payment_id'] = uuid4()
        initial['auth_id'] = uuid4()
        initial['payment_identification_end_to_end_id'] = uuid4()
        initial['requested_execution_date'] = date.today()
        return initial
    
    def get_context_data(self, **kwargs):
        """Add transfers to context data."""
        # Ensure self.object_list is defined
        self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        context['transfers'] = self.object_list # Use self.object_list
        return context
    
    def form_valid(self, form):
        """Process transfer after form validation."""
        try:
            # Save the transfer
            transfer = form.save()
            
            # Process the transfer
            process_view = ProcessTransferView12()
            response = process_view.post(self.request, idempotency_key=transfer.idempotency_key)
            
            # Check if there was an error
            if response.status_code != 200:
                form.add_error(None, "Error processing transfer.")
                return self.form_invalid(form)
                
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error processing transfer: {str(e)}", exc_info=True)
            form.add_error(None, f"Error processing transfer: {str(e)}")
            return self.form_invalid(form)

class DownloadXmlView(APIView):
    """
    View to download the XML file of a SEPA credit transfer by idempotency_key.
    """
    def get(self, request, idempotency_key):
        """Download XML file for a specific SEPA transfer by idempotency_key."""
        try:
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            xml_filename = f"sepa_{transfer.idempotency_key}.xml"
            xml_path = os.path.join(settings.MEDIA_ROOT, xml_filename)
            
            # Generate the XML file if it doesn't exist
            if not os.path.exists(xml_path):
                try:
                    xml_content = generate_sepa_xml(transfer)
                    with open(xml_path, "w") as xml_file:
                        xml_file.write(xml_content)
                except Exception as e:
                    logger.error(f"Error generating XML file: {str(e)}", exc_info=True)
                    return Response(
                        {"error": "Error generating XML file."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            # Download the XML file
            if os.path.exists(xml_path):
                return FileResponse(
                    open(xml_path, "rb"),
                    content_type="application/xml",
                    as_attachment=True,
                    filename=xml_filename
                )
                
            return HttpResponseNotFound("XML file not found.")
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transfer with idempotency_key {idempotency_key} not found.")
            return Response(
                {"error": "Transfer not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error processing request: {str(e)}", exc_info=True)
            return Response(
                {"error": "Unexpected error processing request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DownloadPdfView(APIView):
    """
    View to download the PDF file of a SEPA credit transfer.
    """
    def get(self, request, id):
        """Download PDF file for a specific SEPA transfer by id."""
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=id)
            pdf_path = os.path.join(settings.MEDIA_ROOT, f"transferencia_{transfer.id}.pdf")
            
            # Generate the PDF if it doesn't exist
            if not os.path.exists(pdf_path):
                pdf_path = generar_pdf_transferencia(transfer)
                
            # Download the PDF file
            if os.path.exists(pdf_path):
                return FileResponse(
                    open(pdf_path, "rb"),
                    content_type="application/pdf",
                    as_attachment=True,
                    filename=f"transferencia_{transfer.id}.pdf"
                )
                
            return HttpResponseNotFound("PDF file not found.")
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transfer with id {id} not found.")
            return HttpResponseNotFound("Transfer not found.")
        except Exception as e:
            logger.error(f"Error generating/downloading PDF file: {str(e)}", exc_info=True)
            return Response(
                {"error": "Unexpected error processing request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CancelTransferView(APIView):
    """
    View to cancel a SEPA credit transfer.
    """
    def post(self, request, id):
        """Cancel a specific SEPA transfer by id."""
        try:
            transfer = SepaCreditTransferRequest.objects.get(id=id)
            transfer.delete()
            logger.info(f"Transfer with id {id} successfully cancelled.")
            return Response(
                {"message": "Transfer successfully cancelled."},
                status=status.HTTP_200_OK
            )
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transfer with id {id} not found.", exc_info=True)
            return Response(
                {"error": "Transfer not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error cancelling transfer: {str(e)}", exc_info=True)
            return Response(
                {"error": "Unexpected error cancelling transfer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )