# mie_pdf_email.py
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

from mie_backend import obtener_mie_detalle


def generar_mie_pdf(mie_id: int) -> BytesIO:
    """
    Genera un PDF simple con los datos principales del MIE
    y devuelve un BytesIO listo para usar en st.download_button.
    """
    detalle = obtener_mie_detalle(mie_id)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    x = 50
    y = height - 50

    def line(text: str):
        nonlocal y
        c.drawString(x, y, text)
        y -= 15

    codigo = detalle.codigo_mie
    fecha_evento = detalle.fecha_hora_evento
    fecha_str = str(fecha_evento) if fecha_evento else "-"

    c.setFont("Helvetica-Bold", 14)
    line(f"MIE - {codigo}")
    c.setFont("Helvetica", 10)
    line(f"Fecha de generación PDF: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    line("Datos básicos del incidente")
    c.setFont("Helvetica", 10)
    line(f"Usuario que carga: {detalle.creado_por or '-'}")
    line(f"Fecha del evento: {fecha_str}")
    line(f"Fecha de carga: {detalle.fecha_creacion_registro or '-'}")
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    line("Ubicación / instalación")
    c.setFont("Helvetica", 10)
    line(f"Yacimiento: {getattr(detalle, 'yacimiento', '') or '-'}")
    line(f"Zona: {getattr(detalle, 'zona', '') or '-'}")
    line(f"Instalación: {getattr(detalle, 'nombre_instalacion', '') or '-'}")
    line(f"Latitud: {getattr(detalle, 'latitud', '') or '-'}")
    line(f"Longitud: {getattr(detalle, 'longitud', '') or '-'}")
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    line("Características del evento")
    c.setFont("Helvetica", 10)
    line(f"Tipo de afectación: {getattr(detalle, 'tipo_afectacion', '') or '-'}")
    line(f"Tipo de derrame: {getattr(detalle, 'tipo_derrame', '') or '-'}")
    line(f"Tipo de instalación: {getattr(detalle, 'tipo_instalacion', '') or '-'}")
    line(f"Causa inmediata: {getattr(detalle, 'causa_inmediata', '') or '-'}")
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    line("Volúmenes y área afectada")
    c.setFont("Helvetica", 10)
    line(f"Volumen bruto (m³): {getattr(detalle, 'volumen_bruto_m3', '') or '-'}")
    line(f"Volumen crudo (m³): {getattr(detalle, 'volumen_crudo_m3', '') or '-'}")
    line(f"Volumen gas (m³): {getattr(detalle, 'volumen_gas_m3', '') or '-'}")
    line(f"PPM / % agua: {getattr(detalle, 'ppm_agua', '') or '-'}")
    line(f"Área afectada (m²): {getattr(detalle, 'area_afectada_m2', '') or '-'}")
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    line("Otros datos / notas")
    c.setFont("Helvetica", 10)
    line(f"Causa probable: {detalle.causa_probable or '-'}")
    line(f"Responsable (texto): {detalle.responsable or '-'}")

    obs = (detalle.observaciones or "").strip()
    if obs:
        y -= 10
        c.setFont("Helvetica-Bold", 10)
        line("Observaciones:")
        c.setFont("Helvetica", 9)
        for parrafo in obs.split("\n"):
            line(parrafo[:110])  # corta para que no se vaya de ancho

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

