# mie_pdf_email.py

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def _draw_multiline_text(c, text, x, y, max_width, line_height=14):
    """
    Escribe texto multilínea manejando saltos de línea.
    """
    if not text:
        return y
    from textwrap import wrap
    lines = []
    for raw_line in str(text).split("\n"):
        raw_line = raw_line.strip()
        if not raw_line:
            lines.append("")
        else:
            # wrap por ancho aproximado (caracteres). Ajustable.
            for l in wrap(raw_line, width=90):
                lines.append(l)

    for line in lines:
        c.drawString(x, y, line)
        y -= line_height
    return y


def generar_mie_pdf(detalle, fotos):
    """
    Genera un PDF con:
      - Datos del MIE (detalle)
      - Primera foto 'ANTES' (si existe) o la primera foto de la lista.

    Parámetros:
      detalle: objeto devuelto por obtener_mie_detalle(mie_id)
      fotos: lista devuelta por obtener_fotos_mie(mie_id),
             con elementos tipo dict: {"tipo", "fecha_hora", "data", ...}

    Retorna:
      bytes del PDF (buffer.getvalue())
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x_margin = 40
    y = height - 40

    # Título
    c.setFont("Helvetica-Bold", 16)
    titulo = f"MIE - {detalle.codigo_mie or ''}"
    c.drawString(x_margin, y, titulo)
    y -= 25

    c.setFont("Helvetica", 9)
    from datetime import datetime as _dt
    c.drawString(
        x_margin,
        y,
        f"Fecha de generación PDF: {_dt.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
    )
    y -= 25

    # ---------------------------
    # Datos básicos del incidente
    # ---------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margin, y, "Datos básicos del incidente")
    y -= 18

    c.setFont("Helvetica", 10)
    y = _draw_multiline_text(
        c,
        f"Usuario que carga: {detalle.creado_por or ''}",
        x_margin,
        y,
        max_width=500,
    )
    y = _draw_multiline_text(
        c,
        f"Fecha del evento: {detalle.fecha_hora_evento}",
        x_margin,
        y,
        max_width=500,
    )
    y = _draw_multiline_text(
        c,
        f"Fecha de carga: {detalle.fecha_creacion_registro}",
        x_margin,
        y,
        max_width=500,
    )
    y -= 10

    # ---------------------------
    # Ubicación / instalación
    # ---------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margin, y, "Ubicación / instalación")
    y -= 18
    c.setFont("Helvetica", 10)

    y = _draw_multiline_text(
        c,
        f"Yacimiento: {getattr(detalle, 'yacimiento', '') or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Zona: {getattr(detalle, 'zona', '') or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Instalación: {getattr(detalle, 'nombre_instalacion', '') or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Latitud: {getattr(detalle, 'latitud', '') or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Longitud: {getattr(detalle, 'longitud', '') or ''}",
        x_margin,
        y,
        500,
    )
    y -= 10

    # ---------------------------
    # Características del evento
    # ---------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margin, y, "Características del evento")
    y -= 18
    c.setFont("Helvetica", 10)

    y = _draw_multiline_text(
        c,
        f"Tipo de afectación: {getattr(detalle, 'tipo_afectacion', '') or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Tipo de derrame: {getattr(detalle, 'tipo_derrame', '') or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Tipo de instalación: {getattr(detalle, 'tipo_instalacion', '') or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Causa inmediata: {getattr(detalle, 'causa_inmediata', '') or ''}",
        x_margin,
        y,
        500,
    )
    y -= 10

    # ---------------------------
    # Volúmenes y área
    # ---------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margin, y, "Volúmenes y área afectada")
    y -= 18
    c.setFont("Helvetica", 10)

    y = _draw_multiline_text(
        c,
        f"Volumen bruto (m³): {getattr(detalle, 'volumen_bruto_m3', '')}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Volumen crudo (m³): {getattr(detalle, 'volumen_crudo_m3', '')}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Volumen gas (m³): {getattr(detalle, 'volumen_gas_m3', '')}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"PPM / % agua: {getattr(detalle, 'ppm_agua', '') or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Área afectada (m²): {getattr(detalle, 'area_afectada_m2', '')}",
        x_margin,
        y,
        500,
    )
    y -= 10

    # ---------------------------
    # Otros datos / notas
    # ---------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margin, y, "Otros datos / notas")
    y -= 18
    c.setFont("Helvetica", 10)

    y = _draw_multiline_text(
        c,
        f"Causa probable: {detalle.causa_probable or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"Responsable (texto): {detalle.responsable or ''}",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        "Observaciones:",
        x_margin,
        y,
        500,
    )
    y = _draw_multiline_text(
        c,
        f"{detalle.observaciones or ''}",
        x_margin + 15,
        y,
        480,
    )

    # Nueva página si no queda espacio para la imagen
    if y < 200:
        c.showPage()
        y = height - 40

    # ------------------------------------------
    # FOTO "ANTES" (o la primera disponible)
    # ------------------------------------------
    foto_seleccionada = None
    if fotos:
        # PRIORIDAD: tipo 'ANTES'
        for f in fotos:
            if f.get("tipo") == "ANTES":
                foto_seleccionada = f
                break
        # si no hay 'ANTES', tomo la primera
        if not foto_seleccionada:
            foto_seleccionada = fotos[0]

    if foto_seleccionada and foto_seleccionada.get("data"):
        try:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_margin, y, "Foto ANTES")
            y -= 20

            img_bytes = foto_seleccionada["data"]
            # img_bytes ya viene de obtener_fotos_mie y funciona con st.image,
            # así que suele ser bytes.
            if isinstance(img_bytes, str):
                # por si llegara a venir como string (no debería)
                img_bytes = img_bytes.encode("latin1", errors="ignore")

            img_buffer = BytesIO(img_bytes)
            img = ImageReader(img_buffer)

            # tamaño máximo de la imagen en el PDF
            max_width = width - 2 * x_margin   # margen lateral
            max_height = 300

            iw, ih = img.getSize()
            ratio = min(max_width / iw, max_height / ih)

            draw_w = iw * ratio
            draw_h = ih * ratio

            x_img = x_margin
            y_img = y - draw_h

            c.drawImage(
                img,
                x_img,
                y_img,
                width=draw_w,
                height=draw_h,
                preserveAspectRatio=True,
                mask="auto",
            )
            y = y_img - 20
        except Exception as e:
            # Si algo falla, solo anotamos en texto y seguimos
            c.setFont("Helvetica", 9)
            c.drawString(
                x_margin,
                y,
                f"[No se pudo insertar la imagen ANTES en el PDF: {e}]",
            )
            y -= 15

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()



