from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
import os
from config import settings

def generar_comprobante_pdf(transferencia):
    # Nombre del archivo PDF
    pdf_filename = f"transferencia_{transferencia.codigo_transaccion}.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_filename)
    
    # Crear una respuesta HTTP con el tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprobante_{transferencia.id}.pdf"'

    # Crear el objeto canvas de ReportLab
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, "Comprobante de Transferencia SWIFT")

    # Detalles de la transferencia
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 150, f"Remitente: {transferencia.remitente.nombre}")
    p.drawString(100, height - 170, f"Cuenta Remitente: {transferencia.remitente.cuenta}")
    p.drawString(100, height - 190, f"Destinatario: {transferencia.destinatario.nombre}")
    p.drawString(100, height - 210, f"Cuenta Destinatario: {transferencia.destinatario.cuenta}")
    p.drawString(100, height - 230, f"Monto: {transferencia.monto} {transferencia.moneda}")
    p.drawString(100, height - 250, f"Concepto: {transferencia.concepto}")
    p.drawString(100, height - 270, f"Fecha: {transferencia.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(100, height - 290, f"Código de Transacción: {transferencia.codigo_transaccion}")

    # Finalizar el PDF
    p.showPage()
    p.save()

    return pdf_path

from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = HttpResponse(content_type='application/pdf')
    result['Content-Disposition'] = 'attachment; filename="comprobante.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        return None
    return result
