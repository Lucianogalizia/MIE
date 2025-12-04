# mie_pdf_email.py

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader


def _draw_title(c, text, y, font_size=16):
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(2 * cm, y, text)
    return y - 0.7 * cm


def _draw_label_value(c, label, value, y, label_width=5.5 * cm, font_size=9):
    """
    Dibuja:  LABEL: value
    """
    if value is None:
        value = ""
    value = str(value)

    c.setFont("Helvetica-Bold", font_size)
    c.drawString(2 * cm, y, f"{label}:")
    c.setFont("Helvetica", font_size)
    c.drawString(2 * cm + label_width, y, value)
    return y - 0.5 * cm


def _new_page_if_needed(c, y_min=2 * cm):
    """
    Si se quedó sin espacio en la página, crea una nueva
    y devuelve la nueva coordenada y inicial.
    """
    if y_min < 2 * cm:
        c.showPage()
        return A4[1] - 2 * cm
    return y_min


def _draw_images_section(c, fotos, tipo, page_width, page_height):
    """
    Inserta todas las fotos de un tipo ("ANTES" o "DESPUES") en páginas nuevas.
    'fotos' es la lista completa que viene de obtener_fotos_mie.
    """
    fotos_tipo = [f for f in fotos if f.get("tipo") == tipo]
    if not fotos_tipo:
        return

    for idx, f in enumerate(fotos_tipo, start=1):
        img_data = f.get("data")
        if img_data is None:
            continue

        c.showPage()
        y = page_height - 2 * cm
        c.setFont("Helvetica-Bold", 14)
        c.drawString(
            2 * cm,
            y,
            f"Foto {tipo.title()} {idx} - {f.get('fecha_hora', '')}",
        )

        y -= 1 * cm

        # Convertimos a ImageReader; img_data puede ser bytes o un objeto tipo imagen
        try:
            if isinstance(img_data, bytes):
                img = ImageReader(io.BytesIO(img_data))
            else:
                img = ImageReader(img_data)
        except Exception:
            # Si falla, seguimos con la siguiente sin romper todo
            continue

        iw, ih = img.getSize()

        max_w = page_width - 4 * cm
        max_h = page_height - 5 * cm

        escala = min(max_w / iw, max_h / ih)
        new_w = iw * escala
        new_h = ih * escala

        x = (page_width - new_w) / 2
        y_img = max(2 * cm, y - new_h)

        c.drawImage(
            img,
            x,
            y_img,
            width=new_w,
            height=new_h,
            preserveAspectRatio=True,
        )


def generar_mie_pdf(detalle, fotos):
    """
    Genera un PDF en memoria con TODA la info del MIE:
    - Datos iniciales
    - Volúmenes, recursos, medidas, aprobación
    - Datos de remediación (si está cerrado)
    - Fotos ANTES / DESPUES

    Parameters
    ----------
    detalle : objeto con atributos del MIE (lo devuelve obtener_mie_detalle)
    fotos   : lista de dicts con claves como 'tipo', 'fecha_hora', 'data' (obtener_fotos_mie)
    """
    buffer = io.BytesIO()

    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 2 * cm

    # ===============================
    # ENCABEZADO
    # ===============================
    codigo = getattr(detalle, "codigo_mie", "")
    nombre_inst = (
        (getattr(detalle, "nombre_instalacion", None) or detalle.pozo or "")
        .strip()
    )
    titulo = f"MIE {codigo}"
    if nombre_inst:
        titulo += f" - {nombre_inst}"

    y = _draw_title(c, titulo, y, font_size=18)

    fecha_generacion = datetime.now().strftime("%Y-%m-%d %H:%M")
    y = _draw_label_value(c, "Fecha de generación", fecha_generacion, y)

    # ===============================
    # DATOS BÁSICOS
    # ===============================
    y = _draw_title(c, "1. Datos básicos del incidente", y, font_size=12)
    y = _draw_label_value(c, "DRM / Nº incidente", detalle.drm, y)
    y = _draw_label_value(c, "Usuario que carga", detalle.creado_por, y)
    y = _draw_label_value(
        c, "Fecha y hora del evento", detalle.fecha_hora_evento, y
    )
    y = _draw_label_value(
        c, "Fecha y hora de carga", detalle.fecha_creacion_registro, y
    )

    y = _new_page_if_needed(c, y)

    # ===============================
    # PERSONAS INVOLUCRADAS
    # ===============================
    y = _draw_title(c, "2. Personas involucradas", y, font_size=12)
    obs_ap = getattr(detalle, "observador_apellido", "")
    obs_nom = getattr(detalle, "observador_nombre", "")
    resp_ap = getattr(detalle, "responsable_inst_apellido", "")
    resp_nom = getattr(detalle, "responsable_inst_nombre", "")

    y = _draw_label_value(
        c, "Observador", f"{obs_ap} {obs_nom}".strip(), y
    )
    y = _draw_label_value(
        c, "Responsable de la instalación", f"{resp_ap} {resp_nom}".strip(), y
    )

    y = _new_page_if_needed(c, y)

    # ===============================
    # UBICACIÓN / INSTALACIÓN
    # ===============================
    y = _draw_title(c, "3. Ubicación / instalación", y, font_size=12)
    y = _draw_label_value(c, "Yacimiento", getattr(detalle, "yacimiento", ""), y)
    y = _draw_label_value(c, "Zona", getattr(detalle, "zona", ""), y)
    y = _draw_label_value(
        c,
        "Nombre instalación / Pozo",
        nombre_inst,
        y,
    )
    y = _draw_label_value(c, "Latitud", getattr(detalle, "latitud", ""), y)
    y = _draw_label_value(c, "Longitud", getattr(detalle, "longitud", ""), y)

    y = _new_page_if_needed(c, y)

    # ===============================
    # CARACTERÍSTICAS DEL EVENTO
    # ===============================
    y = _draw_title(c, "4. Características del evento", y, font_size=12)
    y = _draw_label_value(
        c,
        "Tipo de afectación",
        getattr(detalle, "tipo_afectacion", ""),
        y,
    )
    y = _draw_label_value(
        c,
        "Tipo de derrame",
        getattr(detalle, "tipo_derrame", ""),
        y,
    )
    y = _draw_label_value(
        c,
        "Tipo de instalación",
        getattr(detalle, "tipo_instalacion", ""),
        y,
    )
    y = _draw_label_value(
        c,
        "Causa inmediata",
        getattr(detalle, "causa_inmediata", ""),
        y,
    )

    y = _new_page_if_needed(c, y)

    # ===============================
    # VOLÚMENES Y ÁREA AFECTADA
    # ===============================
    y = _draw_title(c, "5. Volúmenes y área afectada", y, font_size=12)
    y = _draw_label_value(
        c,
        "Volumen bruto (m³)",
        getattr(detalle, "volumen_bruto_m3", ""),
        y,
    )
    y = _draw_label_value(
        c,
        "Volumen de crudo (m³)",
        getattr(detalle, "volumen_crudo_m3", ""),
        y,
    )
    y = _draw_label_value(
        c,
        "Volumen de gas (m³)",
        getattr(detalle, "volumen_gas_m3", ""),
        y,
    )
    y = _draw_label_value(
        c,
        "PPM o % de agua",
        getattr(detalle, "ppm_agua", ""),
        y,
    )
    y = _draw_label_value(
        c,
        "Área afectada (m²)",
        getattr(detalle, "area_afectada_m2", ""),
        y,
    )

    y = _new_page_if_needed(c, y)

    # ===============================
    # RECURSOS AFECTADOS
    # ===============================
    y = _draw_title(c, "6. Recursos afectados", y, font_size=12)
    recursos = getattr(detalle, "recursos_afectados", "") or ""
    y = _draw_label_value(c, "Recursos afectados", recursos, y)

    y = _new_page_if_needed(c, y)

    # ===============================
    # OTROS DATOS / MEDIDAS
    # ===============================
    y = _draw_title(c, "7. Otros datos / notas", y, font_size=12)
    y = _draw_label_value(
        c, "Causa probable", getattr(detalle, "causa_probable", ""), y
    )
    y = _draw_label_value(
        c, "Responsable", getattr(detalle, "responsable", ""), y
    )
    y = _draw_label_value(
        c, "Medidas inmediatas",
        getattr(detalle, "medidas_inmediatas", ""),
        y,
    )

    # Observaciones en bloque aparte (puede ser largo)
    y = _new_page_if_needed(c, y)
    y = _draw_title(c, "Observaciones / Comentarios", y, font_size=11)
    obs = getattr(detalle, "observaciones", "") or ""
    # Hacemos un "wrap" simple por líneas
    c.setFont("Helvetica", 9)
    max_width = width - 4 * cm
    for linea in obs.split("\n"):
        # cortar líneas largas
        while linea:
            # si entra completa:
            if c.stringWidth(linea, "Helvetica", 9) <= max_width:
                c.drawString(2 * cm, y, linea)
                y -= 0.45 * cm
                break
            # si no entra, vamos cortando por palabras
            corte = len(linea)
            while c.stringWidth(linea[:corte], "Helvetica", 9) > max_width and " " in linea[:corte]:
                corte = linea[:corte].rfind(" ")
            if corte <= 0:
                # no hay espacio para cortar, forzamos
                corte = len(linea)
            c.drawString(2 * cm, y, linea[:corte])
            y -= 0.45 * cm
            linea = linea[corte:].lstrip()

        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
            c.setFont("Helvetica", 9)

    y = _new_page_if_needed(c, y)

    # ===============================
    # APROBACIÓN
    # ===============================
    y = _draw_title(c, "8. Aprobación", y, font_size=12)
    ap_ap = getattr(detalle, "aprobador_apellido", "")
    ap_nom = getattr(detalle, "aprobador_nombre", "")
    y = _draw_label_value(
        c, "Aprobador", f"{ap_ap} {ap_nom}".strip(), y
    )
    y = _draw_label_value(
        c,
        "Fecha y hora de aprobación",
        getattr(detalle, "fecha_hora_aprobacion", ""),
        y,
    )

    y = _new_page_if_needed(c, y)

    # ===============================
    # DATOS DE REMEDIACIÓN (SI ESTÁ CERRADO)
    # ===============================
    if getattr(detalle, "estado", "") == "CERRADO":
        y = _draw_title(c, "9. Remediación / Cierre", y, font_size=12)

        fecha_fin = getattr(
            detalle, "rem_fecha_fin_saneamiento", None
        ) or getattr(detalle, "rem_fecha", None)

        y = _draw_label_value(
            c, "Fecha fin saneamiento", fecha_fin, y
        )
        y = _draw_label_value(
            c,
            "Volumen de tierra levantada (m³)",
            getattr(detalle, "rem_volumen_tierra_levantada", ""),
            y,
        )
        y = _draw_label_value(
            c,
            "Destino de la tierra impactada",
            getattr(detalle, "rem_destino_tierra_impactada", ""),
            y,
        )
        y = _draw_label_value(
            c,
            "Volumen de líquido recuperado (m³)",
            getattr(detalle, "rem_volumen_liquido_recuperado", ""),
            y,
        )

        comentarios_rem = getattr(
            detalle, "rem_comentarios", None
        ) or getattr(detalle, "rem_detalle", None) or ""

        y = _draw_label_value(
            c,
            "Comentarios remediación",
            comentarios_rem,
            y,
        )

        apf_ap = getattr(detalle, "rem_aprobador_apellido", "")
        apf_nom = getattr(detalle, "rem_aprobador_nombre", "")
        y = _draw_label_value(
            c,
            "Aprobador final",
            f"{apf_ap} {apf_nom}".strip(),
            y,
        )

        y = _new_page_if_needed(c, y)

    # ===============================
    # FOTOS ANTES / DESPUÉS
    # ===============================
    if fotos:
        _draw_images_section(c, fotos, "ANTES", width, height)
        _draw_images_section(c, fotos, "DESPUES", width, height)

    # ===============================
    # CIERRE DEL PDF
    # ===============================
    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes




