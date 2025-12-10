# ================================================================
# mie_pdf_email.py — versión "nivel auditoría" (MIA)
# ================================================================

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader


# --------------------------------------------------------------
# Helpers básicos
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


# --------------------------------------------------------------
# Helpers de página (encabezado / pie) para estilo auditoría
# --------------------------------------------------------------
def _draw_header(c, ctx):
    """Encabezado estándar en todas las páginas. Devuelve y inicial."""
    width, height = A4
    margin = 2 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, height - 1.5 * cm, "MIA - Incidentes Ambientales Declarados")

    c.setFont("Helvetica", 9)
    # Podés cambiar esto por el nombre de la empresa si querés
    c.drawString(margin, height - 2.0 * cm, "Operador: CLEAR PETROLEUM")

    # Número de página (simple)
    c.drawRightString(
        width - margin,
        height - 1.5 * cm,
        f"Página {ctx['page']}",
    )

    # Línea separadora
    c.setLineWidth(0.5)
    c.line(margin, height - 2.2 * cm, width - margin, height - 2.2 * cm)

    # y inicial para el contenido de la página
    return height - 2.7 * cm


def _draw_footer(c, ctx):
    """Pie estándar en todas las páginas."""
    width, _ = A4
    margin = 2 * cm

    c.setLineWidth(0.5)
    c.line(margin, 2.0 * cm, width - margin, 2.0 * cm)

    c.setFont("Helvetica", 7)
    c.drawString(
        margin,
        1.6 * cm,
        "Documento generado automáticamente desde el sistema MIA. Uso interno."
    )

    codigo = ctx.get("codigo", "")
    if codigo:
        c.drawRightString(
            width - margin,
            1.6 * cm,
            f"Código MIA: {codigo}",
        )


def _ensure_space(c, y, ctx, min_y=2.5 * cm):
    """
    Verifica espacio disponible.
    Si no hay, dibuja pie, pasa de página, actualiza header y devuelve nuevo y.
    """
    if y < min_y:
        _draw_footer(c, ctx)
        c.showPage()
        ctx["page"] += 1
        y = _draw_header(c, ctx)
    return y


def _draw_label_value(c, label, value, x_label, x_value, y):
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_label, y, label)
    c.setFont("Helvetica", 9)
    c.drawString(x_value, y, _safe(value))


def _draw_paragraph(c, ctx, title, text, x, y,
                    max_chars=90, spacing=0.42 * cm):
    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, title)
    y -= 0.55 * cm

    c.setFont("Helvetica", 9)
    for line in _wrap_text(text, max_chars):
        y = _ensure_space(c, y, ctx)
        c.drawString(x, y, line)
        y -= spacing
    return y - 0.3 * cm


def _draw_images_block(c, ctx, titulo, fotos, x, y,
                       max_width=15 * cm, max_height=8 * cm):
    if not fotos:
        return y

    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, titulo)
    y -= 0.7 * cm

    for idx, foto in enumerate(fotos, start=1):
        # Quiero espacio suficiente para la foto y descripción
        y = _ensure_space(c, y, ctx, min_y=8 * cm)

        fecha_txt = _safe(foto.get("fecha_hora", ""))
        c.setFont("Helvetica", 9)
        c.drawString(x, y, f"Foto {idx} - {fecha_txt}")
        y -= 0.45 * cm

        try:
            img_data = foto.get("data")
            if img_data:
                img = ImageReader(BytesIO(img_data))
                iw, ih = img.getSize()
                escala = min(max_width / iw, max_height / ih)
                w, h = iw * escala, ih * escala

                if y - h < 3.0 * cm:
                    # Cierro página actual con pie, paso a otra con header
                    _draw_footer(c, ctx)
                    c.showPage()
                    ctx["page"] += 1
                    y = _draw_header(c, ctx) - 0.7 * cm
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(x, y, titulo)
                    y -= 0.7 * cm

                c.drawImage(
                    img,
                    x,
                    y - h,
                    width=w,
                    height=h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                y -= h + 0.9 * cm

        except Exception:
            # Si falla la imagen, no rompo el PDF
            y -= 0.5 * cm

    return y


# ================================================================
# GENERADOR PDF MIA - Estilo auditoría
# ================================================================
def generar_mie_pdf(detalle, fotos):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin = 2 * cm
    x_label = margin
    x_value = margin + 5.3 * cm

    # Contexto de paginado / metadatos
    codigo = _safe(getattr(detalle, "codigo_mie", "MIA"))
    ctx = {
        "page": 1,
        "codigo": codigo,
    }

    # Encabezado inicial
    y = _draw_header(c, ctx)

    # Nombre instalación / pozo
    nombre_inst = (
        _safe(getattr(detalle, "nombre_instalacion", ""))
        or _safe(getattr(detalle, "pozo", ""))
    ).strip()

    # ------------------------------------------------------------
    # Título principal
    # ------------------------------------------------------------
    c.setFont("Helvetica-Bold", 14)
    titulo = f"Informe de Incidente Ambiental Declarado (MIA)"
    c.drawString(margin, y, titulo)
    y -= 0.8 * cm

    c.setFont("Helvetica-Bold", 11)
    subt = f"Código MIA: {codigo}"
    if nombre_inst:
        subt += f"  |  Instalación/Pozo: {nombre_inst}"
    c.drawString(margin, y, subt)
    y -= 0.6 * cm

    c.setFont("Helvetica", 9)
    c.drawString(
        margin,
        y,
        f"PDF generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} (UTC)",
    )
    y -= 1.0 * cm

    # ------------------------------------------------------------
    # 0. Resumen ejecutivo y trazabilidad
    # ------------------------------------------------------------
    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "0. Resumen ejecutivo y trazabilidad")
    y -= 0.7 * cm

    estado = _safe(getattr(detalle, "estado", ""))
    drm = _safe(getattr(detalle, "drm", ""))
    fecha_incidente = _safe(getattr(detalle, "fecha_hora_evento", ""))
    fecha_carga = _safe(getattr(detalle, "fecha_creacion_registro", ""))
    usuario = _safe(getattr(detalle, "creado_por", ""))

    resumen_lines = [
        f"- Estado actual del MIA: {estado or 'No informado'}",
        f"- DRM / referencia interna: {drm or '-'}",
        f"- Fecha y hora del incidente: {fecha_incidente or '-'}",
        f"- Fecha y hora de carga en sistema: {fecha_carga or '-'}",
        f"- Usuario que registra el MIA: {usuario or '-'}",
    ]

    c.setFont("Helvetica", 9)
    for line in resumen_lines:
        y = _ensure_space(c, y, ctx)
        c.drawString(margin, y, line)
        y -= 0.4 * cm
    y -= 0.5 * cm

    # ------------------------------------------------------------
    # 1. Datos básicos del incidente
    # ------------------------------------------------------------
    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "1. Datos básicos del incidente")
    y -= 0.7 * cm

    _draw_label_value(c, "Código MIA", codigo, x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "DRM / N° interno", drm, x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Usuario que carga", usuario, x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Fecha del incidente", fecha_incidente, x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Fecha de carga", fecha_carga, x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Estado del MIA", estado, x_label, x_value, y); y -= 1.0 * cm

    # ------------------------------------------------------------
    # 2. Personas involucradas
    # ------------------------------------------------------------
    obs = f"{_safe(getattr(detalle, 'observador_apellido', ''))} " \
          f"{_safe(getattr(detalle, 'observador_nombre', ''))}".strip()
    resp_inst = f"{_safe(getattr(detalle, 'responsable_inst_apellido', ''))} " \
                f"{_safe(getattr(detalle, 'responsable_inst_nombre', ''))}".strip()

    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "2. Personas involucradas")
    y -= 0.65 * cm

    _draw_label_value(c, "Observador", obs, x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Responsable de la instalación", resp_inst, x_label, x_value, y); y -= 1.0 * cm

    # ------------------------------------------------------------
    # 3. Ubicación / instalación
    # ------------------------------------------------------------
    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "3. Ubicación / instalación")
    y -= 0.65 * cm

    _draw_label_value(c, "Yacimiento", getattr(detalle, "yacimiento", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Zona", getattr(detalle, "zona", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Instalación / Pozo", nombre_inst, x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Latitud", getattr(detalle, "latitud", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Longitud", getattr(detalle, "longitud", ""), x_label, x_value, y); y -= 1.0 * cm

    # ------------------------------------------------------------
    # 4. Características del evento
    # ------------------------------------------------------------
    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "4. Características del evento")
    y -= 0.65 * cm

    _draw_label_value(c, "Tipo de afectación", getattr(detalle, "tipo_afectacion", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Tipo de derrame", getattr(detalle, "tipo_derrame", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Tipo de instalación", getattr(detalle, "tipo_instalacion", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Causa inmediata", getattr(detalle, "causa_inmediata", ""), x_label, x_value, y); y -= 1.0 * cm

    # ------------------------------------------------------------
    # 5. Volúmenes y área afectada
    # ------------------------------------------------------------
    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "5. Volúmenes y área afectada")
    y -= 0.65 * cm

    _draw_label_value(c, "Volumen bruto (m³)", getattr(detalle, "volumen_bruto_m3", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Volumen de crudo (m³)", getattr(detalle, "volumen_crudo_m3", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Volumen de gas (m³)", getattr(detalle, "volumen_gas_m3", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Agua / PPM", getattr(detalle, "ppm_agua", ""), x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Área afectada (m²)", getattr(detalle, "area_afectada_m2", ""), x_label, x_value, y); y -= 1.0 * cm

    # ------------------------------------------------------------
    # 6. Recursos afectados
    # ------------------------------------------------------------
    y = _draw_paragraph(
        c, ctx,
        "6. Recursos afectados",
        getattr(detalle, "recursos_afectados", "") or "",
        margin,
        y,
    )

    # ------------------------------------------------------------
    # 7. Observaciones y medidas inmediatas
    # ------------------------------------------------------------
    y = _draw_paragraph(
        c, ctx,
        "7. Observaciones / comentarios",
        getattr(detalle, "observaciones", "") or "",
        margin,
        y,
    )
    y = _draw_paragraph(
        c, ctx,
        "Medidas inmediatas adoptadas",
        getattr(detalle, "medidas_inmediatas", "") or "",
        margin,
        y,
    )

    # ------------------------------------------------------------
    # 8. Aprobación
    # ------------------------------------------------------------
    aprobador = f"{_safe(getattr(detalle, 'aprobador_apellido', ''))} " \
                f"{_safe(getattr(detalle, 'aprobador_nombre', ''))}".strip()
    fecha_aprob = _safe(getattr(detalle, "fecha_hora_aprobacion", ""))

    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "8. Aprobación")
    y -= 0.65 * cm

    _draw_label_value(c, "Aprobador", aprobador, x_label, x_value, y); y -= 0.42 * cm
    _draw_label_value(c, "Fecha y hora de aprobación", fecha_aprob, x_label, x_value, y); y -= 1.0 * cm

    # ------------------------------------------------------------
    # 9. Fotos del incidente (ANTES)
    # ------------------------------------------------------------
    fotos_antes = [f for f in fotos if f.get("tipo") == "ANTES"]
    y = _draw_images_block(c, ctx, "9. Fotos del incidente (ANTES)", fotos_antes, margin, y)

    # ------------------------------------------------------------
    # 10. Remediación / Cierre
    # ------------------------------------------------------------
    rem_fecha = getattr(detalle, "rem_fecha_fin_saneamiento", None)
    rem_vol_tierra = getattr(detalle, "rem_volumen_tierra_levantada", None)
    rem_destino = getattr(detalle, "rem_destino_tierra_impactada", None)
    rem_vol_liq = getattr(detalle, "rem_volumen_liquido_recuperado", None)
    rem_coment = getattr(detalle, "rem_comentarios", None)
    rem_ap_ape = getattr(detalle, "rem_aprobador_apellido", "")
    rem_ap_nom = getattr(detalle, "rem_aprobador_nombre", "")

    rem_fields = [rem_fecha, rem_vol_tierra, rem_destino, rem_vol_liq, rem_coment]
    fotos_despues = [f for f in fotos if f.get("tipo") == "DESPUES"]

    hay_remediacion = any(v not in (None, "", 0) for v in rem_fields)

    if hay_remediacion or fotos_despues:
        y = _ensure_space(c, y, ctx)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "10. Remediación / cierre del incidente")
        y -= 0.8 * cm

        _draw_label_value(c, "Fecha fin saneamiento", rem_fecha, x_label, x_value, y); y -= 0.5 * cm
        _draw_label_value(c, "Volumen tierra levantada (m³)", rem_vol_tierra, x_label, x_value, y); y -= 0.5 * cm
        _draw_label_value(c, "Destino tierra impactada", rem_destino, x_label, x_value, y); y -= 0.5 * cm
        _draw_label_value(c, "Volumen líquido recuperado (m³)", rem_vol_liq, x_label, x_value, y); y -= 0.8 * cm

        y = _draw_paragraph(
            c, ctx,
            "Comentarios de remediación",
            _safe(rem_coment),
            margin,
            y,
        )

        aprob_final = f"{_safe(rem_ap_ape)} {_safe(rem_ap_nom)}".strip()
        _draw_label_value(c, "Aprobador final remediación", aprob_final, x_label, x_value, y)
        y -= 1.0 * cm

        # --------------------------------------------------------
        # 11. Fotos de la remediación (DESPUÉS)
        # --------------------------------------------------------
        y = _draw_images_block(c, ctx, "11. Fotos de la remediación (DESPUÉS)", fotos_despues, margin, y)

    # ------------------------------------------------------------
    # 12. Firmas (espacio para auditoría / responsables)
    # ------------------------------------------------------------
    y = _ensure_space(c, y, ctx)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "12. Firmas y conformidades")
    y -= 0.8 * cm

    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Responsable de la instalación: _____________________________")
    y -= 0.8 * cm
    c.drawString(margin, y, "Responsable de Ambiente / HSE: _____________________________")
    y -= 0.8 * cm
    c.drawString(margin, y, "Auditor / Revisor interno: _________________________________")
    y -= 1.0 * cm

    # Pie de la última página
    _draw_footer(c, ctx)

    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf











