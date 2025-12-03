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

    col1, col2 = st.columns(2)

    with col1:
        drm = st.text_input("DRM / Código de incidente")
        pozo = st.text_input("Pozo")
        locacion = st.text_input("Locación")
        fluido = st.text_input("Fluido", value="Petróleo + agua de formación")
        volumen = st.number_input("Volumen estimado (m³)", min_value=0.0, step=0.1)

    with col2:
        causa_probable = st.text_input("Causa probable")
        responsable = st.text_input("Responsable / Supervisor")
        creado_por = st.text_input("Usuario que carga el MIE")

        fecha_defecto = date.today()
        hora_defecto = datetime.now().time().replace(microsecond=0)

        fecha_evento = st.date_input("Fecha del evento", value=fecha_defecto)
        hora_evento = st.time_input("Hora del evento", value=hora_defecto)

        fecha_hora_evento = datetime.combine(fecha_evento, hora_evento)

    observaciones = st.text_area("Observaciones adicionales")

    st.subheader("📸 Fotos del derrame (ANTES)")
    fotos = st.file_uploader(
        "Subir una o más fotos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )

    btn_guardar = st.button("Guardar MIE")

    if btn_guardar:
        if not pozo or not locacion or not creado_por:
            st.error("❌ Pozo, Locación y Usuario que carga son obligatorios.")
        else:
            try:
                mie_id, codigo = insertar_mie(
                    drm=drm,
                    pozo=pozo,
                    locacion=locacion,
                    fluido=fluido,
                    volumen_estimado_m3=volumen,
                    causa_probable=causa_probable,
                    responsable=responsable,
                    observaciones=observaciones,
                    creado_por=creado_por,
                    fecha_hora_evento=fecha_hora_evento,
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
        opciones = {
            f"{r.codigo_mie} - {r.pozo} ({r.estado})": r.mie_id
            for r in registros
        }
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
            st.experimental_rerun()

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
        # REMEDIACIÓN (si no está cerrado)
        # ---------------------------------------------------
        if detalle.estado != "CERRADO":
            st.subheader("🛠️ Remediación del Derrame")

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
                accept_multiple_files=True
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
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error al cerrar el MIE: {e}")
        else:
            st.success("Este MIE ya está CERRADO.")



