import streamlit as st
from datetime import datetime, date, time

from mie_backend import (
    insertar_mie,
    insertar_foto,
    subir_foto_a_bucket,
    listar_mie,
    obtener_mie_detalle,
    obtener_fotos_mie,
    actualizar_mie_basico,
    cerrar_mie_con_remediacion,
)

st.set_page_config(page_title="MIE - Gestión de Derrames", layout="wide")

st.title("🛢️ Gestión de MIE (Derrames / DRM)")

modo = st.sidebar.radio("Modo", ["Nuevo MIE", "Historial"])


# =======================================================
#  MODO 1 - NUEVO MIE
# =======================================================
if modo == "Nuevo MIE":

    st.header("Registrar un nuevo MIE")

    # -----------------------
    # Fecha y hora del evento
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

    drm = st.text_input("Número de incidente / DRM")
    creado_por = st.text_input("Usuario que carga el MIE")

    # -----------------------
    # Personas involucradas
    # -----------------------
    st.markdown("### Personas involucradas")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        observador_apellido = st.text_input("Observador - Apellido")
        observador_nombre = st.text_input("Observador - Nombre")
    with col_p2:
        responsable_inst_apellido = st.text_input("Responsable de la instalación - Apellido")
        responsable_inst_nombre = st.text_input("Responsable de la instalación - Nombre")

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
            ["", "Agua de Produccion", "Petroleo Hidratado", "Gas", "Otro (Detallar en notas)"],
        )
    with col_t2:
        tipo_instalacion = st.selectbox(
            "Tipo de instalación",
            ["", "Pozo", "Linea de conduccion", "Ducto", "Tanque",
             "Separador", "Free-Water", "Planta", "Batería"],
        )
        causa_inmediata = st.selectbox(
            "Causa inmediata",
            ["", "Corrosion", "Falla de Material", "Error de operación",
             "Falla en sistemas de control", "Sabotaje", "Fuerza Mayor"],
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
    causa_probable = st.text_input("Causa probable (texto libre)")
    responsable = st.text_input("Responsable (texto libre)")
    observaciones = st.text_area("Notas / Observaciones adicionales")
    medidas_inmediatas = st.text_area("Medidas inmediatas adoptadas")

    # Para compatibilidad: fluido y volumen_estimado_m3 siguen existiendo
    fluido = st.text_input("Fluido", value="Petróleo + agua de formación")
    volumen_estimado_m3 = volumen_bruto_m3  # usamos el bruto como estimado

    # -----------------------
    # Aprobación (opcional)
    # -----------------------
    st.markdown("### Aprobación (opcional)")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        aprobador_apellido = st.text_input("Aprobador - Apellido")
        aprobador_nombre = st.text_input("Aprobador - Nombre")
    with col_a2:
        fecha_aprob = st.date_input("Fecha aprobación", value=date.today())
        hora_aprob = st.time_input(
            "Hora aprobación",
            value=datetime.now().time().replace(microsecond=0),
        )

    fecha_hora_aprobacion = None
    if aprobador_apellido or aprobador_nombre:
        fecha_hora_aprobacion = datetime.combine(fecha_aprob, hora_aprob)

    # -----------------------
    # Fotos ANTES
    # -----------------------
    st.subheader("📸 Fotos del derrame (ANTES)")
    fotos = st.file_uploader(
        "Subir una o más fotos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    btn_guardar = st.button("Guardar MIE")

    if btn_guardar:
        if not nombre_instalacion or not creado_por:
            st.error("❌ Nombre de la instalación y Usuario que carga son obligatorios.")
        else:
            # Compatibilidad con campos viejos:
            pozo = nombre_instalacion
            locacion = (f"{yacimiento or ''} - {zona or ''}").strip(" -") or None

            try:
                mie_id, codigo = insertar_mie(
                    drm=drm,
                    pozo=pozo,
                    locacion=locacion,
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
                    magnitud=None,  # después definimos cálculo
                    aviso_sen=None,
                    difusion_mediatica=None,
                    aviso_autoridad=None,
                    aviso_autoridad_fecha_hora=None,
                    aviso_autoridad_emisor=None,
                    aviso_autoridad_medio=None,
                    aviso_autoridad_organismo=None,
                    aviso_autoridad_contacto=None,
                    aviso_superficiario=None,
                    aviso_superficiario_fecha_hora=None,
                    aviso_superficiario_emisor=None,
                    aviso_superficiario_medio=None,
                    aviso_superficiario_organismo=None,
                    aviso_superficiario_contacto=None,
                    medidas_inmediatas=medidas_inmediatas or None,
                    aprobador_apellido=aprobador_apellido or None,
                    aprobador_nombre=aprobador_nombre or None,
                    fecha_hora_aprobacion=fecha_hora_aprobacion,
                )

                st.success(f"✅ MIE guardado. CÓDIGO: {codigo} (ID={mie_id})")

                if fotos:
                    for archivo in fotos:
                        nombre_destino = (
                            f"{codigo}/ANTES/"
                            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
                        )
                        blob_name = subir_foto_a_bucket(archivo, nombre_destino)
                        insertar_foto(mie_id, "ANTES", blob_name)

                    st.info(f"📁 Se guardaron {len(fotos)} fotos en la nube.")

                st.session_state["ultimo_mie_id"] = mie_id
                st.session_state["ultimo_codigo_mie"] = codigo

            except Exception as e:
                st.error(f"⚠️ Error guardando MIE: {e}")


# =======================================================
#  MODO 2 - HISTORIAL
# =======================================================
else:
    st.header("Historial de MIE")

    registros = listar_mie()

    if not registros:
        st.info("No hay MIE registrados todavía.")
    else:
        opciones = {}
        for r in registros:
            nombre = getattr(r, "nombre_instalacion", None) or r.pozo or "(sin instalación)"
            label = f"{r.codigo_mie} - {nombre} ({r.estado})"
            opciones[label] = r.mie_id

        seleccion = st.selectbox("Seleccionar MIE", list(opciones.keys()))
        mie_id = opciones[seleccion]


        detalle = obtener_mie_detalle(mie_id)
        fotos = obtener_fotos_mie(mie_id)

        # ---------------------------------------------------
        # DATOS EDITABLES DEL MIE
        # ---------------------------------------------------
        st.subheader("📄 Datos del MIE")

        col1, col2 = st.columns(2)

        with col1:
            drm_edit = st.text_input("DRM", detalle.drm)
            pozo_edit = st.text_input("Pozo", detalle.pozo)
            locacion_edit = st.text_input("Locación", detalle.locacion)
            fluido_edit = st.text_input("Fluido", detalle.fluido)
            volumen_edit = st.number_input(
                "Volumen estimado (m³)",
                min_value=0.0,
                step=0.1,
                value=float(detalle.volumen_estimado_m3 or 0.0),
            )

        with col2:
            causa_edit = st.text_input("Causa probable", detalle.causa_probable)
            responsable_edit = st.text_input("Responsable", detalle.responsable)
            observaciones_edit = st.text_area(
                "Observaciones adicionales",
                detalle.observaciones or "",
            )
            st.write(f"**Estado:** {detalle.estado}")
            st.write(f"**Creado por:** {detalle.creado_por}")
            st.write(f"**Fecha evento:** {detalle.fecha_hora_evento}")
            st.write(f"**Fecha carga:** {detalle.fecha_creacion_registro}")

        if st.button("💾 Guardar cambios del MIE"):
            actualizar_mie_basico(
                mie_id,
                drm_edit,
                pozo_edit,
                locacion_edit,
                fluido_edit,
                volumen_edit,
                causa_edit,
                responsable_edit,
                observaciones_edit,
            )
            st.success("Cambios guardados correctamente.")
            st.rerun()

        # ---------------------------------------------------
        # FOTOS (ANTES / DESPUÉS)
        # ---------------------------------------------------
        st.subheader("📸 Fotos asociadas")

        if not fotos:
            st.info("No hay fotos para este MIE.")
        else:
            for f in fotos:
                st.markdown(f"**{f['tipo']}** – {f['fecha_hora']}")
                st.image(f["data"], use_container_width=True)

        # ---------------------------------------------------
        # DATOS DE REMEDIACIÓN (mostrar cuando esté cerrado)
        # ---------------------------------------------------
        if detalle.estado == "CERRADO":
            st.subheader("✅ Datos de la remediación")

            rem_fecha = getattr(detalle, "rem_fecha", None)
            rem_responsable = getattr(detalle, "rem_responsable", None)
            rem_detalle = getattr(detalle, "rem_detalle", None)

            st.write(f"**Fecha remediación:** {rem_fecha or '-'}")
            st.write(f"**Responsable remediación:** {rem_responsable or '-'}")
            st.write("**Detalle:**")
            st.write(rem_detalle or "-")

            st.success("Este MIE ya está CERRADO.")

        # ---------------------------------------------------
        # FORMULARIO DE REMEDIACIÓN (solo si NO está cerrado)
        # ---------------------------------------------------
        else:
            st.subheader("🛠️ Cargar remediación del Derrame")

            colr1, colr2 = st.columns(2)

            with colr1:
                rem_fecha = st.date_input("Fecha de remediación", datetime.now())
                rem_hora = st.time_input("Hora", datetime.now().time())

            rem_fecha_final = datetime.combine(rem_fecha, rem_hora)
            rem_responsable = st.text_input("Responsable de remediación")
            rem_detalle = st.text_area("Detalle de la remediación")

            st.markdown("### 📸 Fotos DESPUÉS")
            fotos_despues = st.file_uploader(
                "Subir fotos después de la remediación",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
            )

            if st.button("✔️ Guardar remediación y CERRAR MIE"):
                try:
                    cerrar_mie_con_remediacion(
                        mie_id,
                        rem_fecha_final,
                        rem_responsable,
                        rem_detalle,
                    )

                    if fotos_despues:
                        codigo = detalle.codigo_mie
                        for archivo in fotos_despues:
                            nombre_destino = (
                                f"{codigo}/DESPUES/"
                                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
                            )
                            blob_name = subir_foto_a_bucket(archivo, nombre_destino)
                            insertar_foto(mie_id, "DESPUES", blob_name)

                    st.success("MIE cerrado exitosamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al cerrar el MIE: {e}")



