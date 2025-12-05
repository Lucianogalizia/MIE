import streamlit as st
from datetime import datetime, date
from io import BytesIO
import pandas as pd
import plotly.graph_objects as go

# ==========================
# CSS CORPORATIVO
# ==========================
st.markdown("""
<style>

    /* --- Fondo general --- */
    .main {
        background-color: #F5F5F7 !important;
    }

    /* --- Títulos principales --- */
    h1, h2, h3 {
        color: #003366 !important;    /* Azul petróleo corporativo */
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }

    /* --- Subtítulos --- */
    h4, h5 {
        color: #144877 !important;
        font-weight: 600 !important;
    }

    /* --- Divider estilo auditoría --- */
    hr {
        border: 0;
        height: 2px;
        background: linear-gradient(to right, #003366, #005599, #003366);
        margin-top: 20px;
        margin-bottom: 20px;
    }

    /* --- Métricas (st.metric) --- */
    div[data-testid="metric-container"] {
        background: #FFFFFF;
        padding: 15px 20px;
        border-radius: 12px;
        border-left: 5px solid #005599;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.10);
        margin-bottom: 20px;
    }

    /* Valor del metric */
    div[data-testid="metric-container"] > div:nth-child(2) {
        color: #003366 !important;
        font-size: 24px !important;
        font-weight: 700 !important;
    }

    /* Texto del metric */
    div[data-testid="metric-container"] > label {
        color: #003366 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }

    /* Delta del metric */
    div[data-testid="metric-container"] svg {
        color: #008000 !important;
    }

    /* --- Selectores (dropdowns) --- */
    .stSelectbox div[role="combobox"] {
        background-color: #ffffff !important;
        border: 1px solid #888 !important;
        border-radius: 8px !important;
        padding: 5px !important;
    }

    /* --- Input de fechas --- */
    .stDateInput input {
        border-radius: 8px !important;
        border: 1px solid #666 !important;
    }

    /* --- Tablas internas --- */
    table {
        border-collapse: collapse !important;
        width: 100% !important;
        background: #FFFFFF !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
    }

    thead tr {
        background-color: #003366 !important;
        color: white !important;
    }

    tbody tr:nth-child(even) {
        background-color: #F2F5F9 !important;
    }

    tbody tr:hover {
        background-color: #e6f0ff !important;
    }

    /* --- Gráficos --- */
    img {
        border-radius: 10px !important;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.15) !important;
    }

</style>
""", unsafe_allow_html=True)

# ==========================
#  LOGIN SIMPLE POR CONTRASEÑA
# ==========================
APP_PASSWORD = "MIE2025"  # 🔐 cambiala por la que quieras

if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

if not st.session_state["auth_ok"]:
    st.title("Ingreso a Módulo IADE / MIE")

    pwd = st.text_input("Contraseña", type="password")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("Ingresar"):
            if pwd == APP_PASSWORD:
                st.session_state["auth_ok"] = True
                st.success("Acceso concedido.")
                st.experimental_rerun()
            else:
                st.error("Contraseña incorrecta.")

    st.stop()  # ⛔ no sigue cargando la app si no está autenticado

# Si llegó acá, está autenticado
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
    ["Nuevo IADE", "Historial", "Estadísticas", "Exportar IADE"]
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
elif modo == "Historial":
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
#  MODO 2.5 - ESTADISTICAS
# =======================================================

elif modo == "Estadísticas":
    st.header("Estadísticas de IADE")

    # ==========================
    # 1) Cargar datos completos
    # ==========================
    from mie_backend import obtener_todos_mie
    import pandas as pd

    registros = obtener_todos_mie()
    if not registros:
        st.info("No hay IADE registrados para generar estadísticas.")
        st.stop()

    # Convertir a DataFrame
    df = pd.DataFrame([dict(r) for r in registros])

    # Asegurar fechas sin timezone
    for col in ["fecha_hora_evento", "fecha_creacion_registro", "rem_fecha_fin_saneamiento"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True).dt.tz_localize(None)

    # ==========================
    # 2) Filtros globales
    # ==========================
    st.subheader("Filtros")

    col_f1, col_f2 = st.columns(2)

    min_fecha = df["fecha_hora_evento"].min()
    max_fecha = df["fecha_hora_evento"].max()

    with col_f1:
        fecha_desde, fecha_hasta = st.date_input(
            "Rango de fechas del evento",
            value=(min_fecha.date(), max_fecha.date()),
        )

    with col_f2:
        yacimientos = sorted(df["yacimiento"].dropna().unique()) if "yacimiento" in df.columns else []
        zonas = sorted(df["zona"].dropna().unique()) if "zona" in df.columns else []
        tipos_inst = sorted(df["tipo_instalacion"].dropna().unique()) if "tipo_instalacion" in df.columns else []
        estados = sorted(df["estado"].dropna().unique()) if "estado" in df.columns else []

    col_ff3, col_ff4, col_ff5 = st.columns(3)

    with col_ff3:
        yac_sel = st.selectbox("Yacimiento", ["(Todos)"] + yacimientos)

    with col_ff4:
        zona_sel = st.selectbox("Zona", ["(Todos)"] + zonas)

    with col_ff5:
        tipo_inst_sel = st.selectbox("Tipo de instalación", ["(Todos)"] + tipos_inst)

    estado_sel = st.selectbox("Estado del IADE", ["(Todos)"] + estados)

    # Aplicar filtros
    df_filt = df.copy()

    df_filt = df_filt[
        (df_filt["fecha_hora_evento"].dt.date >= fecha_desde) &
        (df_filt["fecha_hora_evento"].dt.date <= fecha_hasta)
    ]

    if yac_sel != "(Todos)":
        df_filt = df_filt[df_filt["yacimiento"] == yac_sel]

    if zona_sel != "(Todos)":
        df_filt = df_filt[df_filt["zona"] == zona_sel]

    if tipo_inst_sel != "(Todos)":
        df_filt = df_filt[df_filt["tipo_instalacion"] == tipo_inst_sel]

    if estado_sel != "(Todos)":
        df_filt = df_filt[df_filt["estado"] == estado_sel]

    if df_filt.empty:
        st.warning("No hay IADE que coincidan con los filtros seleccionados.")
        st.stop()

    # ============================================================
    # 3) DASHBOARD EJECUTIVO (solo métricas clave)
    # ============================================================
    st.subheader("📊 Dashboard Ejecutivo (IADE)")

    # MÉTRICAS BASE
    total_iade = len(df_filt)
    abiertos = len(df_filt[df_filt["estado"] == "ABIERTO"])
    cerrados = len(df_filt[df_filt["estado"] == "CERRADO"])

    # TIEMPO PROMEDIO DE CIERRE
    df_cerrados = df_filt.dropna(subset=["rem_fecha_fin_saneamiento"])
    if not df_cerrados.empty:
        df_cerrados["dias_cierre"] = (
            df_cerrados["rem_fecha_fin_saneamiento"] - df_cerrados["fecha_hora_evento"]
        ).dt.days
        promedio_cierre = round(df_cerrados["dias_cierre"].mean(), 1)
    else:
        promedio_cierre = "—"

    # VOLUMEN ACTIVO Y REMEDIADO
    volumen_activo = df_filt[df_filt["estado"] == "ABIERTO"]["volumen_estimado_m3"].sum()
    volumen_remediado = (
        df_filt["rem_volumen_liquido_recuperado"].fillna(0)
        + df_filt["rem_volumen_tierra_levantada"].fillna(0)
    ).sum()

    # MAGNITUD
    df_mag = df_filt["magnitud"].value_counts().to_dict()
    n1 = df_mag.get("N1", 0)
    n2 = df_mag.get("N2", 0)
    n3 = df_mag.get("N3", 0)

    def pct(v): return f"{(v / total_iade * 100):.1f}%" if total_iade > 0 else "0%"

    # -------- Fila 1 --------
    col1, col2, col3 = st.columns(3)
    col1.metric("IADE Totales", total_iade)
    col2.metric("IADE Abiertos", abiertos)
    col3.metric("IADE Cerrados", cerrados)

    # -------- Fila 2 --------
    col4, col5, col6 = st.columns(3)
    col4.metric("⏱️ Tiempo promedio de cierre (días)", promedio_cierre)
    col5.metric("🛢️ Volumen activo (m³)", round(volumen_activo, 2))
    col6.metric("♻️ Volumen remediado total (m³)", round(volumen_remediado, 2))

    st.divider()

    # -------- Magnitud --------
    st.subheader("Distribución por Magnitud del Evento")
    st.write(
        f"""
        **N1:** {n1} ({pct(n1)})  
        **N2:** {n2} ({pct(n2)})  
        **N3:** {n3} ({pct(n3)})  
        """
    )

    st.divider()

    # ============================================================
    # 4) GRÁFICOS Y DISTRIBUCIONES (versión Plotly)
    # ============================================================
    import plotly.graph_objects as go
    import plotly.express as px

    # --------------------------
    # Evolución mensual
    # --------------------------
    st.subheader("Evolución de IADE por mes")

    if "fecha_hora_evento" in df_filt.columns:
        df_tmp = df_filt.copy()
        df_tmp["mes"] = (
            df_tmp["fecha_hora_evento"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

        # Totales por mes
        df_mes_total = (
            df_tmp
            .groupby("mes")
            .size()
            .reset_index(name="total_iade")
            .sort_values("mes")
        )

        # Cerrados por mes
        if "estado" in df_tmp.columns:
            df_cerr_tmp = df_tmp[df_tmp["estado"] == "CERRADO"].copy()
            if not df_cerr_tmp.empty:
                df_cerr_tmp["mes"] = (
                    df_cerr_tmp["fecha_hora_evento"]
                    .dt.to_period("M")
                    .dt.to_timestamp()
                )
                df_mes_cerr = (
                    df_cerr_tmp
                    .groupby("mes")
                    .size()
                    .reset_index(name="cerrados_iade")
                )
            else:
                df_mes_cerr = df_mes_total[["mes"]].copy()
                df_mes_cerr["cerrados_iade"] = 0
        else:
            df_mes_cerr = df_mes_total[["mes"]].copy()
            df_mes_cerr["cerrados_iade"] = 0

        df_evo = df_mes_total.merge(df_mes_cerr, on="mes", how="left").fillna(0)
        df_evo["mes_str"] = df_evo["mes"].dt.strftime("%Y-%m")

        fig = go.Figure()

        # Barras: IADE totales
        fig.add_trace(go.Bar(
            x=df_evo["mes_str"],
            y=df_evo["total_iade"],
            name="IADE totales"
        ))

        # Línea: IADE cerrados
        fig.add_trace(go.Scatter(
            x=df_evo["mes_str"],
            y=df_evo["cerrados_iade"],
            mode="lines+markers+text",
            name="IADE cerrados",
            text=df_evo["cerrados_iade"],
            textposition="top center"
        ))

        fig.update_layout(
            title="IADE totales y cerrados por mes",
            xaxis_title="Mes",
            yaxis_title="Cantidad de IADE",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=40, r=20, t=60, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No se encontró la columna 'fecha_hora_evento' para graficar evolución mensual.")

    # --------------------------
    # IADE por yacimiento
    # --------------------------
    st.subheader("Distribución de IADE por Yacimiento")

    if "yacimiento" in df_filt.columns:
        df_yac = (
            df_filt
            .groupby("yacimiento")
            .size()
            .reset_index(name="cantidad")
            .sort_values("cantidad", ascending=False)
        )

        if not df_yac.empty:
            fig_yac = px.bar(
                df_yac,
                x="cantidad",
                y="yacimiento",
                orientation="h",
                title="IADE por Yacimiento",
                labels={"cantidad": "Cantidad de IADE", "yacimiento": "Yacimiento"},
            )
            fig_yac.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=60, b=40))
            st.plotly_chart(fig_yac, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por yacimiento.")
    else:
        st.info("No se encontró la columna 'yacimiento'.")

    # --------------------------
    # IADE por tipo de instalación
    # --------------------------
    st.subheader("Distribución de IADE por Tipo de Instalación")

    if "tipo_instalacion" in df_filt.columns:
        df_inst = (
            df_filt
            .groupby("tipo_instalacion")
            .size()
            .reset_index(name="cantidad")
            .sort_values("cantidad", ascending=False)
        )

        if not df_inst.empty:
            fig_inst = px.bar(
                df_inst,
                x="tipo_instalacion",
                y="cantidad",
                title="IADE por Tipo de Instalación",
                labels={"cantidad": "Cantidad de IADE", "tipo_instalacion": "Tipo de Instalación"},
            )
            fig_inst.update_layout(
                template="plotly_white",
                xaxis_tickangle=-30,
                margin=dict(l=40, r=20, t=60, b=80),
            )
            st.plotly_chart(fig_inst, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por tipo de instalación.")
    else:
        st.info("No se encontró la columna 'tipo_instalacion'.")

    # --------------------------
    # IADE por causa inmediata
    # --------------------------
    st.subheader("Distribución de IADE por Causa Inmediata")

    if "causa_inmediata" in df_filt.columns:
        df_causa = (
            df_filt
            .groupby("causa_inmediata")
            .size()
            .reset_index(name="cantidad")
            .sort_values("cantidad", ascending=False)
        )

        if not df_causa.empty:
            fig_causa = px.bar(
                df_causa,
                x="causa_inmediata",
                y="cantidad",
                title="IADE por Causa Inmediata",
                labels={"cantidad": "Cantidad de IADE", "causa_inmediata": "Causa Inmediata"},
            )
            fig_causa.update_layout(
                template="plotly_white",
                xaxis_tickangle=-30,
                margin=dict(l=40, r=20, t=60, b=80),
            )
            st.plotly_chart(fig_causa, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por causa inmediata.")
    else:
        st.info("No se encontró la columna 'causa_inmediata'.")

    # --------------------------
    # IADE por tipo de afectación
    # --------------------------
    st.subheader("Distribución de IADE por Tipo de Afectación")

    if "tipo_afectacion" in df_filt.columns:
        df_afec = (
            df_filt
            .groupby("tipo_afectacion")
            .size()
            .reset_index(name="cantidad")
            .sort_values("cantidad", ascending=False)
        )

        if not df_afec.empty:
            fig_afec = px.bar(
                df_afec,
                x="tipo_afectacion",
                y="cantidad",
                title="IADE por Tipo de Afectación",
                labels={"cantidad": "Cantidad de IADE", "tipo_afectacion": "Tipo de Afectación"},
            )
            fig_afec.update_layout(
                template="plotly_white",
                xaxis_tickangle=-30,
                margin=dict(l=40, r=20, t=60, b=80),
            )
            st.plotly_chart(fig_afec, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por tipo de afectación.")
    else:
        st.info("No se encontró la columna 'tipo_afectacion'.")

    # --------------------------
    # IADE por tipo de derrame
    # --------------------------
    st.subheader("Distribución de IADE por Tipo de Derrame")

    if "tipo_derrame" in df_filt.columns:
        df_der = (
            df_filt
            .groupby("tipo_derrame")
            .size()
            .reset_index(name="cantidad")
            .sort_values("cantidad", ascending=False)
        )

        if not df_der.empty:
            fig_der = px.bar(
                df_der,
                x="tipo_derrame",
                y="cantidad",
                title="IADE por Tipo de Derrame",
                labels={"cantidad": "Cantidad de IADE", "tipo_derrame": "Tipo de Derrame"},
            )
            fig_der.update_layout(
                template="plotly_white",
                xaxis_tickangle=-30,
                margin=dict(l=40, r=20, t=60, b=80),
            )
            st.plotly_chart(fig_der, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por tipo de derrame.")
    else:
        st.info("No se encontró la columna 'tipo_derrame'.")


            


# =======================================================
#  MODO 3 - EXPORTAR IADE A EXCEL
# =======================================================
elif modo == "Exportar IADE":
    st.header("Exportar base completa de IADE")

    st.markdown("""
    Esta opción exporta la tabla **mie_eventos** completa (sin fotos)
    en un archivo Excel `.xlsx` para auditoría o análisis.
    """)

    if st.button("Generar archivo Excel"):
        try:
            from io import BytesIO
            import pandas as pd
            from datetime import datetime
            from mie_backend import obtener_todos_mie

            registros = obtener_todos_mie()

            if not registros:
                st.info("No existen registros de IADE para exportar.")
            else:
                # Convertimos filas a DataFrame
                filas = [dict(r) for r in registros]
                df = pd.DataFrame(filas)

                # 🔥🔥🔥 FIX: Excel no acepta timezone → convertimos todas las columnas datetime
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = pd.to_datetime(df[col], utc=True).dt.tz_localize(None)

                # Generar Excel
                buffer = BytesIO()

                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="IADE")

                buffer.seek(0)

                nombre_archivo = (
                    f"IADE_mie_eventos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                )

                st.download_button(
                    "📥 Descargar Excel",
                    data=buffer,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        except Exception as e:
            st.error(f"❌ Error al generar la exportación: {e}")














