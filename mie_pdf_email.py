# mie_pdf_email.py

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from datetime import datetime


# ================================================================
# HELPERS
# ================================================================
def _wrap_text(text, max_chars=90):
    """Divide un texto largo en líneas más cortas."""
    if not text:
        return []
    lines = []
    for raw_line in str(text).split("\n"):
        line = raw_line.strip()
        while len(line) > max_chars:
            corte = line.rfind(" ", 0, max_chars)
            if corte == -1:
                corte = max_chars
            lines.append(line[:corte])
            line = line[corte:].lstrip()
        if line:
            lines.append(line)
    return lines


def _draw_label_value(c, label, value, x_label, x_value, y):
    """Imprime una línea 'label: valor'."""
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_label, y, label)
    c.setFont("Helvetica", 9)
    if value is not None:
        c.drawString(x_value, y, str(value))


def _ensure_space(c, y, min_y=2*cm):
    """Si no hay espacio suficiente en la página, crea una nueva."""
    if y < min_y:
        c.showPage()
        return A4[1] - 2.5*cm
    return y


def _draw_paragraph(c, title, text, x, y, max_chars=90):
    """Imprime un título y un párrafo multilínea."""
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, title)
    y -= 0.55 * cm

    c.setFont("Helvetica", 9)
    for line in _wrap_text(text, max_chars=max_chars):
        y = _ensure_space(c, y)
        c.drawString(x, y, line)
        y -= 0.38 * cm
    return y


def _draw_images_block(c, titulo, fotos, x, y, max_width=16*cm, max_height=8*cm):
    """Dibuja un bloque de fotos."""
    if not fotos:
        return y

    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, titulo)
    y -= 0.65 * cm

    for idx, foto in enumerate(fotos, start=1):
        y = _ensure_space(c, y, min_y=6*cm)

        c.setFont("Helvetica", 9)
        fecha_txt = foto.get("fecha_hora", "")
        c.drawString(x, y, f"Foto {idx} - {fecha_txt}")
        y -= 0.45 * cm

        try:
            img_data = foto.get("data")
            if img_data:
                img = ImageReader(BytesIO(img_data))
                iw, ih = img.getSize()
                escala = min(max_width / iw, max_height / ih)
                w = iw * escala
                h = ih * escala

                if y - h < 2 * cm:
                    c.showPage()
                    y = A4[1] - 2.5 * cm

                c.drawImage(
                    img,
                    x,
                    y - h,
                    width=w,
                    height=h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                y -= h + 0.7 * cm
        except Exception:
            y -= 0.5 * cm

    return y


# ================================================================
# GENERADOR PDF IADE
# ================================================================
def generar_mie_pdf(detalle, fotos):
    """
    Genera el PDF completo del IADE:
      - Datos del incidente
      - Fotos ANTES
      - Datos de remediación (solo si existen)
      - Fotos DESPUÉS
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin = 2.0 * cm
    x_label = margin
    x_value = margin + 5.0 * cm
    y = height - 2.5 * cm

    codigo = getattr(detalle, "codigo_mie", "IADE")
    nombre_inst = (getattr(detalle, "nombre_instalacion", None)
                   or getattr(detalle, "pozo", "")
                   or "").strip()

    # ================================================================
    # TÍTULO
    # ================================================================
    c.setFont("Helvetica-Bold", 14)
    titulo = f"IADE {codigo}"
    if nombre_inst:
        titulo += f" - {nombre_inst}"

    c.drawString(margin, y, titulo)
    y -= 0.7 * cm

    c.setFont("Helvetica", 9)
    c.drawString(
        margin,
        y,
        f"Fecha de generación: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} (UTC)",
    )
    y -= 1.0 * cm

    # ================================================================
    # 1. Datos básicos
    # ================================================================
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "1. Datos básicos del incidente")
    y -= 0.7 * cm

    _draw_label_value(c, "IADE / Nº incidente", codigo, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Usuario que carga", detalle.creado_por, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Fecha y hora del evento", detalle.fecha_hora_evento, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Fecha y hora de carga",
        getattr(detalle, "fecha_creacion_registro", ""),
        x_label,
        x_value,
        y,
    )
    y -= 1.0 * cm

    # ================================================================
    # 2. Personas involucradas
    # ================================================================
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "2. Personas involucradas")
    y -= 0.65 * cm

    obs = f"{(detalle.observador_apellido or '').strip()} {(detalle.observador_nombre or '').strip()}".strip()
    resp = f"{(detalle.responsable_inst_apellido or '').strip()} {(detalle.responsable_inst_nombre or '').strip()}".strip()

    _draw_label_value(c, "Observador", obs, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Responsable de la instalación", resp, x_label, x_value, y)
    y -= 1.0 * cm

    # ================================================================
    # 3. Ubicación
    # ================================================================
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "3. Ubicación / instalación")
    y -= 0.65 * cm

    _draw_label_value(c, "Yacimiento", detalle.yacimiento, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Zona", detalle.zona, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Instalación / Pozo", nombre_inst, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Latitud", detalle.latitud, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Longitud", detalle.longitud, x_label, x_value, y)
    y -= 1.0 * cm

    # ================================================================
    # 4. Características
    # ================================================================
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "4. Características del evento")
    y -= 0.65 * cm

    _draw_label_value(c, "Tipo de afectación", detalle.tipo_afectacion, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Tipo de derrame", detalle.tipo_derrame, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Tipo instalación", detalle.tipo_instalacion, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Causa inmediata", detalle.causa_inmediata, x_label, x_value, y)
    y -= 1.0 * cm

    # ================================================================
    # 5. Volúmenes
    # ================================================================
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "5. Volúmenes y área afectada")
    y -= 0.65 * cm

    _draw_label_value(c, "Volumen bruto (m³)", detalle.volumen_bruto_m3, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Volumen crudo (m³)", detalle.volumen_crudo_m3, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Volumen gas (m³)", detalle.volumen_gas_m3, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "PPM / % agua", detalle.ppm_agua, x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Área afectada (m²)", detalle.area_afectada_m2, x_label, x_value, y)
    y -= 1.0 * cm

    # ================================================================
    # 6. Recursos afectados
    # ================================================================
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "6. Recursos afectados")
    y -= 0.65 * cm

    for line in _wrap_text(detalle.recursos_afectados, 90):
        c.drawString(margin, y, line)
        y -= 0.38 * cm

    y -= 0.7 * cm

    # ================================================================
    # 7. Observaciones
    # ================================================================
    texto_obs = detalle.observaciones or ""
    y = _draw_paragraph(c, "7. Observaciones / Comentarios", texto_obs, margin, y)

    texto_med = detalle.medidas_inmediatas or ""
    y = _draw_paragraph(c, "Medidas inmediatas", texto_med, margin, y)

    # ================================================================
    # 8. Aprobación
    # ================================================================
    c.setFont("Helvetica-Bold", 11)
    y = _ensure_space(c, y)
    c.drawString(margin, y, "8. Aprobación")
    y -= 0.65 * cm

    aprobador = f"{(detalle.aprobador_apellido or '').strip()} {(detalle.aprobador_nombre or '').strip()}".strip()
    _draw_label_value(c, "Aprobador", aprobador, x_label, x_value, y)
    y -= 0.4 * cm

    _draw_label_value(c, "Fecha aprobación", detalle.fecha_hora_aprobacion, x_label, x_value, y)
    y -= 1.2 * cm

    # ================================================================
    # 9. Fotos ANTES
    # ================================================================
    fotos_antes = [f for f in fotos if f.get("tipo") == "ANTES"]
    if fotos_antes:
        y = _draw_images_block(c, "9. Fotos del incidente (ANTES)", fotos_antes, margin, y)

    # ================================================================
    # 10. Remediación — solo si existe
    # ================================================================
    rem_fecha = getattr(detalle, "rem_fecha_fin_saneamiento", None)
    rem_vol_tierra = getattr(detalle, "rem_volumen_tierra_levantada", None)
    rem_destino = getattr(detalle, "rem_destino_tierra_impactada", None)
    rem_vol_liq = getattr(detalle, "rem_volumen_liquido_recuperado", None)
    rem_coment = getattr(detalle, "rem_comentarios", None)
    rem_ap_ap = getattr(detalle, "rem_aprobador_apellido", None)
    rem_ap_no = getattr(detalle, "rem_aprobador_nombre", None)

    hay_remediacion = any([
        rem_fecha,
        rem_vol_tierra,
        rem_destino,
        rem_vol_liq,
        rem_coment,
        rem_ap_ap,
        rem_ap_no,
    ])

    fotos_despues = [f for f in fotos if f.get("tipo") == "DESPUES"]

    if hay_remediacion or fotos_despues:
        y = _ensure_space(c, y)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "10. Remediación / Cierre")
        y -= 0.8 * cm

        _draw_label_value(c, "Fecha fin saneamiento", rem_fecha, x_label, x_value, y)
        y -= 0.55 * cm

        _draw_label_value(c, "Volumen tierra levantada (m³)", rem_vol_tierra, x_label, x_value, y)
        y -= 0.55 * cm

        _draw_label_value(c, "Destino tierra impactada", rem_destino, x_label, x_value, y)
        y -= 0.55 * cm

        _draw_label_value(c, "Volumen líquido recuperado (m³)", rem_vol_liq, x_label, x_value, y)
        y -= 0.75 * cm

        y = _draw_paragraph(c, "Comentarios de remediación", rem_coment or "", margin, y)

        aprob_final = f"{(rem_ap_ap or '').strip()} {(rem_ap_no or '').strip()}".strip()
        _draw_label_value(c, "Aprobador final", aprob_final, x_label, x_value, y)
        y -= 1.0 * cm

        # ================================================================
        # 11. Fotos DESPUÉS
        # ================================================================
        if fotos_despues:
            y = _draw_images_block(c, "11. Fotos de la remediación (DESPUÉS)", fotos_despues, margin, y)

    # ================================================================
    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf







