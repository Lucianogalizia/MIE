# mie_pdf_email.py

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from datetime import datetime


def _wrap_text(text, max_chars=90):
    """Divide un texto largo en líneas más cortas."""
    if not text:
        return []
    lines = []
    for raw_line in str(text).split("\n"):
        line = raw_line.strip()
        while len(line) > max_chars:
            # cortamos por el último espacio antes del límite
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
        return A4[1] - 2.5*cm  # y inicial nueva página
    return y


def _draw_paragraph(c, title, text, x, y, max_chars=90):
    """Imprime un título y un párrafo multilínea."""
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, title)
    y -= 0.5*cm

    c.setFont("Helvetica", 9)
    for line in _wrap_text(text, max_chars=max_chars):
        y = _ensure_space(c, y)
        c.drawString(x, y, line)
        y -= 0.4*cm
    return y


def _draw_images_block(c, titulo, fotos, x, y, max_width=16*cm, max_height=8*cm):
    """
    Dibuja un bloque de fotos (ANTES o DESPUÉS).
    'fotos' es una lista de dicts con keys: tipo, fecha_hora, data.
    """
    if not fotos:
        return y

    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, titulo)
    y -= 0.7*cm

    for idx, foto in enumerate(fotos, start=1):
        y = _ensure_space(c, y, min_y=6*cm)  # necesitamos más lugar para la imagen
        # Texto arriba de la foto
        c.setFont("Helvetica", 9)
        fecha_txt = foto.get("fecha_hora", "")
        c.drawString(x, y, f"Foto {idx} - {fecha_txt}")
        y -= 0.5*cm

        # Imagen
        try:
            img_data = foto.get("data")
            if img_data:
                img = ImageReader(BytesIO(img_data))
                iw, ih = img.getSize()
                escala = min(max_width / iw, max_height / ih)
                w = iw * escala
                h = ih * escala

                # Si no entra, pasamos a página nueva
                if y - h < 2*cm:
                    c.showPage()
                    y = A4[1] - 2.5*cm

                c.drawImage(
                    img,
                    x,
                    y - h,
                    width=w,
                    height=h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                y -= h + 0.7*cm
        except Exception:
            # Si falla la imagen, seguimos sin cortar el PDF
            y -= 0.5*cm

    return y


def generar_mie_pdf(detalle, fotos):
    """
    Genera un PDF con:
      - Datos del incidente
      - Fotos ANTES
      - (Opcional) Datos de remediación
      - (Opcional) Fotos DESPUÉS

    'detalle' = objeto con todos los campos del MIE (incluye remediación si existe)
    'fotos'   = lista de dicts con keys: tipo ("ANTES"/"DESPUES"), fecha_hora, data
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margen_x = 2.0 * cm
    x_label = margen_x
    x_value = margen_x + 5.0 * cm
    y = height - 2.5 * cm

    codigo = getattr(detalle, "codigo_mie", "MIE")
    nombre_inst = (
        getattr(detalle, "nombre_instalacion", None)
        or getattr(detalle, "pozo", "")
        or ""
    ).strip()

    # ------------------------------------------------------------------
    # Título
    # ------------------------------------------------------------------
    c.setFont("Helvetica-Bold", 14)
    titulo = f"MIE {codigo}"
    if nombre_inst:
        titulo += f" - {nombre_inst}"
    c.drawString(margen_x, y, titulo)
    y -= 0.6 * cm

    c.setFont("Helvetica", 9)
    c.drawString(
        margen_x,
        y,
        f"Fecha de generación: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} (UTC)",
    )
    y -= 1.0 * cm

    # ------------------------------------------------------------------
    # 1. Datos básicos del incidente
    # ------------------------------------------------------------------
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margen_x, y, "1. Datos básicos del incidente")
    y -= 0.7 * cm

    _draw_label_value(c, "DRM / Nº incidente", codigo, x_label, x_value, y)
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
    y -= 0.7 * cm

    # ------------------------------------------------------------------
    # 2. Personas involucradas
    # ------------------------------------------------------------------
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margen_x, y, "2. Personas involucradas")
    y -= 0.6 * cm

    obs_ap = getattr(detalle, "observador_apellido", "") or ""
    obs_no = getattr(detalle, "observador_nombre", "") or ""
    resp_ap = getattr(detalle, "responsable_inst_apellido", "") or ""
    resp_no = getattr(detalle, "responsable_inst_nombre", "") or ""

    _draw_label_value(c, "Observador", f"{obs_ap} {obs_no}".strip(), x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Responsable de la instalación",
        f"{resp_ap} {resp_no}".strip(),
        x_label,
        x_value,
        y,
    )
    y -= 0.7 * cm

    # ------------------------------------------------------------------
    # 3. Ubicación / instalación
    # ------------------------------------------------------------------
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margen_x, y, "3. Ubicación / instalación")
    y -= 0.6 * cm

    _draw_label_value(c, "Yacimiento", getattr(detalle, "yacimiento", ""), x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Zona", getattr(detalle, "zona", ""), x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Nombre instalación / Pozo",
        nombre_inst,
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(c, "Latitud", getattr(detalle, "latitud", ""), x_label, x_value, y)
    y -= 0.4 * cm
    _draw_label_value(c, "Longitud", getattr(detalle, "longitud", ""), x_label, x_value, y)
    y -= 0.7 * cm

    # ------------------------------------------------------------------
    # 4. Características del evento
    # ------------------------------------------------------------------
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margen_x, y, "4. Características del evento")
    y -= 0.6 * cm

    _draw_label_value(
        c,
        "Tipo de afectación",
        getattr(detalle, "tipo_afectacion", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Tipo de derrame",
        getattr(detalle, "tipo_derrame", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Tipo de instalación",
        getattr(detalle, "tipo_instalacion", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Causa inmediata",
        getattr(detalle, "causa_inmediata", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.7 * cm

    # ------------------------------------------------------------------
    # 5. Volúmenes y área afectada
    # ------------------------------------------------------------------
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margen_x, y, "5. Volúmenes y área afectada")
    y -= 0.6 * cm

    _draw_label_value(
        c,
        "Volumen bruto (m³)",
        getattr(detalle, "volumen_bruto_m3", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Volumen de crudo (m³)",
        getattr(detalle, "volumen_crudo_m3", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Volumen de gas (m³)",
        getattr(detalle, "volumen_gas_m3", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "PPM o % de agua",
        getattr(detalle, "ppm_agua", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Área afectada (m²)",
        getattr(detalle, "area_afectada_m2", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.7 * cm

    # ------------------------------------------------------------------
    # 6. Recursos afectados
    # ------------------------------------------------------------------
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margen_x, y, "6. Recursos afectados")
    y -= 0.6 * cm
    c.setFont("Helvetica", 9)
    for line in _wrap_text(getattr(detalle, "recursos_afectados", ""), max_chars=90):
        y = _ensure_space(c, y)
        c.drawString(margen_x, y, line)
        y -= 0.4 * cm
    y -= 0.3 * cm

    # ------------------------------------------------------------------
    # 7. Otros datos / notas
    # ------------------------------------------------------------------
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margen_x, y, "7. Otros datos / notas")
    y -= 0.6 * cm

    _draw_label_value(
        c,
        "Causa probable",
        getattr(detalle, "causa_probable", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Responsable",
        getattr(detalle, "responsable", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.5 * cm

    texto_obs = getattr(detalle, "observaciones", "") or ""
    y = _draw_paragraph(c, "Observaciones / Comentarios", texto_obs, margen_x, y)

    texto_medidas = getattr(detalle, "medidas_inmediatas", "") or ""
    y = _draw_paragraph(c, "Medidas inmediatas", texto_medidas, margen_x, y)

    # ------------------------------------------------------------------
    # 8. Aprobación
    # ------------------------------------------------------------------
    y = _ensure_space(c, y)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margen_x, y, "8. Aprobación")
    y -= 0.6 * cm

    ap_ap = getattr(detalle, "aprobador_apellido", "") or ""
    ap_no = getattr(detalle, "aprobador_nombre", "") or ""
    _draw_label_value(
        c,
        "Aprobador",
        f"{ap_ap} {ap_no}".strip(),
        x_label,
        x_value,
        y,
    )
    y -= 0.4 * cm
    _draw_label_value(
        c,
        "Fecha y hora de aprobación",
        getattr(detalle, "fecha_hora_aprobacion", ""),
        x_label,
        x_value,
        y,
    )
    y -= 0.8 * cm

    # ------------------------------------------------------------------
    # 9. Fotos del incidente (ANTES)
    # ------------------------------------------------------------------
    fotos_antes = [f for f in fotos if f.get("tipo") == "ANTES"]
    if fotos_antes:
        y = _draw_images_block(
            c,
            "9. Fotos del incidente (ANTES)",
            fotos_antes,
            margen_x,
            y,
        )

    # ------------------------------------------------------------------
    # 10. Remediación / Cierre (solo si realmente existe info)
    # ------------------------------------------------------------------
        # ------------------------------------------------------------------
    # 10. Remediación / Cierre (solo si realmente existe info)
    # ------------------------------------------------------------------

    rem_fecha = getattr(detalle, "rem_fecha_fin_saneamiento", None) or getattr(
        detalle, "rem_fecha", None
    )
    rem_vol_tierra = getattr(detalle, "rem_volumen_tierra_levantada", None)
    rem_destino = getattr(detalle, "rem_destino_tierra_impactada", None)
    rem_vol_liq = getattr(detalle, "rem_volumen_liquido_recuperado", None)
    rem_coment = getattr(detalle, "rem_comentarios", None) or getattr(
        detalle, "rem_detalle", None
    )
    rem_ap_ap = getattr(detalle, "rem_aprobador_apellido", None)
    rem_ap_no = getattr(detalle, "rem_aprobador_nombre", None)

    fotos_despues = [f for f in fotos if f.get("tipo") == "DESPUES"]
    hay_remediacion_datos = any([
        rem_fecha,
        rem_vol_tierra not in (None, 0),
        rem_destino,
        rem_vol_liq not in (None, 0),
        rem_coment,
        rem_ap_ap,
        rem_ap_no,
    ])
    estado = getattr(detalle, "estado", "").upper()

    if hay_remediacion_datos or fotos_despues or estado == "CERRADO":

        # === TÍTULO ===
        y = _ensure_space(c, y)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margen_x, y, "10. Remediación / Cierre")
        y -= 0.8 * cm

        linea_sep = 0.55 * cm  # separación más grande

        _draw_label_value(
            c, "Fecha fin saneamiento", rem_fecha or "", x_label, x_value, y
        )
        y -= linea_sep

        _draw_label_value(
            c, "Volumen de tierra levantada (m³)",
            rem_vol_tierra if rem_vol_tierra is not None else "",
            x_label, x_value, y
        )
        y -= linea_sep

        _draw_label_value(
            c, "Destino de la tierra impactada", rem_destino or "",
            x_label, x_value, y
        )
        y -= linea_sep

        _draw_label_value(
            c, "Volumen de líquido recuperado (m³)",
            rem_vol_liq if rem_vol_liq is not None else "",
            x_label, x_value, y
        )
        y -= (linea_sep + 0.2*cm)

        # === Comentarios (párrafo multilinea con más separación) ===
        y = _draw_paragraph(
            c,
            "Comentarios de remediación",
            rem_coment or "",
            margen_x,
            y,
            max_chars=85  # más ancho para evitar saltos feos
        )
        y -= 0.3*cm

        aprobador_final = f"{(rem_ap_ap or '').strip()} {(rem_ap_no or '').strip()}".strip()

        _draw_label_value(
            c, "Aprobador final", aprobador_final, x_label, x_value, y
        )
        y -= (linea_sep + 0.4*cm)

        # === 11. Fotos de la remediación ===
        if fotos_despues:
            y = _draw_images_block(
                c,
                "11. Fotos de la remediación (DESPUÉS)",
                fotos_despues,
                margen_x,
                y,
            )


    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf






