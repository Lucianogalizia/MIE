# mie_pdf_email.py
import os
import tempfile
import smtplib
from email.message import EmailMessage

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from mie_backend import obtener_mie_detalle


# ==============================
# CONFIG SMTP (completar vos)
# ==============================
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "TU_MAIL@empresa.com")
SMTP_PASS = os.getenv("SMTP_PASS", "TU_PASSWORD")  # mejor usar variables de entorno


# ------------------------------
# Generar PDF de un MIE
# ------------------------------
def generar_pdf_mie(mie_id: int) -> str:
    """
    Arma un PDF simple con los datos del MIE y devuelve
    la ruta del archivo generado (en /tmp).
    """
    detalle = obtener_mie_detalle(mie_id)
    if not detalle:
        raise ValueError(f"No se encontró el MIE con id {mie_id}")

    # Archivo temporal
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = tmp.name
    tmp.close()

    c = canvas.Canvas(pdf_path, pagesize=A4)
    text = c.beginText(40, 800)
    text.setFont("Helvetica", 10)

    def add(label, value):
        text.textLine(f"{label}: {'' if value is None else str(value)}")

    add("Código MIE", detalle.codigo_mie)
    add("Estado", detalle.estado)
    add("Usuario que carga", detalle.creado_por)
    add("Fecha evento", detalle.fecha_hora_evento)
    add("Fecha carga", detalle.fecha_creacion_registro)

    add("Yacimiento", getattr(detalle, "yacimiento", None))
    add("Zona", getattr(detalle, "zona", None))
    add("Nombre instalación", getattr(detalle, "nombre_instalacion", None))

    add("Tipo de afectación", getattr(detalle, "tipo_afectacion", None))
    add("Tipo de derrame", getattr(detalle, "tipo_derrame", None))
    add("Tipo de instalación", getattr(detalle, "tipo_instalacion", None))
    add("Causa inmediata", getattr(detalle, "causa_inmediata", None))

    add("Volumen bruto (m3)", getattr(detalle, "volumen_bruto_m3", None))
    add("Volumen crudo (m3)", getattr(detalle, "volumen_crudo_m3", None))
    add("Volumen gas (m3)", getattr(detalle, "volumen_gas_m3", None))
    add("PPM / % agua", getattr(detalle, "ppm_agua", None))
    add("Área afectada (m2)", getattr(detalle, "area_afectada_m2", None))

    add("Causa probable", detalle.causa_probable)
    add("Responsable (texto libre)", detalle.responsable)
    add("Notas / Observaciones", detalle.observaciones)
    add("Medidas inmediatas", getattr(detalle, "medidas_inmediatas", None))

    c.drawText(text)
    c.showPage()
    c.save()

    return pdf_path


# ------------------------------
# Enviar mail con adjunto PDF
# ------------------------------
def enviar_mie_por_mail(mie_id: int, destinatarios: list[str]):
    """
    Genera el PDF del MIE indicado y lo envía por mail
    a la lista de destinatarios.
    """
    if not destinatarios:
        raise ValueError("No se especificaron destinatarios")

    pdf_path = generar_pdf_mie(mie_id)
    detalle = obtener_mie_detalle(mie_id)

    asunto = f"MIE {detalle.codigo_mie} - {getattr(detalle, 'nombre_instalacion', '')}"
    cuerpo = (
        f"Se adjunta el registro del MIE {detalle.codigo_mie}.\n\n"
        f"Creado por: {detalle.creado_por}\n"
        f"Fecha evento: {detalle.fecha_hora_evento}\n"
        f"Yacimiento: {getattr(detalle, 'yacimiento', '')}\n"
        f"Zona: {getattr(detalle, 'zona', '')}\n"
    )

    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = SMTP_USER
    msg["To"] = ", ".join(destinatarios)
    msg.set_content(cuerpo)

    with open(pdf_path, "rb") as f:
        data = f.read()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(pdf_path),
        )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
