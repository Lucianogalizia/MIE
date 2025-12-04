# mie_pdf_email.py

from io import BytesIO
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

from mie_backend import obtener_mie_detalle, obtener_fotos_mie


def _draw_multiline_text(c, text, x, y, max_width, leading=12, font_name="Helvetica", font_size=10):
    """
    Dibuja texto multilínea con salto de línea simple por palabras
    y devuelve la nueva coordenada y al terminar.
    """
    c.setFont(font_name, font_size)
    words = text.split()
    line = ""
    for w in words:
        test_line = (line + " " + w).strip()
        if c.stringWidth(test_line, font_name, font_size) > max_width:
            c.drawString(x, y, line)
            y -= leading
            line = w
        else:
            line = test_line
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def generar_mie_pdf(mie_id: int) -> bytes:
    """
    Genera un PDF con la información del MIE y las fotos asociadas.
    Devuelve los bytes del PDF (para usar en download_button).
    """
    detalle = obtener_mie_detalle(mie_id)
    fotos = obtener_fotos_mie(mie_id)  # lista de dicts con 'tipo', 'fecha_hora', 'data'

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margen_x = 2 * cm
    margen_y = 2 * cm
    max_text_width = width - 2 * margen_x

    y = height - margen_y

    # -----------------------------
    # ENCABEZADO
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margen_x, y, "MIE - Informe de Derrame / DRM")
    y -= 20

    c.setFont("Helvetica", 10)
    codigo = getattr(detalle, "codigo_mie", f"MIE-{mie_id}")
    c.drawString(margen_x, y, f"Código MIE: {codigo}")
    y -= 14
    c.drawString(margen_x, y, f"Número de incidente / DRM: {detalle.drm or '-'}")
    y -= 14
    c.drawString(margen_x, y, f"Usuario que carga el MIE: {detalle.creado_por or '-'}")
    y -= 20

    # Función helper para chequeo de salto de página en texto
    def ensure_space(c, y, needed=40):
        if y < margen_y + needed:
            c.showPage()
            return height - margen_y
        return y

    # -----------------------------
    # DATOS BÁSICOS
    # -----------------------------
    y = ensure_space(c, y)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_x, y, "Datos básicos del incidente")
    y -= 16
    c.setFont("Helvetica", 10)

    c.drawString(
        margen_x,
        y,
        f"Fecha del evento: {str(detalle.fecha_hora_evento or '')}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Fecha de carga: {str(detalle.fecha_creacion_registro or '')}",
    )
    y -= 20

    # -----------------------------
    # PERSONAS INVOLUCRADAS
    # -----------------------------
    y = ensure_space(c, y)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_x, y, "Personas involucradas")
    y -= 16
    c.setFont("Helvetica", 10)

    c.drawString(
        margen_x,
        y,
        f"Observador: "
        f"{(getattr(detalle, 'observador_apellido', '') or '').strip()}, "
        f"{(getattr(detalle, 'observador_nombre', '') or '').strip()}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Responsable de la instalación: "
        f"{(getattr(detalle, 'responsable_inst_apellido', '') or '').strip()}, "
        f"{(getattr(detalle, 'responsable_inst_nombre', '') or '').strip()}",
    )
    y -= 20

    # -----------------------------
    # UBICACIÓN / INSTALACIÓN
    # -----------------------------
    y = ensure_space(c, y)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_x, y, "Ubicación / instalación")
    y -= 16
    c.setFont("Helvetica", 10)

    c.drawString(
        margen_x,
        y,
        f"Yacimiento: {getattr(detalle, 'yacimiento', '') or '-'}",
    )
    y -= 14
    c.drawString(margen_x, y, f"Zona: {getattr(detalle, 'zona', '') or '-'}")
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Instalación: {getattr(detalle, 'nombre_instalacion', '') or '-'}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Latitud: {getattr(detalle, 'latitud', '') or '-'}   "
        f"Longitud: {getattr(detalle, 'longitud', '') or '-'}",
    )
    y -= 20

    # -----------------------------
    # CARACTERÍSTICAS DEL EVENTO
    # -----------------------------
    y = ensure_space(c, y)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_x, y, "Características del evento")
    y -= 16
    c.setFont("Helvetica", 10)

    c.drawString(
        margen_x,
        y,
        f"Tipo de afectación: {getattr(detalle, 'tipo_afectacion', '') or '-'}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Tipo de derrame: {getattr(detalle, 'tipo_derrame', '') or '-'}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Tipo de instalación: {getattr(detalle, 'tipo_instalacion', '') or '-'}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Causa inmediata: {getattr(detalle, 'causa_inmediata', '') or '-'}",
    )
    y -= 20

    # -----------------------------
    # VOLÚMENES Y ÁREA
    # -----------------------------
    y = ensure_space(c, y)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_x, y, "Volúmenes y área afectada")
    y -= 16
    c.setFont("Helvetica", 10)

    c.drawString(
        margen_x,
        y,
        f"Volumen bruto (m³): {getattr(detalle, 'volumen_bruto_m3', '') or '-'}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Volumen crudo (m³): {getattr(detalle, 'volumen_crudo_m3', '') or '-'}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Volumen gas (m³): {getattr(detalle, 'volumen_gas_m3', '') or '-'}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"PPM / % agua: {getattr(detalle, 'ppm_agua', '') or '-'}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Área afectada (m²): {getattr(detalle, 'area_afectada_m2', '') or '-'}",
    )
    y -= 20

    # -----------------------------
    # RECURSOS AFECTADOS
    # -----------------------------
    recursos = getattr(detalle, "recursos_afectados", "") or "-"
    y = ensure_space(c, y)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_x, y, "Recursos afectados")
    y -= 16
    c.setFont("Helvetica", 10)
    y = _draw_multiline_text(c, recursos, margen_x, y, max_text_width)
    y -= 10

    # -----------------------------
    # OTROS DATOS / NOTAS
    # -----------------------------
    y = ensure_space(c, y)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_x, y, "Otros datos / notas")
    y -= 16
    c.setFont("Helvetica", 10)

    causa_prob = detalle.causa_probable or "-"
    responsable = detalle.responsable or "-"
    observ = detalle.observaciones or "-"
    medidas = getattr(detalle, "medidas_inmediatas", "") or "-"

    c.drawString(margen_x, y, f"Causa probable: {causa_prob}")
    y -= 14
    c.drawString(margen_x, y, f"Responsable: {responsable}")
    y -= 18

    y = _draw_multiline_text(
        c, f"Notas / Observaciones: {observ}", margen_x, y, max_text_width
    )
    y -= 6
    y = _draw_multiline_text(
        c, f"Medidas inmediatas: {medidas}", margen_x, y, max_text_width
    )
    y -= 14

    # -----------------------------
    # APROBACIÓN
    # -----------------------------
    y = ensure_space(c, y)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_x, y, "Aprobación")
    y -= 16
    c.setFont("Helvetica", 10)

    c.drawString(
        margen_x,
        y,
        f"Aprobador: "
        f"{(getattr(detalle, 'aprobador_apellido', '') or '').strip()}, "
        f"{(getattr(detalle, 'aprobador_nombre', '') or '').strip()}",
    )
    y -= 14
    c.drawString(
        margen_x,
        y,
        f"Fecha/hora aprobación: "
        f"{str(getattr(detalle, 'fecha_hora_aprobacion', '') or '-')}",
    )
    y -= 20

    # =============================
    # SECCIÓN FOTOS
    # =============================
    if fotos:
        c.showPage()  # empezamos página nueva para fotos
        y = height - margen_y

        c.setFont("Helvetica-Bold", 14)
        c.drawString(margen_x, y, "Fotos del incidente")
        y -= 24

        # Orden simple por tipo y fecha
        try:
            fotos_orden = sorted(
                fotos,
                key=lambda f: (
                    f.get("tipo", ""),
                    str(f.get("fecha_hora", "")),
                ),
            )
        except Exception:
            fotos_orden = fotos

        max_img_width = width - 2 * margen_x
        max_img_height = height / 2.0  # para que entren un par por página

        for f in fotos_orden:
            tipo = f.get("tipo", "SIN TIPO")
            fecha_foto = str(f.get("fecha_hora", ""))
            data = f.get("data", None)

            if not data:
                continue

            # Antes de cada foto, chequeamos espacio
            if y < margen_y + max_img_height + 40:
                c.showPage()
                y = height - margen_y
                c.setFont("Helvetica-Bold", 14)
                c.drawString(margen_x, y, "Fotos del incidente (cont.)")
                y -= 24

            # Título de la foto
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margen_x, y, f"{tipo} – {fecha_foto}")
            y -= 14

            # Convertimos a ImageReader
            try:
                img_reader = ImageReader(BytesIO(data))
                img_w, img_h = img_reader.getSize()
            except Exception:
                c.setFont("Helvetica", 9)
                c.drawString(margen_x, y, "[No se pudo cargar la imagen]")
                y -= 20
                continue

            # Escalar manteniendo proporción
            scale = min(max_img_width / img_w, max_img_height / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale

            # Coordenadas (x fijo, y se baja con la altura de la imagen)
            x_img = margen_x
            y_img = y - draw_h

            c.drawImage(
                img_reader,
                x_img,
                y_img,
                width=draw_w,
                height=draw_h,
                preserveAspectRatio=True,
                mask="auto",
            )

            y = y_img - 20  # dejamos un espacio después de la foto

    # =============================
    # CIERRE DEL PDF
    # =============================
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


