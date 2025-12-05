# mie_pdf_email.py
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors


def generar_mie_pdf(detalle, fotos):
    """
    Genera un PDF prolijo con:
      - Datos del incidente
      - Fotos del incidente (ANTES)
      - Datos de remediación (si existen)
      - Fotos de remediación (DESPUÉS)

    detalle: objeto con los campos del MIE
    fotos:   lista de dicts {"tipo": "...", "fecha_hora": ..., "data": bytes}
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Estilos
    title_style = ParagraphStyle(
        "TituloMIE",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        spaceAfter=14,
        alignment=0,  # izquierda
    )

    subtitle_style = ParagraphStyle(
        "Subtitulo",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=12,
    )

    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=4,
    )

    text_style = styles["Normal"]

    story = []

    # -----------------------
    #  Título principal
    # -----------------------
    codigo = getattr(detalle, "codigo_mie", None) or getattr(detalle, "drm", "")
    nombre_inst = (
        getattr(detalle, "nombre_instalacion", None)
        or getattr(detalle, "pozo", "")
        or ""
    ).strip()

    titulo = f"MIE {codigo}"
    if nombre_inst:
        titulo += f" - {nombre_inst}"

    story.append(Paragraph(titulo, title_style))
    story.append(
        Paragraph(
            f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            subtitle_style,
        )
    )

    # Helper tabla 2 columnas
    def tabla_campos(filas):
        data = []
        for label, value in filas:
            if value is None:
                value = ""
            data.append([f"<b>{label}</b>", str(value)])

        table = Table(data, colWidths=[6 * cm, 9 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        return table

    # Helper para dibujar fotos en orden
    def agregar_fotos(titulo_seccion, lista_fotos):
        if not lista_fotos:
            return
        story.append(Paragraph(titulo_seccion, header_style))
        story.append(Spacer(0, 6))

        # Orden por fecha/hora para que se vea prolijo
        fotos_sorted = sorted(
            lista_fotos,
            key=lambda f: str(f.get("fecha_hora", "")),
        )

        for idx, f in enumerate(fotos_sorted, start=1):
            fecha_hora = f.get("fecha_hora", "")
            data = f.get("data", b"")

            story.append(
                Paragraph(f"Foto {idx} - {fecha_hora}", text_style)
            )
            story.append(Spacer(0, 4))

            try:
                img = Image(BytesIO(data))
                img._restrictSize(16 * cm, 18 * cm)
                story.append(img)
            except Exception:
                story.append(
                    Paragraph("[No se pudo mostrar la imagen]", text_style)
                )

            story.append(Spacer(0, 10))

    # ======================================================
    # 1. Datos básicos del incidente
    # ======================================================
    story.append(Paragraph("1. Datos básicos del incidente", header_style))
    story.append(
        tabla_campos(
            [
                ("DRM / Nº incidente", codigo),
                ("Usuario que carga", getattr(detalle, "creado_por", "")),
                ("Fecha y hora del evento", getattr(detalle, "fecha_hora_evento", "")),
                (
                    "Fecha y hora de carga",
                    getattr(detalle, "fecha_creacion_registro", ""),
                ),
            ]
        )
    )
    story.append(Spacer(0, 6))

    # ======================================================
    # 2. Personas involucradas
    # ======================================================
    story.append(Paragraph("2. Personas involucradas", header_style))
    story.append(
        tabla_campos(
            [
                (
                    "Observador",
                    f"{getattr(detalle, 'observador_apellido', '')} "
                    f"{getattr(detalle, 'observador_nombre', '')}".strip(),
                ),
                (
                    "Responsable de la instalación",
                    f"{getattr(detalle, 'responsable_inst_apellido', '')} "
                    f"{getattr(detalle, 'responsable_inst_nombre', '')}".strip(),
                ),
            ]
        )
    )
    story.append(Spacer(0, 6))

    # ======================================================
    # 3. Ubicación / instalación
    # ======================================================
    story.append(Paragraph("3. Ubicación / instalación", header_style))
    story.append(
        tabla_campos(
            [
                ("Yacimiento", getattr(detalle, "yacimiento", "")),
                ("Zona", getattr(detalle, "zona", "")),
                ("Nombre instalación / Pozo", nombre_inst),
                ("Latitud", getattr(detalle, "latitud", "")),
                ("Longitud", getattr(detalle, "longitud", "")),
            ]
        )
    )
    story.append(Spacer(0, 6))

    # ======================================================
    # 4. Características del evento
    # ======================================================
    story.append(Paragraph("4. Características del evento", header_style))
    story.append(
        tabla_campos(
            [
                ("Tipo de afectación", getattr(detalle, "tipo_afectacion", "")),
                ("Tipo de derrame", getattr(detalle, "tipo_derrame", "")),
                ("Tipo de instalación", getattr(detalle, "tipo_instalacion", "")),
                ("Causa inmediata", getattr(detalle, "causa_inmediata", "")),
            ]
        )
    )
    story.append(Spacer(0, 6))

    # ======================================================
    # 5. Volúmenes y área afectada
    # ======================================================
    story.append(Paragraph("5. Volúmenes y área afectada", header_style))
    story.append(
        tabla_campos(
            [
                ("Volumen bruto (m³)", getattr(detalle, "volumen_bruto_m3", "")),
                ("Volumen de crudo (m³)", getattr(detalle, "volumen_crudo_m3", "")),
                ("Volumen de gas (m³)", getattr(detalle, "volumen_gas_m3", "")),
                ("PPM o % de agua", getattr(detalle, "ppm_agua", "")),
                ("Área afectada (m²)", getattr(detalle, "area_afectada_m2", "")),
            ]
        )
    )
    story.append(Spacer(0, 6))

    # ======================================================
    # 6. Recursos afectados
    # ======================================================
    story.append(Paragraph("6. Recursos afectados", header_style))
    recursos = getattr(detalle, "recursos_afectados", "") or "-"
    story.append(Paragraph(recursos, text_style))
    story.append(Spacer(0, 6))

    # ======================================================
    # 7. Otros datos / notas
    # ======================================================
    story.append(Paragraph("7. Otros datos / notas", header_style))
    story.append(
        tabla_campos(
            [
                ("Causa probable", getattr(detalle, "causa_probable", "")),
                ("Responsable", getattr(detalle, "responsable", "")),
            ]
        )
    )
    story.append(Spacer(0, 4))

    obs = getattr(detalle, "observaciones", "") or ""
    med = getattr(detalle, "medidas_inmediatas", "") or ""

    if obs:
        story.append(Paragraph("<b>Observaciones / Comentarios</b>", text_style))
        story.append(Paragraph(obs.replace("\n", "<br/>"), text_style))
        story.append(Spacer(0, 4))

    if med:
        story.append(Paragraph("<b>Medidas inmediatas</b>", text_style))
        story.append(Paragraph(med.replace("\n", "<br/>"), text_style))
        story.append(Spacer(0, 6))

    # ======================================================
    # 8. Aprobación
    # ======================================================
    story.append(Paragraph("8. Aprobación", header_style))
    aprobador_ini = (
        f"{getattr(detalle, 'aprobador_apellido', '')} "
        f"{getattr(detalle, 'aprobador_nombre', '')}"
    ).strip()
    story.append(
        tabla_campos(
            [
                ("Aprobador", aprobador_ini),
                (
                    "Fecha y hora de aprobación",
                    getattr(detalle, "fecha_hora_aprobacion", ""),
                ),
            ]
        )
    )
    story.append(Spacer(0, 8))

    # ======================================================
    # 9. Fotos del incidente (ANTES)
    # ======================================================
    fotos = fotos or []
    fotos_antes = [f for f in fotos if f.get("tipo", "").upper() == "ANTES"]
    fotos_despues = [f for f in fotos if f.get("tipo", "").upper() == "DESPUES"]

    if fotos_antes:
        agregar_fotos("9. Fotos del incidente (ANTES)", fotos_antes)

    # ======================================================
    # 10. Remediación / Cierre (solo si hay datos)
    # ======================================================
    rem_fecha = getattr(detalle, "rem_fecha_fin_saneamiento", None) or getattr(
        detalle, "rem_fecha", None
    )
    rem_vol_tierra = getattr(detalle, "rem_volumen_tierra_levantada", None)
    rem_destino_tierra = getattr(detalle, "rem_destino_tierra_impactada", None)
    rem_vol_liq = getattr(detalle, "rem_volumen_liquido_recuperado", None)
    rem_coment = getattr(detalle, "rem_comentarios", None) or getattr(
        detalle, "rem_detalle", None
    )
    rem_aprobador = (
        f"{getattr(detalle, 'rem_aprobador_apellido', '')} "
        f"{getattr(detalle, 'rem_aprobador_nombre', '')}"
    ).strip()

    # Detectar si REALMENTE hay remediación cargada
    has_rem_data = any(
        v not in (None, "", 0)
        for v in [
            rem_fecha,
            rem_vol_tierra,
            rem_destino_tierra,
            rem_vol_liq,
            rem_coment,
            rem_aprobador,
        ]
    )

    if has_rem_data:
        story.append(Spacer(0, 8))
        story.append(Paragraph("10. Remediación / Cierre", header_style))
        story.append(
            tabla_campos(
                [
                    ("Fecha fin saneamiento", rem_fecha),
                    ("Volumen de tierra levantada (m³)", rem_vol_tierra),
                    ("Destino de la tierra impactada", rem_destino_tierra),
                    ("Volumen de líquido recuperado (m³)", rem_vol_liq),
                ]
            )
        )
        story.append(Spacer(0, 4))

        if rem_coment:
            story.append(
                Paragraph("<b>Comentarios de remediación</b>", text_style)
            )
            story.append(
                Paragraph((rem_coment or "").replace("\n", "<br/>"), text_style)
            )
            story.append(Spacer(0, 4))

        if rem_aprobador:
            story.append(
                Paragraph(f"<b>Aprobador final:</b> {rem_aprobador}", text_style)
            )
        story.append(Spacer(0, 8))

    # ======================================================
    # 11. Fotos de la remediación (DESPUÉS)
    # ======================================================
    if fotos_despues:
        agregar_fotos("11. Fotos de la remediación (DESPUÉS)", fotos_despues)

    # Construimos el PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes





