# ================================================================
# mie_pdf_email.py — versión corregida y mejorada
# ================================================================

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from datetime import datetime


# --------------------------------------------------------------
# Helpers
# --------------------------------------------------------------
def _safe(v):
    """Evita imprimir 'None'."""
    return "" if v in (None, "None") else str(v)


def _wrap_text(text, max_chars=90):
    if not text:
        return []
    lines = []
    for raw in str(text).split("\n"):
        line = raw.strip()
        while len(line) > max_chars:
            corte = line.rfind(" ", 0, max_chars)
            if corte == -1:
                corte = max_chars
            lines.append(line[:corte])
            line = line[corte:].lstrip()
        if line:
            lines.append(line)
    return lines


def _ensure_space(c, y, min_y=2*cm):
    if y < min_y:
        c.showPage()
        return A4[1] - 2.5*cm
    return y


def _draw_label_value(c, label, value, x_label, x_value, y):
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_label, y, label)
    c.setFont("Helvetica", 9)
    c.drawString(x_value, y, _safe(value))


def _draw_paragraph(c, title, text, x, y, max_chars=90, spacing=0.42*cm):
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, title)
    y -= 0.55*cm

    c.setFont("Helvetica", 9)
    for line in _wrap_text(text, max_chars):
        y = _ensure_space(c, y)
        c.drawString(x, y, line)
        y -= spacing
    return y - 0.3*cm


def _draw_images_block(c, titulo, fotos, x, y,
                       max_width=15*cm, max_height=8*cm):
    if not fotos:
        return y

    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, titulo)
    y -= 0.7*cm

    for idx, foto in enumerate(fotos, start=1):

        y = _ensure_space(c, y, min_y=8*cm)

        fecha_txt = foto.get("fecha_hora", "")
        c.setFont("Helvetica", 9)
        c.drawString(x, y, f"Foto {idx} - {fecha_txt}")
        y -= 0.45*cm

        try:
            img_data = foto.get("data")
            if img_data:
                img = ImageReader(BytesIO(img_data))
                iw, ih = img.getSize()
                escala = min(max_width / iw, max_height / ih)
                w, h = iw * escala, ih * escala

                if y - h < 2.0 * cm:
                    c.showPage()
                    y = A4[1] - 2.5*cm
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(x, y, titulo)
                    y -= 0.7*cm

                c.drawImage(img, x, y - h, width=w, height=h,
                            preserveAspectRatio=True, mask="auto")
                y -= h + 0.9*cm

        except Exception:
            y -= 0.5*cm

    return y


# ================================================================
# GENERADOR PDF IADE
# ================================================================
def generar_mie_pdf(detalle, fotos):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin = 2*cm
    x_label = margin
    x_value = margin + 5.3*cm
    y = height - 2.3*cm

    codigo = _safe(getattr(detalle, "codigo_mie", "IADE"))
    nombre_inst = (
        _safe(getattr(detalle, "nombre_instalacion", ""))
        or _safe(getattr(detalle, "pozo", ""))
    ).strip()

    # ------------------------------------------------------------
    # TÍTULO
    # ------------------------------------------------------------
    c.setFont("Helvetica-Bold", 15)
    titulo = f"IADE — {codigo}"
    if nombre_inst:
        titulo += f" — {nombre_inst}"
    c.drawString(margin, y, titulo)
    y -= 0.9*cm

    c.setFont("Helvetica", 9)
    c.drawString(
        margin,
        y,
        f"PDF generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} (UTC)",
    )
    y -= 1.1*cm

    # ------------------------------------------------------------
    # 1. Datos básicos
    # ------------------------------------------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "1. Datos básicos del incidente")
    y -= 0.7*cm

    _draw_label_value(c, "Código IADE", codigo, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Usuario carga", detalle.creado_por, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Fecha incidente", detalle.fecha_hora_evento, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Fecha carga", getattr(detalle, "fecha_creacion_registro", ""), x_label, x_value, y); y -= 1.0*cm

    # ------------------------------------------------------------
    # 2. Personas
    # ------------------------------------------------------------
    obs = f"{_safe(detalle.observador_apellido)} {_safe(detalle.observador_nombre)}".strip()
    resp = f"{_safe(detalle.responsable_inst_apellido)} {_safe(detalle.responsable_inst_nombre)}".strip()

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "2. Personas involucradas")
    y -= 0.65*cm

    _draw_label_value(c, "Observador", obs, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Responsable instalación", resp, x_label, x_value, y); y -= 1.0*cm

    # ------------------------------------------------------------
    # 3. Ubicación
    # ------------------------------------------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "3. Ubicación / Instalación")
    y -= 0.65*cm

    _draw_label_value(c, "Yacimiento", detalle.yacimiento, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Zona", detalle.zona, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Instalación / Pozo", nombre_inst, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Latitud", detalle.latitud, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Longitud", detalle.longitud, x_label, x_value, y); y -= 1.0*cm

    # ------------------------------------------------------------
    # 4. Características
    # ------------------------------------------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "4. Características del evento")
    y -= 0.65*cm

    _draw_label_value(c, "Tipo afectación", detalle.tipo_afectacion, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Tipo derrame", detalle.tipo_derrame, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Tipo instalación", detalle.tipo_instalacion, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Causa inmediata", detalle.causa_inmediata, x_label, x_value, y); y -= 1.0*cm

    # ------------------------------------------------------------
    # 5. Volúmenes
    # ------------------------------------------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "5. Volúmenes y área afectada")
    y -= 0.65*cm

    _draw_label_value(c, "Volumen bruto (m³)", detalle.volumen_bruto_m3, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Volumen crudo (m³)", detalle.volumen_crudo_m3, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Volumen gas (m³)", detalle.volumen_gas_m3, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Agua / PPM", detalle.ppm_agua, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Área afectada (m²)", detalle.area_afectada_m2, x_label, x_value, y); y -= 1.0*cm

    # ------------------------------------------------------------
    # 6. Recursos afectados
    # ------------------------------------------------------------
    y = _draw_paragraph(c, "6. Recursos afectados", detalle.recursos_afectados, margin, y)

    # ------------------------------------------------------------
    # 7. Observaciones
    # ------------------------------------------------------------
    y = _draw_paragraph(c, "7. Observaciones / Comentarios", detalle.observaciones, margin, y)
    y = _draw_paragraph(c, "Medidas inmediatas", detalle.medidas_inmediatas, margin, y)

    # ------------------------------------------------------------
    # 8. Aprobación
    # ------------------------------------------------------------
    aprobador = f"{_safe(detalle.aprobador_apellido)} {_safe(detalle.aprobador_nombre)}".strip()

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "8. Aprobación")
    y -= 0.65*cm

    _draw_label_value(c, "Aprobador", aprobador, x_label, x_value, y); y -= 0.42*cm
    _draw_label_value(c, "Fecha aprobación", detalle.fecha_hora_aprobacion, x_label, x_value, y); y -= 1.0*cm

    # ------------------------------------------------------------
    # 9. Fotos ANTES
    # ------------------------------------------------------------
    fotos_antes = [f for f in fotos if f.get("tipo") == "ANTES"]
    y = _draw_images_block(c, "9. Fotos del incidente (ANTES)", fotos_antes, margin, y)

    # ------------------------------------------------------------
    # 10. Remediación
    # ------------------------------------------------------------
    rem_fields = [
        getattr(detalle, "rem_fecha_fin_saneamiento", None),
        getattr(detalle, "rem_volumen_tierra_levantada", None),
        getattr(detalle, "rem_destino_tierra_impactada", None),
        getattr(detalle, "rem_volumen_liquido_recuperado", None),
        getattr(detalle, "rem_comentarios", None),
    ]

    hay_remediacion = any(v not in (None, "", 0) for v in rem_fields)

    fotos_despues = [f for f in fotos if f.get("tipo") == "DESPUES"]

    if hay_remediacion or fotos_despues:
        y = _ensure_space(c, y)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "10. Remediación / Cierre")
        y -= 0.8*cm

        _draw_label_value(c, "Fecha fin saneamiento",
                          detalle.rem_fecha_fin_saneamiento, x_label, x_value, y); y -= 0.5*cm
        _draw_label_value(c, "Volumen tierra levantada (m³)",
                          detalle.rem_volumen_tierra_levantada, x_label, x_value, y); y -= 0.5*cm
        _draw_label_value(c, "Destino tierra impactada",
                          detalle.rem_destino_tierra_impactada, x_label, x_value, y); y -= 0.5*cm
        _draw_label_value(c, "Volumen líquido recuperado (m³)",
                          detalle.rem_volumen_liquido_recuperado, x_label, x_value, y); y -= 0.8*cm

        y = _draw_paragraph(c, "Comentarios de remediación",
                            _safe(detalle.rem_comentarios), margin, y)

        aprob_final = f"{_safe(detalle.rem_aprobador_apellido)} {_safe(detalle.rem_aprobador_nombre)}".strip()
        _draw_label_value(c, "Aprobador final", aprob_final, x_label, x_value, y)
        y -= 1.0*cm

        # ------------------------------------------------------------
        # 11. Fotos DESPUÉS
        # ------------------------------------------------------------
        y = _draw_images_block(c, "11. Fotos de la remediación (DESPUÉS)", fotos_despues, margin, y)

    # ------------------------------------------------------------
    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf









