# app_mie.py
import streamlit as st
from datetime import datetime, date, time
from io import BytesIO
import pandas as pd
import time
import json
import hashlib

# =======================================================
#   CONFIGURACIÓN GENERAL (DEBE IR ANTES DE CUALQUIER st.*)
# =======================================================
st.set_page_config(page_title="MIA - Módulo de Incidentes Ambientales", layout="wide")

# ==========================
#  HELPERS - PICK LIST HORAS
# ==========================
def _time_options(step_minutes=5):
    opts = []
    for h in range(24):
        for m in range(0, 60, step_minutes):
            opts.append(time(h, m))
    return opts

def _nearest_index(opts, t):
    best_i = 0
    best_diff = 10**9
    t_min = t.hour * 60 + t.minute
    for i, x in enumerate(opts):
        x_min = x.hour * 60 + x.minute
        diff = abs(x_min - t_min)
        if diff < best_diff:
            best_diff = diff
            best_i = i
    return best_i

HORAS_OPTS = _time_options(step_minutes=5)

# ==========================
#  LISTAS / PICKLISTS
# ==========================
USUARIOS_CARGA = [
    "Barros, Claudio",
    "Martinez, Cristian",
    "Muñoz, Hector",
    "Uribe, Fabian",
    "Lafeuillade, Geraldine",
    "Alessandrini, Eliana",
    "Orellana, Ramiro",
    "Zuñiga, Ricardo",
    "Vera, Enzo",
    "Michunovich, Alejo",
    "Moreno, Javier",
    "Momber, Joan",
    "Perriere, Gaston",
    "Segura, Eduardo",
    "Quiroga, Guillermo",
    "Millanahuel, Jonathan",
    "Reyna, Jonatan",
    "Fernandez, Bruno",
    "Soria, Gabriel",
    "Argumoza, Gaston",
    "Rodriguez, Diego",
    "Catrilaf, Ivana",
    "Escobar, Leonel",
    "Maza, Juan Carlos",
    "Oyarzo, Hector",
    "Arce, Gustavo",
    "Acuña, Martin",
    "Lescano, Federico",
    "Taboada, Christian",
]

APROBADORES = [
    "Oyarzo, Hector",
    "Arce, Gustavo",
    "Acuña, Martin",
    "Lescano, Federico",
    "Reyes, Pablo",
    "Taboada, Christian",
    "Sepulveda, Cristian",
]

# Mapa apellido -> nombre para autocompletar
APROBADORES_MAP = {
    "Oyarzo": "Hector",
    "Arce": "Gustavo",
    "Acuña": "Martin",
    "Lescano": "Federico",
    "Reyes": "Pablo",
    "Taboada": "Christian",
    "Sepulveda": "Cristian",
}

def _split_apellido_nombre(full: str):
    """Devuelve (Apellido, Nombre) desde 'Apellido, Nombre'."""
    if not full:
        return ("", "")
    if "," in full:
        a, n = full.split(",", 1)
        return (a.strip(), n.strip())
    return (full.strip(), "")

APROBADORES_APELLIDOS = [""] + sorted(list(APROBADORES_MAP.keys()))

# ==========================
#  PICKLISTS NUEVOS (ZONA / RESPONSABLE / EVENTO)
# ==========================
ZONAS_PICK = [
    "LH-CG",
    "CAÑADON LA ESCONDIDA 02",
    "CAÑADON LA ESCONDIDA 10",
    "BARRANCA BAYA",
    "PLANTA LH-03",
    "PLANTA CeN-10",
]

RESPONSABLES_PICK = [
    "Integridad",
    "Mantenimiento",
    "Ingeniería",
    "Operaciones (producción/planta)",
    "Seguridad",
]

TIPO_AFECTACION_PICK = [
    "Derrame menor",
    "Derrame mayor",
    "Emisión",
]

TIPO_DERRAME_PICK = [
    "Petróleo",
    "Petróleo + agua de formación",
    "Agua de formación",
    "Gases",
    "Químicos",
    "Derivados de hidrocarburo (aceites, gas oil, etc)",
]

TIPO_INSTALACION_PICK = [
    "Pozo",
    "Línea de conducción",
    "Ducto",
    "Tanque",
    "Separador",
    "Free Water",
    "Planta",
    "Batería",
    "Booster",
    "Calentador",
    "PIA",
    "Colector",
    "Otro (detallar en Notas/Observaciones)",
]

CAUSA_INMEDIATA_PICK = [
    "Acumulación parafina",
    "Aluvión",
    "Animales",
    "Choque o colisión",
    "Corrosión",
    "Desgaste",
    "Exceso de presión",
    "Formación de hidratos",
    "Golpe por maquinaria",
    "Golpe por maquina",
    "Junta o conexión",
    "Mantenimiento",
    "Nieve o lluvia",
    "Puesta en marcha",
    "Rayo",
    "Reparación",
    "Rotura o fisura",
    "Sabotaje o robo",
    "Sistema de control",
    "Sistema de seguridad",
    "vientos",
]


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
        color: #003366 !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }

    /* --- Subtítulos --- */
    h4, h5 {
        color: #144877 !important;
        font-weight: 600 !important;
    }

    /* --- Divider --- */
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
APP_PASSWORD = "MIE2025"

if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

if not st.session_state["auth_ok"]:
    st.title("Ingreso a Módulo MIA / MIE")

    pwd = st.text_input("Contraseña", type="password")

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("Ingresar"):
            if pwd == APP_PASSWORD:
                st.session_state["auth_ok"] = True
                st.success("Acceso concedido.")
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")

    st.stop()

# ==========================
# Imports backend (ya autenticado)
# ==========================
from mie_backend import (
    insertar_mie,
    insertar_foto,
    subir_foto_a_bucket,
    listar_mie,
    obtener_mie_detalle,
    obtener_fotos_mie,
    cerrar_mie_con_remediacion,
    obtener_todos_mie,
    actualizar_mie_completo,
    reemplazar_fotos_antes,   # 👈 NUEVO: reemplazar fotos ANTES
)

from mie_pdf_email import generar_mie_pdf

# =======================================================
#   APP
# =======================================================
st.title("🌱 Gestión de MIA (Incidentes Ambientales Declarados)")

modo = st.sidebar.radio(
    "Modo",
    ["Nuevo MIA", "Historial", "Estadísticas", "Exportar MIA"]
)

# =======================================================
#  MODO 1 - NUEVO MIA
# =======================================================
if modo == "Nuevo MIA":

    st.header("Registrar un nuevo MIA")

    # -----------------------
    # Datos básicos del incidente
    # -----------------------
    st.markdown("### Datos básicos del incidente")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fecha_evento = st.date_input("Fecha del evento", value=date.today())
    with col_f2:
        ahora = datetime.now().time().replace(microsecond=0)
        hora_evento = st.selectbox(
            "Hora del evento",
            options=HORAS_OPTS,
            format_func=lambda t: t.strftime("%H:%M"),
            index=_nearest_index(HORAS_OPTS, ahora),
            key="hora_evento_nuevo",
        )

    fecha_hora_evento = datetime.combine(fecha_evento, hora_evento)

    st.text_input(
        "Número de incidente / MIA",
        value="Se genera automáticamente al guardar",
        disabled=True,
    )
    drm = None

    # Usuario que carga (picklist)
    creado_por = st.selectbox(
        "Usuario que carga el MIA",
        options=[""] + USUARIOS_CARGA,
        index=0,
        key="creado_por_nuevo",
    )

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
        yacimiento = st.selectbox(
            "Yacimiento",
            ["", "Las Heras CG", "Canadon Escondida"],
            index=0,
        )

    with col_u2:
        zona = st.selectbox(
            "Zona",
            options=[""] + ZONAS_PICK,
            index=0,
        )

    with col_u3:
        nombre_instalacion = st.text_input("Nombre de la instalación")

    col_geo1, col_geo2 = st.columns(2)

    with col_geo1:
        latitud = st.text_input(
            "Latitud",
            placeholder="ej: -46,3832381000",
        )

    with col_geo2:
        longitud = st.text_input(
            "Longitud",
            placeholder="ej: -68,4552825300",
        )

    # -----------------------
    # Características del evento
    # -----------------------
    st.markdown("### Características del evento")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tipo_afectacion = st.selectbox(
            "Tipo de afectación",
            options=[""] + TIPO_AFECTACION_PICK,
        )
        tipo_derrame = st.selectbox(
            "Tipo de derrame",
            options=[""] + TIPO_DERRAME_PICK,
        )
    with col_t2:
        tipo_instalacion = st.selectbox(
            "Tipo de instalación",
            options=[""] + TIPO_INSTALACION_PICK,
        )
        causa_inmediata = st.selectbox(
            "Causa inmediata",
            options=[""] + CAUSA_INMEDIATA_PICK,
        )

    # -----------------------
    # Volúmenes y área
    # -----------------------
    st.markdown("### Volúmenes y área afectada")

    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        volumen_bruto_m3 = st.number_input("Volumen bruto (m³)", min_value=0.0, step=0.1)
    with col_v2:
        volumen_gas_m3 = st.number_input("Volumen de gas (m³)", min_value=0.0, step=1.0)
    with col_v3:
        area_afectada_m2 = st.number_input("Área afectada (m²)", min_value=0.0, step=1.0)

    col_v4, col_v5 = st.columns(2)
    with col_v5:
        ppm_agua = st.number_input(
            "% de agua",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            value=0.0,
        )

    volumen_crudo_m3 = volumen_bruto_m3 * ((100.0 - ppm_agua) / 100.0)

    with col_v4:
        st.number_input(
            "Volumen de crudo (m³)",
            value=float(volumen_crudo_m3),
            disabled=True,
        )

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
    responsable = st.selectbox(
        "Responsable",
        options=[""] + RESPONSABLES_PICK,
        index=0,
    )
    observaciones = st.text_area("Notas / observaciones")
    medidas_inmediatas = st.text_area("Medidas inmediatas adoptadas")

    fluido = st.text_input("Fluido", value="Petróleo + agua de formación")
    volumen_estimado_m3 = volumen_bruto_m3

    # -----------------------
    # Aprobación (opcional) - picklist apellido -> autocompleta nombre (FIX)
    # -----------------------
    st.markdown("### Aprobación (opcional)")

    def _sync_aprob_nombre_nuevo():
        ap = st.session_state.get("aprob_apellido_nuevo", "")
        st.session_state["aprob_nombre_nuevo"] = APROBADORES_MAP.get(ap, "") if ap else ""

    col_a1a, col_a1b = st.columns(2)
    with col_a1a:
        aprob_apellido = st.selectbox(
            "Aprobador - Apellido",
            options=APROBADORES_APELLIDOS,
            index=0,
            key="aprob_apellido_nuevo",
            on_change=_sync_aprob_nombre_nuevo,
        )

    # asegura autocompletado en el primer render también
    if "aprob_nombre_nuevo" not in st.session_state:
        _sync_aprob_nombre_nuevo()

    with col_a1b:
        aprob_nombre = st.text_input(
            "Aprobador - Nombre",
            key="aprob_nombre_nuevo",
            disabled=True,
        )

    col_a2a, col_a2b = st.columns(2)
    with col_a2a:
        fecha_aprob = st.date_input("Fecha aprobación", value=date.today())
    with col_a2b:
        ahora = datetime.now().time().replace(microsecond=0)
        hora_aprob = st.selectbox(
            "Hora aprobación",
            options=HORAS_OPTS,
            format_func=lambda t: t.strftime("%H:%M"),
            index=_nearest_index(HORAS_OPTS, ahora),
            key="hora_aprob_nuevo",
        )

    fecha_hora_aprobacion = (
        datetime.combine(fecha_aprob, hora_aprob)
        if st.session_state.get("aprob_apellido_nuevo")
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
        key="fotos_antes_nuevo",
    )

    # -----------------------
    # Anti doble envío (estado + huella)
    # -----------------------
    if "saving_mia" not in st.session_state:
        st.session_state["saving_mia"] = False
    if "last_submit_key" not in st.session_state:
        st.session_state["last_submit_key"] = None
    if "last_submit_ts" not in st.session_state:
        st.session_state["last_submit_ts"] = 0.0

    def _make_submit_key():
        payload = {
            "fecha_evento": str(fecha_evento),
            "hora_evento": hora_evento.strftime("%H:%M") if hora_evento else "",
            "creado_por": creado_por or "",
            "yacimiento": yacimiento or "",
            "zona": zona or "",
            "nombre_instalacion": nombre_instalacion or "",
            "latitud": latitud or "",
            "longitud": longitud or "",
            "tipo_afectacion": tipo_afectacion or "",
            "tipo_derrame": tipo_derrame or "",
            "tipo_instalacion": tipo_instalacion or "",
            "causa_inmediata": causa_inmediata or "",
            "volumen_bruto_m3": float(volumen_bruto_m3 or 0),
            "volumen_gas_m3": float(volumen_gas_m3 or 0),
            "ppm_agua": float(ppm_agua or 0),
            "area_afectada_m2": float(area_afectada_m2 or 0),
            "recursos_afectados": recursos_afectados or "",
            "causa_probable": causa_probable or "",
            "responsable": responsable or "",
            "observaciones": observaciones or "",
            "medidas_inmediatas": medidas_inmediatas or "",
            "aprob_apellido": st.session_state.get("aprob_apellido_nuevo") or "",
            "aprob_nombre": st.session_state.get("aprob_nombre_nuevo") or "",
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    # -----------------------
    # Botón GUARDAR (con anti-duplicado)
    # -----------------------
    btn_guardar = st.button("Guardar MIA", disabled=st.session_state["saving_mia"])

    if btn_guardar:
        if st.session_state["saving_mia"]:
            st.warning("Ya estoy guardando…")
            st.stop()

        # Anti doble envío (mismo formulario dentro de 60s)
        submit_key = _make_submit_key()
        now = time.time()
        if (st.session_state["last_submit_key"] == submit_key) and (now - st.session_state["last_submit_ts"] < 60):
            st.warning("Este MIA ya fue enviado recién. Evito duplicarlo.")
            st.stop()

        st.session_state["saving_mia"] = True

        if not nombre_instalacion or not creado_por:
            st.session_state["saving_mia"] = False
            st.error("❌ Nombre de la instalación y Usuario son obligatorios.")
            st.stop()

        try:
            with st.spinner("Guardando MIA..."):
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
                    volumen_bruto_m3=float(volumen_bruto_m3),
                    volumen_gas_m3=float(volumen_gas_m3),
                    ppm_agua=float(ppm_agua),
                    volumen_crudo_m3=float(volumen_crudo_m3),
                    area_afectada_m2=float(area_afectada_m2),
                    recursos_afectados=recursos_afectados,
                    medidas_inmediatas=medidas_inmediatas or None,

                    aprobador_apellido=st.session_state.get("aprob_apellido_nuevo") or None,
                    aprobador_nombre=st.session_state.get("aprob_nombre_nuevo") or None,
                    fecha_hora_aprobacion=fecha_hora_aprobacion,
                )

            # marcar como enviado (para evitar reintentos inmediatos)
            st.session_state["last_submit_key"] = submit_key
            st.session_state["last_submit_ts"] = now

            st.success(f"✅ MIA guardado. CÓDIGO: {codigo}")

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
            st.error(f"⚠️ Error guardando MIA: {e}")

        finally:
            st.session_state["saving_mia"] = False

    # ==================================================
    #  PDF del último MIA
    # ==================================================
    st.markdown("### 📄 Generar PDF del último MIA")

    if "ultimo_mie_id" not in st.session_state:
        st.info("Guardá un MIA para generar el PDF.")
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
                "📄 Descargar PDF MIA",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
            )


# =======================================================
#  MODO 2 - HISTORIAL MIA (CON EDICIÓN SOLO DE CARGA + REEMPLAZO FOTOS ANTES)
# =======================================================
elif modo == "Historial":
    st.header("Historial de MIA")

    registros = listar_mie()
    if not registros:
        st.info("No hay MIA registrados.")
        st.stop()

    opciones = {}
    for r in registros:
        nombre = getattr(r, "nombre_instalacion", None) or r.pozo or "(sin instalación)"
        label = f"{r.codigo_mie} - {nombre} ({r.estado})"
        opciones[label] = r.mie_id

    seleccion = st.selectbox("Seleccionar MIA", list(opciones.keys()), key="hist_sel_mie")
    mie_id = opciones[seleccion]

    detalle = obtener_mie_detalle(mie_id)
    fotos = obtener_fotos_mie(mie_id)

    if "edit_mie_id" not in st.session_state:
        st.session_state["edit_mie_id"] = None

    editando = (st.session_state["edit_mie_id"] == mie_id)

    st.subheader("📄 Datos del MIA")

    # Botonera
    c1, c2, c3 = st.columns([1, 1, 6])
    with c1:
        if not editando:
            if st.button("✏️ Editar", key=f"btn_edit_{mie_id}"):
                st.session_state["edit_mie_id"] = mie_id
                st.rerun()
        else:
            st.success("Modo edición activado (solo carga del MIA)")

    with c2:
        if editando:
            if st.button("❌ Cancelar", key=f"btn_cancel_{mie_id}"):
                st.session_state["edit_mie_id"] = None
                st.rerun()

    def _to_datetime(val):
        try:
            if val is None or val == "":
                return None
            return pd.to_datetime(val).to_pydatetime()
        except Exception:
            return None

    dt_evento = _to_datetime(getattr(detalle, "fecha_hora_evento", None)) or datetime.now()
    dt_aprob  = _to_datetime(getattr(detalle, "fecha_hora_aprobacion", None))

    fecha_evento_def = dt_evento.date()
    hora_evento_def  = dt_evento.time().replace(microsecond=0)

    if dt_aprob:
        fecha_aprob_def = dt_aprob.date()
        hora_aprob_def  = dt_aprob.time().replace(microsecond=0)
    else:
        fecha_aprob_def = date.today()
        hora_aprob_def  = datetime.now().time().replace(microsecond=0)

    # ----- Datos básicos -----
    st.markdown("### Datos básicos del incidente")
    colb1, colb2 = st.columns(2)
    with colb1:
        st.text_input(
            "Número de incidente / DRM",
            getattr(detalle, "drm", "") or "",
            disabled=True,
            key=f"drm_{mie_id}",
        )

    # usuario carga (picklist también en historial)
    creado_por_val = getattr(detalle, "creado_por", "") or ""
    creado_por_opts = [""] + USUARIOS_CARGA
    creado_por_idx = creado_por_opts.index(creado_por_val) if creado_por_val in creado_por_opts else 0

    with colb2:
        creado_por = st.selectbox(
            "Usuario que carga el MIA",
            options=creado_por_opts,
            index=creado_por_idx,
            disabled=(not editando),
            key=f"creado_por_{mie_id}",
        )

    colf1, colf2 = st.columns(2)
    with colf1:
        fecha_evento = st.date_input(
            "Fecha del evento",
            value=fecha_evento_def,
            disabled=(not editando),
            key=f"fecha_evento_{mie_id}",
        )
        hora_evento = st.selectbox(
            "Hora del evento",
            options=HORAS_OPTS,
            format_func=lambda t: t.strftime("%H:%M"),
            index=_nearest_index(HORAS_OPTS, hora_evento_def),
            disabled=(not editando),
            key=f"hora_evento_{mie_id}",
        )
    with colf2:
        st.text_input(
            "Fecha de carga",
            str(getattr(detalle, "fecha_creacion_registro", "") or ""),
            disabled=True,
            key=f"fecha_carga_{mie_id}",
        )

    fecha_hora_evento = datetime.combine(fecha_evento, hora_evento)

    # ----- Personas involucradas -----
    st.markdown("### Personas involucradas")

    colp1a, colp1b = st.columns(2)
    with colp1a:
        observador_apellido = st.text_input(
            "Observador - Apellido",
            getattr(detalle, "observador_apellido", "") or "",
            disabled=(not editando),
            key=f"obs_ap_{mie_id}",
        )
    with colp1b:
        observador_nombre = st.text_input(
            "Observador - Nombre",
            getattr(detalle, "observador_nombre", "") or "",
            disabled=(not editando),
            key=f"obs_no_{mie_id}",
        )

    colp2a, colp2b = st.columns(2)
    with colp2a:
        responsable_inst_apellido = st.text_input(
            "Responsable de la instalación - Apellido",
            getattr(detalle, "responsable_inst_apellido", "") or "",
            disabled=(not editando),
            key=f"resp_inst_ap_{mie_id}",
        )
    with colp2b:
        responsable_inst_nombre = st.text_input(
            "Responsable de la instalación - Nombre",
            getattr(detalle, "responsable_inst_nombre", "") or "",
            disabled=(not editando),
            key=f"resp_inst_no_{mie_id}",
        )

    # ----- Ubicación / instalación -----
    st.markdown("### Ubicación / instalación")
    colu1, colu2, colu3 = st.columns(3)

    yacimiento_opts = ["", "Las Heras CG", "Canadon Escondida"]
    yac_val = getattr(detalle, "yacimiento", "") or ""
    yac_idx = yacimiento_opts.index(yac_val) if yac_val in yacimiento_opts else 0

    with colu1:
        yacimiento = st.selectbox(
            "Yacimiento",
            yacimiento_opts,
            index=yac_idx,
            disabled=(not editando),
            key=f"yacimiento_{mie_id}",
        )
    with colu2:
        zona_val = getattr(detalle, "zona", "") or ""
        zona_opts = [""] + ZONAS_PICK
        if zona_val and zona_val not in zona_opts:
            zona_opts = [zona_val] + zona_opts
        zona_idx = zona_opts.index(zona_val) if zona_val in zona_opts else 0

        zona = st.selectbox(
            "Zona",
            options=zona_opts,
            index=zona_idx,
            disabled=(not editando),
            key=f"zona_{mie_id}",
        )
    with colu3:
        nombre_instalacion = st.text_input(
            "Nombre de la instalación",
            getattr(detalle, "nombre_instalacion", "") or "",
            disabled=(not editando),
            key=f"nombre_inst_{mie_id}",
        )

    coll1, coll2 = st.columns(2)
    with coll1:
        latitud = st.text_input(
            "Latitud",
            getattr(detalle, "latitud", "") or "",
            disabled=(not editando),
            key=f"lat_{mie_id}",
        )
    with coll2:
        longitud = st.text_input(
            "Longitud",
            getattr(detalle, "longitud", "") or "",
            disabled=(not editando),
            key=f"lon_{mie_id}",
        )

    # ----- Características del evento -----
    st.markdown("### Características del evento")
    colc1, colc2 = st.columns(2)

    tipo_afectacion_opts = [""] + TIPO_AFECTACION_PICK
    tipo_derrame_opts = [""] + TIPO_DERRAME_PICK
    tipo_instalacion_opts = [""] + TIPO_INSTALACION_PICK
    causa_inmediata_opts = [""] + CAUSA_INMEDIATA_PICK

    ta_val = getattr(detalle, "tipo_afectacion", "") or ""
    td_val = getattr(detalle, "tipo_derrame", "") or ""
    ti_val = getattr(detalle, "tipo_instalacion", "") or ""
    ci_val = getattr(detalle, "causa_inmediata", "") or ""

    with colc1:
        tipo_afectacion = st.selectbox(
            "Tipo de afectación",
            tipo_afectacion_opts,
            index=(tipo_afectacion_opts.index(ta_val) if ta_val in tipo_afectacion_opts else 0),
            disabled=(not editando),
            key=f"tipo_af_{mie_id}",
        )
        tipo_derrame = st.selectbox(
            "Tipo de derrame",
            tipo_derrame_opts,
            index=(tipo_derrame_opts.index(td_val) if td_val in tipo_derrame_opts else 0),
            disabled=(not editando),
            key=f"tipo_der_{mie_id}",
        )
    with colc2:
        tipo_instalacion = st.selectbox(
            "Tipo de instalación",
            tipo_instalacion_opts,
            index=(tipo_instalacion_opts.index(ti_val) if ti_val in tipo_instalacion_opts else 0),
            disabled=(not editando),
            key=f"tipo_inst_{mie_id}",
        )
        causa_inmediata = st.selectbox(
            "Causa inmediata",
            causa_inmediata_opts,
            index=(causa_inmediata_opts.index(ci_val) if ci_val in causa_inmediata_opts else 0),
            disabled=(not editando),
            key=f"causa_inm_{mie_id}",
        )

    # ----- Volúmenes y área afectada -----
    st.markdown("### Volúmenes y área afectada")
    colv1, colv2, colv3 = st.columns(3)

    vol_bruto_def = float(getattr(detalle, "volumen_bruto_m3", 0) or 0)
    vol_gas_def   = float(getattr(detalle, "volumen_gas_m3", 0) or 0)
    area_def      = float(getattr(detalle, "area_afectada_m2", 0) or 0)
    try:
        ppm_def = float(getattr(detalle, "ppm_agua", 0) or 0)
    except Exception:
        ppm_def = 0.0

    with colv1:
        volumen_bruto_m3 = st.number_input(
            "Volumen bruto (m³)",
            min_value=0.0,
            step=0.1,
            value=vol_bruto_def,
            disabled=(not editando),
            key=f"vol_bruto_{mie_id}",
        )
    with colv2:
        volumen_gas_m3 = st.number_input(
            "Volumen de gas (m³)",
            min_value=0.0,
            step=1.0,
            value=vol_gas_def,
            disabled=(not editando),
            key=f"vol_gas_{mie_id}",
        )
    with colv3:
        area_afectada_m2 = st.number_input(
            "Área afectada (m²)",
            min_value=0.0,
            step=1.0,
            value=area_def,
            disabled=(not editando),
            key=f"area_{mie_id}",
        )

    colv4, colv5 = st.columns(2)
    with colv5:
        ppm_agua = st.number_input(
            "% de agua",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            value=ppm_def,
            disabled=(not editando),
            key=f"ppm_{mie_id}",
        )

    volumen_crudo_m3 = volumen_bruto_m3 * ((100.0 - ppm_agua) / 100.0)

    with colv4:
        st.number_input(
            "Volumen de crudo (m³)",
            value=float(volumen_crudo_m3),
            disabled=True,
            key=f"vol_crudo_{mie_id}",
        )

    # ----- Recursos afectados -----
    st.markdown("### Recursos afectados")
    recursos_afectados = st.text_area(
        "Recursos afectados",
        getattr(detalle, "recursos_afectados", "") or "",
        disabled=(not editando),
        key=f"recursos_{mie_id}",
    )

    # ----- Otros datos / notas -----
    st.markdown("### Otros datos / notas")
    coln1, coln2 = st.columns(2)
    with coln1:
        causa_probable = st.text_input(
            "Causa probable",
            getattr(detalle, "causa_probable", "") or "",
            disabled=(not editando),
            key=f"causa_prob_{mie_id}",
        )
    with coln2:
        responsable_val = getattr(detalle, "responsable", "") or ""
        responsable_opts = [""] + RESPONSABLES_PICK
        if responsable_val and responsable_val not in responsable_opts:
            responsable_opts = [responsable_val] + responsable_opts
        responsable_idx = responsable_opts.index(responsable_val) if responsable_val in responsable_opts else 0

        responsable = st.selectbox(
            "Responsable",
            options=responsable_opts,
            index=responsable_idx,
            disabled=(not editando),
            key=f"responsable_{mie_id}",
        )

    observaciones = st.text_area(
        "Notas / Observaciones",
        getattr(detalle, "observaciones", "") or "",
        disabled=(not editando),
        key=f"obs_{mie_id}",
    )

    medidas_inmediatas = st.text_area(
        "Medidas inmediatas adoptadas",
        getattr(detalle, "medidas_inmediatas", "") or "",
        disabled=(not editando),
        key=f"medidas_{mie_id}",
    )

    # ----- Aprobación (picklist apellido -> autocompleta nombre) (FIX) -----
    st.markdown("### Aprobación")

    k_ap = f"aprob_ap_{mie_id}"
    k_no = f"aprob_no_{mie_id}"

    def _sync_aprob_nombre_hist():
        ap = st.session_state.get(k_ap, "")
        st.session_state[k_no] = APROBADORES_MAP.get(ap, "") if ap else ""

    ap_current = getattr(detalle, "aprobador_apellido", "") or ""
    no_current = getattr(detalle, "aprobador_nombre", "") or ""

    ap_guess, no_guess = _split_apellido_nombre(ap_current)
    if ap_guess and not no_current:
        no_current = no_guess

    # inicialización (solo una vez por mie_id)
    if k_ap not in st.session_state:
        st.session_state[k_ap] = ap_guess if ap_guess in APROBADORES_MAP else ""
    if k_no not in st.session_state:
        st.session_state[k_no] = APROBADORES_MAP.get(st.session_state[k_ap], "") if st.session_state[k_ap] else (no_current or "")

    ap_idx = APROBADORES_APELLIDOS.index(st.session_state[k_ap]) if st.session_state[k_ap] in APROBADORES_APELLIDOS else 0

    cola1, cola2 = st.columns(2)
    with cola1:
        aprobador_apellido = st.selectbox(
            "Aprobador - Apellido",
            options=APROBADORES_APELLIDOS,
            index=ap_idx,
            disabled=(not editando),
            key=k_ap,
            on_change=_sync_aprob_nombre_hist,
        )
        aprobador_nombre = st.text_input(
            "Aprobador - Nombre",
            key=k_no,
            disabled=True,
        )

    with cola2:
        fecha_aprob = st.date_input(
            "Fecha aprobación",
            value=fecha_aprob_def,
            disabled=(not editando),
            key=f"fecha_aprob_{mie_id}",
        )
        hora_aprob = st.selectbox(
            "Hora aprobación",
            options=HORAS_OPTS,
            format_func=lambda t: t.strftime("%H:%M"),
            index=_nearest_index(HORAS_OPTS, hora_aprob_def),
            disabled=(not editando),
            key=f"hora_aprob_{mie_id}",
        )

    fecha_hora_aprobacion = (
        datetime.combine(fecha_aprob, hora_aprob)
        if st.session_state.get(k_ap)
        else None
    )

    # -----------------------
    # Guardar cambios (solo carga del MIA)
    # -----------------------
    if editando:
        st.divider()
        colg1, colg2, colg3 = st.columns([1, 1, 6])

        with colg1:
            if st.button("💾 Guardar cambios", key=f"btn_save_{mie_id}"):
                if not nombre_instalacion or not creado_por:
                    st.error("❌ Nombre de la instalación y Usuario son obligatorios.")
                else:
                    try:
                        actualizar_mie_completo(
                            mie_id=mie_id,
                            creado_por=creado_por or None,
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

                            volumen_bruto_m3=float(volumen_bruto_m3),
                            volumen_gas_m3=float(volumen_gas_m3),
                            ppm_agua=float(ppm_agua),
                            volumen_crudo_m3=float(volumen_crudo_m3),
                            area_afectada_m2=float(area_afectada_m2),

                            recursos_afectados=recursos_afectados or None,
                            causa_probable=causa_probable or None,
                            responsable=responsable or None,
                            observaciones=observaciones or None,
                            medidas_inmediatas=medidas_inmediatas or None,

                            aprobador_apellido=st.session_state.get(k_ap) or None,
                            aprobador_nombre=st.session_state.get(k_no) or None,
                            fecha_hora_aprobacion=fecha_hora_aprobacion,
                        )
                        st.success("✅ Cambios guardados.")
                        st.session_state["edit_mie_id"] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error guardando cambios: {e}")

        with colg2:
            if st.button("❌ Cancelar edición", key=f"btn_cancel2_{mie_id}"):
                st.session_state["edit_mie_id"] = None
                st.rerun()

    # ---------------------------------------------------
    # FOTOS (VISTA) + REEMPLAZO SOLO DE ANTES EN MODO EDITAR
    # ---------------------------------------------------
    st.subheader("📸 Fotos asociadas")

    fotos_antes = [f for f in fotos if f["tipo"] == "ANTES"]
    fotos_despues = [f for f in fotos if f["tipo"] == "DESPUES"]

    # 1) Fotos actuales ANTES (siempre se ven)
    if fotos_antes:
        st.markdown("#### Fotos del incidente (ANTES)")
        for f in fotos_antes:
            st.markdown(f"**{f['fecha_hora']}**")
            st.image(f["data"], use_container_width=True)
    else:
        st.info("No hay fotos ANTES cargadas.")

    # 2) REEMPLAZO de fotos ANTES: SOLO cuando está editando
    if editando:
        st.markdown("### ♻️ Reemplazar fotos ANTES (INCIDENTE)")
        st.caption("⚠️ Esto borra TODAS las fotos ANTES actuales y carga las nuevas. No se toca remediación ni fotos DESPUÉS.")

        nuevas_fotos_antes = st.file_uploader(
            "Seleccionar nuevas fotos ANTES (reemplazo total)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key=f"fotos_antes_replace_{mie_id}",
        )

        if st.button("♻️ Reemplazar fotos ANTES", key=f"btn_replace_antes_{mie_id}"):
            try:
                if not nuevas_fotos_antes:
                    st.warning("No seleccionaste fotos.")
                else:
                    codigo = getattr(detalle, "codigo_mie", None)
                    if not codigo:
                        st.error("No se encontró código de MIA para armar la ruta en el bucket.")
                    else:
                        reemplazar_fotos_antes(
                            mie_id=mie_id,
                            codigo_mie=codigo,
                            archivos=nuevas_fotos_antes
                        )
                        st.success("✅ Fotos ANTES reemplazadas.")
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Error reemplazando fotos ANTES: {e}")

    # 3) Fotos DESPUÉS: SOLO se muestran fuera de edición (modo lectura),
    #    porque corresponden a remediación / cierre.
    if (not editando):
        if fotos_despues:
            st.markdown("#### Fotos de remediación (DESPUÉS)")
            for f in fotos_despues:
                st.markdown(f"**{f['fecha_hora']}**")
                st.image(f["data"], use_container_width=True)

    # ---------------------------------------------------
    # BLOQUE DE REMEDIACIÓN (NO SE TOCA EN EDICIÓN)
    # ---------------------------------------------------
    if not editando:
        if detalle.estado == "CERRADO":
            st.subheader("✅ Datos de remediación")

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

            st.success("Este MIA ya está CERRADO.")

            st.subheader("📄 Generar PDF de este MIA")

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
                    "📄 Descargar PDF de este MIA",
                    data=pdf_bytes_hist,
                    file_name=file_name_hist,
                    mime="application/pdf",
                )

        else:
            st.subheader("🛠️ Cargar datos de remediación y CERRAR MIA")

            colr1, colr2 = st.columns(2)
            with colr1:
                fecha_fin = st.date_input(
                    "Fecha finalización saneamiento",
                    datetime.now().date(),
                    key=f"rem_fecha_{mie_id}",
                )
            with colr2:
                ahora = datetime.now().time().replace(microsecond=0)
                hora_fin = st.selectbox(
                    "Hora finalización",
                    options=HORAS_OPTS,
                    format_func=lambda t: t.strftime("%H:%M"),
                    index=_nearest_index(HORAS_OPTS, ahora),
                    key=f"rem_hora_{mie_id}",
                )

            fecha_fin_dt = datetime.combine(fecha_fin, hora_fin)

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

            destino_tierra = st.text_input("Destino tierra impactada", key=f"destino_{mie_id}")
            comentarios = st.text_area("Comentarios de remediación", key=f"coment_{mie_id}")

            colap1, colap2 = st.columns(2)
            with colap1:
                aprob_ap = st.text_input("Aprobador final - Apellido", key=f"ap_ap_{mie_id}")
            with colap2:
                aprob_no = st.text_input("Aprobador final - Nombre", key=f"ap_no_{mie_id}")

            st.markdown("### 📸 Fotos DESPUÉS del Saneamiento")
            fotos_despues_up = st.file_uploader(
                "Subir fotos",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"fotos_desp_{mie_id}",
            )

            if st.button("✔️ Guardar remediación y CERRAR MIA", key=f"btn_cerrar_{mie_id}"):
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

                    if fotos_despues_up:
                        codigo = detalle.codigo_mie
                        for archivo in fotos_despues_up:
                            nombre_destino = (
                                f"{codigo}/DESPUES/"
                                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
                            )
                            blob_name = subir_foto_a_bucket(archivo, nombre_destino)
                            insertar_foto(mie_id, "DESPUES", blob_name)

                    st.success("MIA cerrado exitosamente.")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al cerrar MIA: {e}")

# =======================================================
#  MODO 2.5 - ESTADISTICAS
# =======================================================
elif modo == "Estadísticas":
    st.header("Estadísticas de MIA")

    registros = obtener_todos_mie()
    if not registros:
        st.info("No hay MIA registrados para generar estadísticas.")
        st.stop()

    df = pd.DataFrame([dict(r) for r in registros])

    for col in ["fecha_hora_evento", "fecha_creacion_registro", "rem_fecha_fin_saneamiento"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True).dt.tz_localize(None)

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

    estado_sel = st.selectbox("Estado del MIA", ["(Todos)"] + estados)

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
        st.warning("No hay MIA que coincidan con los filtros seleccionados.")
        st.stop()

    st.subheader("📊 Dashboard Ejecutivo (MIA)")

    total_mia = len(df_filt)
    abiertos = len(df_filt[df_filt["estado"] == "ABIERTO"])
    cerrados = len(df_filt[df_filt["estado"] == "CERRADO"])

    df_cerrados = df_filt.dropna(subset=["rem_fecha_fin_saneamiento"])
    if not df_cerrados.empty:
        df_cerrados["dias_cierre"] = (
            df_cerrados["rem_fecha_fin_saneamiento"] - df_cerrados["fecha_hora_evento"]
        ).dt.days
        promedio_cierre = round(df_cerrados["dias_cierre"].mean(), 1)
    else:
        promedio_cierre = "—"

    volumen_activo = df_filt[df_filt["estado"] == "ABIERTO"]["volumen_estimado_m3"].sum()
    volumen_remediado = (
        df_filt["rem_volumen_liquido_recuperado"].fillna(0)
        + df_filt["rem_volumen_tierra_levantada"].fillna(0)
    ).sum()

    df_mag = df_filt["magnitud"].value_counts().to_dict()
    n1 = df_mag.get("N1", 0)
    n2 = df_mag.get("N2", 0)
    n3 = df_mag.get("N3", 0)

    def pct(v): return f"{(v / total_mia * 100):.1f}%" if total_mia > 0 else "0%"

    col1, col2, col3 = st.columns(3)
    col1.metric("MIA Totales", total_mia)
    col2.metric("MIA Abiertos", abiertos)
    col3.metric("MIA Cerrados", cerrados)

    col4, col5, col6 = st.columns(3)
    col4.metric("⏱️ Tiempo promedio de cierre (días)", promedio_cierre)
    col5.metric("🛢️ Volumen activo (m³)", round(volumen_activo, 2))
    col6.metric("♻️ Volumen remediado total (m³)", round(volumen_remediado, 2))

    st.divider()

    st.subheader("Distribución por Magnitud del Evento")
    st.write(
        f"""
        **N1:** {n1} ({pct(n1)})  
        **N2:** {n2} ({pct(n2)})  
        **N3:** {n3} ({pct(n3)})  
        """
    )

    st.divider()

    import plotly.graph_objects as go
    import plotly.express as px

    st.subheader("Evolución de MIA por mes")

    if "fecha_hora_evento" in df_filt.columns:
        df_tmp = df_filt.copy()
        df_tmp["mes"] = df_tmp["fecha_hora_evento"].dt.to_period("M").dt.to_timestamp()

        df_mes_total = df_tmp.groupby("mes").size().reset_index(name="total_mia").sort_values("mes")

        df_cerr_tmp = df_tmp[df_tmp["estado"] == "CERRADO"].copy()
        if not df_cerr_tmp.empty:
            df_cerr_tmp["mes"] = df_cerr_tmp["fecha_hora_evento"].dt.to_period("M").dt.to_timestamp()
            df_mes_cerr = df_cerr_tmp.groupby("mes").size().reset_index(name="cerrados_mia")
        else:
            df_mes_cerr = df_mes_total[["mes"]].copy()
            df_mes_cerr["cerrados_mia"] = 0

        df_evo = df_mes_total.merge(df_mes_cerr, on="mes", how="left").fillna(0)
        df_evo["mes_str"] = df_evo["mes"].dt.strftime("%Y-%m")

        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_evo["mes_str"], y=df_evo["total_mia"], name="MIA totales"))
        fig.add_trace(go.Scatter(
            x=df_evo["mes_str"],
            y=df_evo["cerrados_mia"],
            mode="lines+markers+text",
            name="MIA cerrados",
            text=df_evo["cerrados_mia"],
            textposition="top center"
        ))

        fig.update_layout(
            title="MIA totales y cerrados por mes",
            xaxis_title="Mes",
            yaxis_title="Cantidad de MIA",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=40, r=20, t=60, b=40)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No se encontró la columna 'fecha_hora_evento' para graficar evolución mensual.")

    st.subheader("Distribución de MIA por Yacimiento")
    if "yacimiento" in df_filt.columns:
        df_yac = df_filt.groupby("yacimiento").size().reset_index(name="cantidad").sort_values("cantidad", ascending=False)
        if not df_yac.empty:
            fig_yac = px.bar(df_yac, x="cantidad", y="yacimiento", orientation="h",
                             title="MIA por Yacimiento",
                             labels={"cantidad": "Cantidad de MIA", "yacimiento": "Yacimiento"})
            fig_yac.update_layout(template="plotly_white", margin=dict(l=40, r=20, t=60, b=40))
            st.plotly_chart(fig_yac, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por yacimiento.")
    else:
        st.info("No se encontró la columna 'yacimiento'.")

    st.subheader("Distribución de MIA por Tipo de Instalación")
    if "tipo_instalacion" in df_filt.columns:
        df_inst = df_filt.groupby("tipo_instalacion").size().reset_index(name="cantidad").sort_values("cantidad", ascending=False)
        if not df_inst.empty:
            fig_inst = px.bar(df_inst, x="tipo_instalacion", y="cantidad",
                              title="MIA por Tipo de Instalación",
                              labels={"cantidad": "Cantidad de MIA", "tipo_instalacion": "Tipo de Instalación"})
            fig_inst.update_layout(template="plotly_white", xaxis_tickangle=-30, margin=dict(l=40, r=20, t=60, b=80))
            st.plotly_chart(fig_inst, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por tipo de instalación.")
    else:
        st.info("No se encontró la columna 'tipo_instalacion'.")

    st.subheader("Distribución de MIA por Causa Inmediata")
    if "causa_inmediata" in df_filt.columns:
        df_causa = df_filt.groupby("causa_inmediata").size().reset_index(name="cantidad").sort_values("cantidad", ascending=False)
        if not df_causa.empty:
            fig_causa = px.bar(df_causa, x="causa_inmediata", y="cantidad",
                               title="MIA por Causa Inmediata",
                               labels={"cantidad": "Cantidad de MIA", "causa_inmediata": "Causa Inmediata"})
            fig_causa.update_layout(template="plotly_white", xaxis_tickangle=-30, margin=dict(l=40, r=20, t=60, b=80))
            st.plotly_chart(fig_causa, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por causa inmediata.")
    else:
        st.info("No se encontró la columna 'causa_inmediata'.")

    st.subheader("Distribución de MIA por Tipo de Afectación")
    if "tipo_afectacion" in df_filt.columns:
        df_afec = df_filt.groupby("tipo_afectacion").size().reset_index(name="cantidad").sort_values("cantidad", ascending=False)
        if not df_afec.empty:
            fig_afec = px.bar(df_afec, x="tipo_afectacion", y="cantidad",
                              title="MIA por Tipo de Afectación",
                              labels={"cantidad": "Cantidad de MIA", "tipo_afectacion": "Tipo de Afectación"})
            fig_afec.update_layout(template="plotly_white", xaxis_tickangle=-30, margin=dict(l=40, r=20, t=60, b=80))
            st.plotly_chart(fig_afec, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por tipo de afectación.")
    else:
        st.info("No se encontró la columna 'tipo_afectacion'.")

    st.subheader("Distribución de MIA por Tipo de Derrame")
    if "tipo_derrame" in df_filt.columns:
        df_der = df_filt.groupby("tipo_derrame").size().reset_index(name="cantidad").sort_values("cantidad", ascending=False)
        if not df_der.empty:
            fig_der = px.bar(df_der, x="tipo_derrame", y="cantidad",
                             title="MIA por Tipo de Derrame",
                             labels={"cantidad": "Cantidad de MIA", "tipo_derrame": "Tipo de Derrame"})
            fig_der.update_layout(template="plotly_white", xaxis_tickangle=-30, margin=dict(l=40, r=20, t=60, b=80))
            st.plotly_chart(fig_der, use_container_width=True)
        else:
            st.info("No hay datos para mostrar por tipo de derrame.")
    else:
        st.info("No se encontró la columna 'tipo_derrame'.")

# =======================================================
#  MODO 3 - EXPORTAR MIA A EXCEL
# =======================================================
elif modo == "Exportar MIA":
    st.header("Exportar base completa de MIA")

    st.markdown("""
    Esta opción exporta la tabla **mie_eventos** completa (sin fotos)
    en un archivo Excel `.xlsx` para auditoría o análisis.
    """)

    if st.button("Generar archivo Excel"):
        try:
            registros = obtener_todos_mie()

            if not registros:
                st.info("No existen registros de MIA para exportar.")
            else:
                filas = [dict(r) for r in registros]
                df = pd.DataFrame(filas)

                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = pd.to_datetime(df[col], utc=True).dt.tz_localize(None)

                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="MIA")

                buffer.seek(0)

                nombre_archivo = f"MIA_mie_eventos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

                st.download_button(
                    "📥 Descargar Excel",
                    data=buffer,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        except Exception as e:
            st.error(f"❌ Error al generar la exportación: {e}")
