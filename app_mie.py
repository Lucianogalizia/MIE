import streamlit as st
from datetime import datetime, date
from io import BytesIO
import pandas as pd

from mie_backend import (
    insertar_mie,
    insertar_foto,
    subir_foto_a_bucket,
    listar_mie,
    obtener_mie_detalle,
    obtener_fotos_mie,
    actualizar_mie_basico,
    cerrar_mie_con_remediacion,
    obtener_todos_mie,      # 👈 NUEVO
)


from mie_pdf_email import generar_mie_pdf  # genera el PDF en memoria

# =======================================================
#   CONFIGURACIÓN GENERAL
# =======================================================
st.set_page_config(page_title="IADE - Incidentes Ambientales Declarados", layout="wide")

st.title("🌱 Gestión de IADE (Incidentes Ambientales Declarados)")

modo = st.sidebar.radio(
    "Modo",
    ["Nuevo IADE", "Historial", "Exportar IADE"]
)


# =======================================================
#  MODO 1 - NUEVO IADE
# =======================================================
if modo == "Nuevo IADE":

    st.header("Registrar un nuevo IADE")

    # -----------------------
    # Datos básicos del incidente
    # -----------------------
    st.markdown("### Datos básicos del incidente")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fecha_evento = st.date_input("Fecha del evento", value=date.today())
    with col_f2:
        hora_evento = st.time_input(
            "Hora del evento",
            value=datetime.now().time().replace(microsecond=0),
        )

    fecha_hora_evento = datetime.combine(fecha_evento, hora_evento)

    # Número IADE autogenerado
    st.text_input(
        "Número de incidente / IADE",
        value="Se genera automáticamente al guardar",
        disabled=True,
    )
    drm = None

    creado_por = st.text_input("Usuario que carga el IADE")

    # -----------------------
    # Personas involucradas
    # -----------------------
    st.markdown("### Personas involucradas")

    col_obs1, col_obs2 = st.columns(2)
    with col_obs1:
        observador_apellido = st.text_input("Observador - Apellido")
    with col_obs2:
        observador_nombre = st.text_input("Observador - Nombre")

    col_resp1, col_resp2 = st.columns(2)
    with col_resp1:
        responsable_inst_apellido = st.text_input("Responsable instalación - Apellido")
    with col_resp2:
        responsable_inst_nombre = st.text_input("Responsable instalación - Nombre")

    # -----------------------
    # Ubicación / instalación
    # -----------------------
    st.markdown("### Ubicación / instalación")
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        yacimiento = st.text_input("Yacimiento")
    with col_u2:
        zona = st.text_input("Zona")
    with col_u3:
        nombre_instalacion = st.text_input("Nombre de la instalación")

    col_geo1, col_geo2 = st.columns(2)
    with col_geo1:
        latitud = st.text_input("Latitud")
    with col_geo2:
        longitud = st.text_input("Longitud")

    # -----------------------
    # Características del evento
    # -----------------------
    st.markdown("### Características del evento")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tipo_afectacion = st.selectbox(
            "Tipo de afectación",
            ["", "Derrame", "Aventamiento de gas"],
        )
        tipo_derrame = st.selectbox(
            "Tipo de derrame",
            [
                "",
                "Agua de Produccion",
                "Petroleo Hidratado",
                "Gas",
                "Otro (Detallar en notas)",
            ],
        )
    with col_t2:
        tipo_instalacion = st.selectbox(
            "Tipo de instalación",
            [
                "",
                "Pozo",
                "Linea de conduccion",
                "Ducto",
                "Tanque",
                "Separador",
                "Free-Water",
                "Planta",
                "Batería",
            ],
        )
        causa_inmediata = st.selectbox(
            "Causa inmediata",
            [
                "",
                "Corrosion",
                "Falla de Material",
                "Error de operación",
                "Falla en sistemas de control",
                "Sabotaje",
                "Fuerza Mayor",
            ],
        )

    # -----------------------
    # Volúmenes y área
    # -----------------------
    st.markdown("### Volúmenes y área afectada")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        volumen_bruto_m3 = st.number_input("Volumen bruto (m³)", min_value=0.0, step=0.1)
        volumen_crudo_m3 = st.number_input("Volumen de crudo (m³)", min_value=0.0, step=0.1)
    with col_v2:
        volumen_gas_m3 = st.number_input("Volumen de gas (m³)", min_value=0.0, step=1.0)
        ppm_agua = st.text_input("PPM o % de agua")
    with col_v3:
        area_afectada_m2 = st.number_input("Área afectada (m²)", min_value=0.0, step=1.0)

    # -----------------------
    # Recursos afectados
    # -----------------------
    st.markdown("### Recursos afectados")
    recursos_sel = st.multiselect(
        "Recursos afectados",
        [
            "Contenido en recinto",
            "Instalaciones propias",
            "Suelo",
            "Aire",
            "Flora",
            "Curso de agua",
            "Agua subsuperficial",
            "Fauna",
        ],
    )
    recursos_afectados = "|".join(recursos_sel) if recursos_sel else None

    # -----------------------
    # Otros datos / notas
    # -----------------------
    st.markdown("### Otros datos / notas")
    causa_probable = st.text_input("Causa probable")
    responsable = st.text_input("Responsable")
    observaciones = st.text_area("Notas / observaciones")
    medidas_inmediatas = st.text_area("Medidas inmediatas adoptadas")

    fluido = st.text_input("Fluido", value="Petróleo + agua de formación")
    volumen_estimado_m3 = volumen_bruto_m3

    # -----------------------
    # Aprobación (opcional)
    # -----------------------
    st.markdown("### Aprobación (opcional)")

    col_a1a, col_a1b = st.columns(2)
    with col_a1a:
        aprobador_apellido = st.text_input("Aprobador - Apellido")
    with col_a1b:
        aprobador_nombre = st.text_input("Aprobador - Nombre")

    col_a2a, col_a2b = st.columns(2)
    with col_a2a:
        fecha_aprob = st.date_input("Fecha aprobación", value=date.today())
    with col_a2b:
        hora_aprob = st.time_input(
            "Hora aprobación",
            value=datetime.now().time().replace(microsecond=0),
        )

    fecha_hora_aprobacion = (
        datetime.combine(fecha_aprob, hora_aprob)
        if (aprobador_apellido or aprobador_nombre)
        else None
    )

    # -----------------------
    # Fotos ANTES
    # -----------------------
    st.subheader("📸 Fotos del incidente (ANTES)")
    fotos = st.file_uploader(
        "Subir fotos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    # -----------------------
    # Botón GUARDAR
    # -----------------------
    btn_guardar = st.button("Guardar IADE")

    if btn_guardar:
        if not nombre_instalacion or not creado_por:
            st.error("❌ Nombre de la instalación y Usuario son obligatorios.")
        else:
            try:
                # Inserción en DB
                mie_id, codigo = insertar_mie(
                    drm=drm,
                    pozo=nombre_instalacion,
                    locacion=(f"{yacimiento or ''} - {zona or ''}").strip(" -"),
                    fluido=fluido,
                    volumen_estimado_m3=volumen_estimado_m3,
                    causa_probable=causa_probable,
                    responsable=responsable,
                    observaciones=observaciones,
                    creado_por=creado_por,
                    fecha_hora_evento=fecha_hora_evento,
                    observador_apellido=observador_apellido or None,
                    observador_nombre=observador_nombre or None,
                    responsable_inst_apellido=responsable_inst_apellido or None,
                    responsable_inst_nombre=responsable_inst_nombre or None,
                    yacimiento=yacimiento or None,
                    zona=zona or None,
                    nombre_instalacion=nombre_instalacion or None,
                    latitud=latitud or None,
                    longitud=longitud or None,
                    tipo_afectacion=tipo_afectacion or None,
                    tipo_derrame=tipo_derrame or None,
                    tipo_instalacion=tipo_instalacion or None,
                    causa_inmediata=causa_inmediata or None,
                    volumen_bruto_m3=volumen_bruto_m3,
                    volumen_gas_m3=volumen_gas_m3,
                    ppm_agua=ppm_agua or None,
                    volumen_crudo_m3=volumen_crudo_m3,
                    area_afectada_m2=area_afectada_m2,
                    recursos_afectados=recursos_afectados,
                    medidas_inmediatas=medidas_inmediatas or None,
                    aprobador_apellido=aprobador_apellido or None,
                    aprobador_nombre=aprobador_nombre or None,
                    fecha_hora_aprobacion=fecha_hora_aprobacion,
                )

                st.success(f"✅ IADE guardado. CÓDIGO: {codigo}")

                # Fotos ANTES
                if fotos:
                    for archivo in fotos:
                        nombre_destino = (
                            f"{codigo}/ANTES/"
                            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
                        )
                        blob_name = subir_foto_a_bucket(archivo, nombre_destino)
                        insertar_foto(mie_id, "ANTES", blob_name)

                st.session_state["ultimo_mie_id"] = mie_id
                st.session_state["ultimo_codigo_mie"] = codigo

            except Exception as e:
                st.error(f"⚠️ Error guardando IADE: {e}")

    # ==================================================
    #  PDF del último IADE
    # ==================================================
    st.markdown("### 📄 Generar PDF del último IADE")

    if "ultimo_mie_id" not in st.session_state:
        st.info("Guardá un IADE para generar el PDF.")
    else:
        mie_id_envio = st.session_state["ultimo_mie_id"]

        try:
            detalle_envio = obtener_mie_detalle(mie_id_envio)
            fotos_envio = obtener_fotos_mie(mie_id_envio)
            pdf_bytes = generar_mie_pdf(detalle_envio, fotos_envio)
        except Exception as e:
            st.error(f"⚠️ Error generando PDF: {e}")
        else:
            nombre_inst = getattr(detalle_envio, "nombre_instalacion", "") or detalle_envio.pozo
            file_name = f"{detalle_envio.codigo_mie} - {nombre_inst}.pdf"

            st.download_button(
                "📄 Descargar PDF IADE",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
            )

# =======================================================
#  MODO 2 - HISTORIAL IADE
# =======================================================
else:
    st.header("Historial de IADE")

    registros = listar_mie()

    if not registros:
        st.info("No hay IADE registrados.")
    else:

        opciones = {}
        for r in registros:
            nombre = getattr(r, "nombre_instalacion", None) or r.pozo or "(sin instalación)"
            label = f"{r.codigo_mie} - {nombre} ({r.estado})"
            opciones[label] = r.mie_id

        seleccion = st.selectbox("Seleccionar IADE", list(opciones.keys()))
        mie_id = opciones[seleccion]

        detalle = obtener_mie_detalle(mie_id)
        fotos = obtener_fotos_mie(mie_id)

        st.subheader("📄 Datos del IADE")

        # ----- Datos básicos -----
        st.markdown("### Datos básicos del incidente")
        colb1, colb2 = st.columns(2)
        with colb1:
            st.text_input(
                "Número de incidente / DRM",
                detalle.drm or "",
                disabled=True,
            )
        with colb2:
            st.text_input(
                "Usuario que carga el IADE",
                detalle.creado_por or "",
                disabled=True,
            )

        colf1, colf2 = st.columns(2)
        with colf1:
            st.text_input(
                "Fecha del evento",
                str(detalle.fecha_hora_evento or ""),
                disabled=True,
            )
        with colf2:
            st.text_input(
                "Fecha de carga",
                str(detalle.fecha_creacion_registro or ""),
                disabled=True,
            )

        # ----- Personas involucradas -----
        st.markdown("### Personas involucradas")

        colp1a, colp1b = st.columns(2)
        with colp1a:
            st.text_input(
                "Observador - Apellido",
                getattr(detalle, "observador_apellido", "") or "",
                disabled=True,
            )
        with colp1b:
            st.text_input(
                "Observador - Nombre",
                getattr(detalle, "observador_nombre", "") or "",
                disabled=True,
            )

        colp2a, colp2b = st.columns(2)
        with colp2a:
            st.text_input(
                "Responsable de la instalación - Apellido",
                getattr(detalle, "responsable_inst_apellido", "") or "",
                disabled=True,
            )
        with colp2b:
            st.text_input(
                "Responsable de la instalación - Nombre",
                getattr(detalle, "responsable_inst_nombre", "") or "",
                disabled=True,
            )

        # ----- Ubicación / instalación -----
        st.markdown("### Ubicación / instalación")
        colu1, colu2, colu3 = st.columns(3)
        with colu1:
            st.text_input(
                "Yacimiento",
                getattr(detalle, "yacimiento", "") or "",
                disabled=True,
            )
        with colu2:
            st.text_input(
                "Zona",
                getattr(detalle, "zona", "") or "",
                disabled=True,
            )
        with colu3:
            st.text_input(
                "Nombre de la instalación",
                getattr(detalle, "nombre_instalacion", "") or "",
                disabled=True,
            )

        coll1, coll2 = st.columns(2)
        with coll1:
            st.text_input(
                "Latitud",
                getattr(detalle, "latitud", "") or "",
                disabled=True,
            )
        with coll2:
            st.text_input(
                "Longitud",
                getattr(detalle, "longitud", "") or "",
                disabled=True,
            )

        # ----- Características del evento -----
        st.markdown("### Características del evento")
        colc1, colc2 = st.columns(2)
        with colc1:
            st.text_input(
                "Tipo de afectación",
                getattr(detalle, "tipo_afectacion", "") or "",
                disabled=True,
            )
            st.text_input(
                "Tipo de derrame",
                getattr(detalle, "tipo_derrame", "") or "",
                disabled=True,
            )
        with colc2:
            st.text_input(
                "Tipo de instalación",
                getattr(detalle, "tipo_instalacion", "") or "",
                disabled=True,
            )
            st.text_input(
                "Causa inmediata",
                getattr(detalle, "causa_inmediata", "") or "",
                disabled=True,
            )

        # ----- Volúmenes y área afectada -----
        st.markdown("### Volúmenes y área afectada")
        colv1, colv2, colv3 = st.columns(3)
        with colv1:
            st.text_input(
                "Volumen bruto (m³)",
                str(getattr(detalle, "volumen_bruto_m3", "") or ""),
                disabled=True,
            )
            st.text_input(
                "Volumen de crudo (m³)",
                str(getattr(detalle, "volumen_crudo_m3", "") or ""),
                disabled=True,
            )
        with colv2:
            st.text_input(
                "Volumen de gas (m³)",
                str(getattr(detalle, "volumen_gas_m3", "") or ""),
                disabled=True,
            )
            st.text_input(
                "PPM o % de agua",
                getattr(detalle, "ppm_agua", "") or "",
                disabled=True,
            )
        with colv3:
            st.text_input(
                "Área afectada (m²)",
                str(getattr(detalle, "area_afectada_m2", "") or ""),
                disabled=True,
            )

        # ----- Recursos afectados -----
        st.markdown("### Recursos afectados")
        st.text_area(
            "Recursos afectados",
            getattr(detalle, "recursos_afectados", "") or "",
            disabled=True,
        )

        # ----- Otros datos / notas -----
        st.markdown("### Otros datos / notas")
        coln1, coln2 = st.columns(2)
        with coln1:
            st.text_input(
                "Causa probable",
                detalle.causa_probable or "",
                disabled=True,
            )
        with coln2:
            st.text_input(
                "Responsable",
                detalle.responsable or "",
                disabled=True,
            )

        st.text_area(
            "Notas / Observaciones",
            detalle.observaciones or "",
            disabled=True,
        )

        st.text_area(
            "Medidas inmediatas adoptadas",
            getattr(detalle, "medidas_inmediatas", "") or "",
            disabled=True,
        )

        # ----- Aprobación -----
        st.markdown("### Aprobación")
        cola1, cola2 = st.columns(2)
        with cola1:
            st.text_input(
                "Aprobador - Apellido",
                getattr(detalle, "aprobador_apellido", "") or "",
                disabled=True,
            )
            st.text_input(
                "Aprobador - Nombre",
                getattr(detalle, "aprobador_nombre", "") or "",
                disabled=True,
            )
        with cola2:
            st.text_input(
                "Fecha y hora aprobación",
                str(getattr(detalle, "fecha_hora_aprobacion", "") or ""),
                disabled=True,
            )

        # ---------------------------------------------------
        # FOTOS ANTES / DESPUÉS
        # ---------------------------------------------------
        st.subheader("📸 Fotos asociadas")

        fotos_antes = [f for f in fotos if f["tipo"] == "ANTES"]
        fotos_despues = [f for f in fotos if f["tipo"] == "DESPUES"]

        if fotos_antes:
            st.markdown("#### Fotos del incidente (ANTES)")
            for f in fotos_antes:
                st.markdown(f"**{f['fecha_hora']}**")
                st.image(f["data"], use_container_width=True)

        if fotos_despues:
            st.markdown("#### Fotos de remediación (DESPUÉS)")
            for f in fotos_despues:
                st.markdown(f"**{f['fecha_hora']}**")
                st.image(f["data"], use_container_width=True)

        # ---------------------------------------------------
        # BLOQUE DE REMEDIACIÓN
        # ---------------------------------------------------
        if detalle.estado == "CERRADO":
            st.subheader("✅ Datos de remediación")

            # Campos remediación
            fecha_fin = getattr(detalle, "rem_fecha_fin_saneamiento", None)
            if not fecha_fin:
                fecha_fin = getattr(detalle, "rem_fecha", None)

            vol_tierra = getattr(detalle, "rem_volumen_tierra_levantada", None)
            destino_tierra = getattr(detalle, "rem_destino_tierra_impactada", None)
            vol_liquido = getattr(detalle, "rem_volumen_liquido_recuperado", None)
            comentarios = (
                getattr(detalle, "rem_comentarios", None)
                or getattr(detalle, "rem_detalle", None)
            )
            aprob_ap = getattr(detalle, "rem_aprobador_apellido", "")
            aprob_no = getattr(detalle, "rem_aprobador_nombre", "")

            st.write(f"**Fecha fin saneamiento:** {fecha_fin or '-'}")
            st.write(f"**Volumen tierra levantada (m³):** {vol_tierra or '-'}")
            st.write(f"**Destino tierra impactada:** {destino_tierra or '-'}")
            st.write(f"**Volumen líquido recuperado (m³):** {vol_liquido or '-'}")
            st.write("**Comentarios:**")
            st.write(comentarios or "-")
            st.write(f"**Aprobador final:** {aprob_ap} {aprob_no}")

            st.success("Este IADE ya está CERRADO.")

            # ---------------------------------------------------
            # PDF FINAL DESDE HISTORIAL
            # ---------------------------------------------------
            st.subheader("📄 Generar PDF de este IADE")

            try:
                pdf_bytes_hist = generar_mie_pdf(detalle, fotos)
            except Exception as e:
                st.error(f"⚠️ Error generando PDF: {e}")
            else:
                nombre_inst = (
                    getattr(detalle, "nombre_instalacion", None)
                    or detalle.pozo
                    or ""
                ).strip()

                file_name_hist = (
                    f"{detalle.codigo_mie} - {nombre_inst}.pdf"
                    if nombre_inst
                    else f"{detalle.codigo_mie}.pdf"
                )

                st.download_button(
                    "📄 Descargar PDF de este IADE",
                    data=pdf_bytes_hist,
                    file_name=file_name_hist,
                    mime="application/pdf",
                )

        # ---------------------------------------------------
        # FORMULARIO PARA CERRAR (si aún está abierto)
        # ---------------------------------------------------
        else:
            st.subheader("🛠️ Cargar datos de remediación y CERRAR IADE")

            # Fecha fin saneamiento
            colr1, colr2 = st.columns(2)
            with colr1:
                fecha_fin = st.date_input(
                    "Fecha finalización saneamiento",
                    datetime.now().date(),
                    key=f"rem_fecha_{mie_id}",
                )
            with colr2:
                hora_fin = st.time_input(
                    "Hora finalización",
                    datetime.now().time(),
                    key=f"rem_hora_{mie_id}",
                )

            fecha_fin_dt = datetime.combine(fecha_fin, hora_fin)

            # Volúmenes
            colv1r, colv2r = st.columns(2)
            with colv1r:
                vol_tierra = st.number_input(
                    "Volumen tierra levantada (m³)",
                    min_value=0.0,
                    step=0.1,
                    key=f"vol_tierra_{mie_id}",
                )
            with colv2r:
                vol_liquido = st.number_input(
                    "Volumen líquido recuperado (m³)",
                    min_value=0.0,
                    step=0.1,
                    key=f"vol_liq_{mie_id}",
                )

            destino_tierra = st.text_input(
                "Destino tierra impactada",
                key=f"destino_{mie_id}",
            )

            comentarios = st.text_area(
                "Comentarios de remediación",
                key=f"coment_{mie_id}",
            )

            colap1, colap2 = st.columns(2)
            with colap1:
                aprob_ap = st.text_input(
                    "Aprobador final - Apellido",
                    key=f"ap_ap_{mie_id}",
                )
            with colap2:
                aprob_no = st.text_input(
                    "Aprobador final - Nombre",
                    key=f"ap_no_{mie_id}",
                )

            # Fotos DESPUÉS
            st.markdown("### 📸 Fotos DESPUÉS del Saneamiento")
            fotos_despues = st.file_uploader(
                "Subir fotos",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"fotos_desp_{mie_id}",
            )

            # Botón cerrar
            if st.button(
                "✔️ Guardar remediación y CERRAR IADE",
                key=f"btn_cerrar_{mie_id}",
            ):
                try:
                    cerrar_mie_con_remediacion(
                        mie_id,
                        fecha_fin_dt,
                        vol_tierra,
                        destino_tierra,
                        vol_liquido,
                        comentarios,
                        aprob_ap,
                        aprob_no,
                    )

                    # Guardar fotos DESPUÉS
                    if fotos_despues:
                        codigo = detalle.codigo_mie
                        for archivo in fotos_despues:
                            nombre_destino = (
                                f"{codigo}/DESPUES/"
                                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
                            )
                            blob_name = subir_foto_a_bucket(archivo, nombre_destino)
                            insertar_foto(mie_id, "DESPUES", blob_name)

                    st.success("IADE cerrado exitosamente.")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al cerrar IADE: {e}")


# =======================================================
#  MODO 3 - EXPORTAR IADE A EXCEL
# =======================================================
elif modo == "Exportar IADE":
    st.header("Exportar base de IADE a Excel")

    st.markdown(
        """
        Esta opción exporta la tabla **mie_eventos** completa (sin fotos)
        a un archivo Excel `.xlsx` para análisis o auditoría.
        """
    )

    if st.button("Generar archivo Excel"):
        try:
            registros = obtener_todos_mie()

            if not registros:
                st.info("No hay registros de IADE para exportar.")
            else:
                # BigQuery Row -> dict -> DataFrame
                filas = [dict(r) for r in registros]
                df = pd.DataFrame(filas)

                # Generar Excel en memoria
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="IADE")

                buffer.seek(0)

                nombre_archivo = (
                    f"IADE_mie_eventos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                )

                st.download_button(
                    "📥 Descargar Excel",
                    data=buffer,
                    file_name=nombre_archivo,
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                )

        except Exception as e:
            st.error(f"❌ Error al generar la exportación: {e}")











