# ============================================================
# mie_backend.py — versión corregida y unificada
# ============================================================

from datetime import datetime
from io import BytesIO
from google.cloud import bigquery, storage
from config import PROJECT_ID, DATASET_ID, BUCKET_NAME

# ---------------------------------------------------------
# Clientes globales
# ---------------------------------------------------------
bq_client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)


# ---------------------------------------------------------
# 1) Obtener siguiente ID incremental
# ---------------------------------------------------------
def obtener_siguiente_id(tabla: str, campo: str) -> int:
    query = f"""
        SELECT MAX({campo}) AS max_id
        FROM `{PROJECT_ID}.{DATASET_ID}.{tabla}`
    """
    rows = list(bq_client.query(query).result())
    if not rows or rows[0].max_id is None:
        return 1
    return rows[0].max_id + 1


# ---------------------------------------------------------
# 2) Generar código tipo MIE-2025-0001
# ---------------------------------------------------------
def generar_codigo_mie(num: int) -> str:
    year = datetime.now().year
    return f"MIE-{year}-{num:04d}"


# ---------------------------------------------------------
# 3) Subir imagen al bucket
# ---------------------------------------------------------
def subir_foto_a_bucket(file_obj, nombre_destino: str) -> str:
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(nombre_destino)

    data = file_obj.read()
    blob.upload_from_file(BytesIO(data), content_type=file_obj.type)

    return nombre_destino   # path interno del bucket


# ---------------------------------------------------------
# 4) Insertar nuevo MIE
# ---------------------------------------------------------
def insertar_mie(
    drm,
    pozo,
    locacion,
    fluido,
    volumen_estimado_m3,
    causa_probable,
    responsable,
    observaciones,
    creado_por,
    fecha_hora_evento=None,

    # ---- campos nuevos IADE ----
    observador_apellido=None,
    observador_nombre=None,
    responsable_inst_apellido=None,
    responsable_inst_nombre=None,
    yacimiento=None,
    zona=None,
    nombre_instalacion=None,
    latitud=None,
    longitud=None,
    tipo_afectacion=None,
    tipo_derrame=None,
    tipo_instalacion=None,
    causa_inmediata=None,
    volumen_bruto_m3=None,
    volumen_gas_m3=None,
    ppm_agua=None,
    volumen_crudo_m3=None,
    area_afectada_m2=None,
    recursos_afectados=None,
    magnitud=None,
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
    medidas_inmediatas=None,
    aprobador_apellido=None,
    aprobador_nombre=None,
    fecha_hora_aprobacion=None,
):
    tabla = f"{PROJECT_ID}.{DATASET_ID}.mie_eventos"

    mie_id = obtener_siguiente_id("mie_eventos", "mie_id")
    codigo = generar_codigo_mie(mie_id)

    if not drm:
        drm = codigo

    ahora = datetime.utcnow()
    fecha_evento = fecha_hora_evento or ahora

    # ---- Insert ----
    query = f"""
        INSERT INTO `{tabla}` (
            mie_id, codigo_mie, drm, pozo, locacion, fluido,
            volumen_estimado_m3, causa_probable, responsable, observaciones,
            estado, creado_por, fecha_hora_evento, fecha_creacion_registro,

            observador_apellido, observador_nombre,
            responsable_inst_apellido, responsable_inst_nombre,
            yacimiento, zona, nombre_instalacion,
            latitud, longitud, tipo_afectacion, tipo_derrame, tipo_instalacion,
            causa_inmediata, volumen_bruto_m3, volumen_gas_m3, ppm_agua,
            volumen_crudo_m3, area_afectada_m2, recursos_afectados,
            magnitud, aviso_sen, difusion_mediatica, aviso_autoridad,
            aviso_autoridad_fecha_hora, aviso_autoridad_emisor,
            aviso_autoridad_medio, aviso_autoridad_organismo,
            aviso_autoridad_contacto, aviso_superficiario,
            aviso_superficiario_fecha_hora, aviso_superficiario_emisor,
            aviso_superficiario_medio, aviso_superficiario_organismo,
            aviso_superficiario_contacto, medidas_inmediatas,
            aprobador_apellido, aprobador_nombre, fecha_hora_aprobacion
        )
        VALUES (
            @mie_id, @codigo_mie, @drm, @pozo, @locacion, @fluido,
            @vol_est, @causa_prob, @responsable, @observ,
            "ABIERTO", @creado_por, @fecha_evento, @fecha_creacion,

            @obs_apellido, @obs_nombre,
            @res_inst_ape, @res_inst_nom,
            @yacimiento, @zona, @nombre_inst,
            @latitud, @longitud, @tipo_afectacion, @tipo_derrame, @tipo_inst,
            @causa_inm, @vol_bruto, @vol_gas, @ppm_agua,
            @vol_crudo, @area_af, @rec_af,
            @magnitud, @av_sen, @dif_med, @av_aut,
            @av_aut_fh, @av_aut_emi,
            @av_aut_medio, @av_aut_org,
            @av_aut_cont, @av_sup,
            @av_sup_fh, @av_sup_emi,
            @av_sup_medio, @av_sup_org,
            @av_sup_cont, @med_inm,
            @ap_apellido, @ap_nombre, @ap_fh
        )
    """

    params = [
        ("mie_id", "INT64", mie_id),
        ("codigo_mie", "STRING", codigo),
        ("drm", "STRING", drm),
        ("pozo", "STRING", pozo),
        ("locacion", "STRING", locacion),
        ("fluido", "STRING", fluido),
        ("vol_est", "FLOAT64", float(volumen_estimado_m3) if volumen_estimado_m3 else None),
        ("causa_prob", "STRING", causa_probable),
        ("responsable", "STRING", responsable),
        ("observ", "STRING", observaciones),
        ("creado_por", "STRING", creado_por),
        ("fecha_evento", "TIMESTAMP", fecha_evento.isoformat()),
        ("fecha_creacion", "TIMESTAMP", ahora.isoformat()),

        ("obs_apellido", "STRING", observador_apellido),
        ("obs_nombre", "STRING", observador_nombre),
        ("res_inst_ape", "STRING", responsable_inst_apellido),
        ("res_inst_nom", "STRING", responsable_inst_nombre),
        ("yacimiento", "STRING", yacimiento),
        ("zona", "STRING", zona),
        ("nombre_inst", "STRING", nombre_instalacion),
        ("latitud", "STRING", latitud),
        ("longitud", "STRING", longitud),
        ("tipo_afectacion", "STRING", tipo_afectacion),
        ("tipo_derrame", "STRING", tipo_derrame),
        ("tipo_inst", "STRING", tipo_instalacion),
        ("causa_inm", "STRING", causa_inmediata),
        ("vol_bruto", "FLOAT64", volumen_bruto_m3),
        ("vol_gas", "FLOAT64", volumen_gas_m3),
        ("ppm_agua", "STRING", str(ppm_agua) if ppm_agua is not None else None),
        ("vol_crudo", "FLOAT64", volumen_crudo_m3),
        ("area_af", "FLOAT64", area_afectada_m2),
        ("rec_af", "STRING", recursos_afectados),
        ("magnitud", "STRING", magnitud),
        ("av_sen", "STRING", aviso_sen),
        ("dif_med", "STRING", difusion_mediatica),
        ("av_aut", "STRING", aviso_autoridad),
        ("av_aut_fh", "TIMESTAMP", aviso_autoridad_fecha_hora.isoformat() if aviso_autoridad_fecha_hora else None),
        ("av_aut_emi", "STRING", aviso_autoridad_emisor),
        ("av_aut_medio", "STRING", aviso_autoridad_medio),
        ("av_aut_org", "STRING", aviso_autoridad_organismo),
        ("av_aut_cont", "STRING", aviso_autoridad_contacto),
        ("av_sup", "STRING", aviso_superficiario),
        ("av_sup_fh", "TIMESTAMP", aviso_superficiario_fecha_hora.isoformat() if aviso_superficiario_fecha_hora else None),
        ("av_sup_emi", "STRING", aviso_superficiario_emisor),
        ("av_sup_medio", "STRING", aviso_superficiario_medio),
        ("av_sup_org", "STRING", aviso_superficiario_organismo),
        ("av_sup_cont", "STRING", aviso_superficiario_contacto),
        ("med_inm", "STRING", medidas_inmediatas),
        ("ap_apellido", "STRING", aprobador_apellido),
        ("ap_nombre", "STRING", aprobador_nombre),
        ("ap_fh", "TIMESTAMP", fecha_hora_aprobacion.isoformat() if fecha_hora_aprobacion else None),
    ]

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(n, t, v) for (n, t, v) in params
        ]
    )

    bq_client.query(query, job_config=job_config).result()
    return mie_id, codigo


# ---------------------------------------------------------
# 5) Insertar foto
# ---------------------------------------------------------
def insertar_foto(mie_id: int, tipo: str, blob_name: str):
    tabla = f"{PROJECT_ID}.{DATASET_ID}.mie_fotos"
    foto_id = obtener_siguiente_id("mie_fotos", "id")
    ahora = datetime.utcnow()

    row = [{
        "id": foto_id,
        "mie_id": mie_id,
        "tipo": tipo,
        "url_foto": blob_name,
        "fecha_hora": ahora.isoformat(),
    }]

    errors = bq_client.insert_rows_json(tabla, row)
    if errors:
        raise RuntimeError(errors)


# ---------------------------------------------------------
# 6) Listar IADE (historial)
# ---------------------------------------------------------
def listar_mie():
    query = f"""
        SELECT mie_id, codigo_mie, pozo, nombre_instalacion,
               estado, fecha_creacion_registro
        FROM `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        ORDER BY fecha_creacion_registro DESC
        LIMIT 300
    """
    return list(bq_client.query(query).result())


# ---------------------------------------------------------
# 7) Detalle de un IADE
# ---------------------------------------------------------
def obtener_mie_detalle(mie_id: int):
    query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        WHERE mie_id = @mie_id
    """
    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("mie_id", "INT64", mie_id)]
    )
    rows = list(bq_client.query(query, cfg).result())
    return rows[0] if rows else None


# ---------------------------------------------------------
# 8) Fotos (bytes)
# ---------------------------------------------------------
def obtener_fotos_mie(mie_id: int):
    query = f"""
        SELECT tipo, url_foto, fecha_hora
        FROM `{PROJECT_ID}.{DATASET_ID}.mie_fotos`
        WHERE mie_id = @id
        ORDER BY fecha_hora
    """
    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("id", "INT64", mie_id)]
    )
    rows = bq_client.query(query, cfg).result()

    bucket = storage_client.bucket(BUCKET_NAME)
    fotos = []

    for r in rows:
        if not r.url_foto:
            continue

        blob = bucket.blob(r.url_foto)
        data = blob.download_as_bytes()

        fotos.append({
            "tipo": r.tipo,
            "fecha_hora": r.fecha_hora,
            "data": data,
        })

    return fotos


# ---------------------------------------------------------
# 9) Actualizar datos básicos
# ---------------------------------------------------------
def actualizar_mie_basico(
    mie_id, drm, pozo, locacion, fluido,
    volumen_estimado_m3, causa_probable,
    responsable, observaciones
):
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        SET
            drm=@drm, pozo=@pozo, locacion=@locacion, fluido=@fluido,
            volumen_estimado_m3=@vol,
            causa_probable=@causa, responsable=@resp, observaciones=@obs
        WHERE mie_id=@id
    """

    cfg = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("drm", "STRING", drm),
            bigquery.ScalarQueryParameter("pozo", "STRING", pozo),
            bigquery.ScalarQueryParameter("locacion", "STRING", locacion),
            bigquery.ScalarQueryParameter("fluido", "STRING", fluido),
            bigquery.ScalarQueryParameter(
                "vol", "FLOAT64",
                float(volumen_estimado_m3) if volumen_estimado_m3 else None
            ),
            bigquery.ScalarQueryParameter("causa", "STRING", causa_probable),
            bigquery.ScalarQueryParameter("resp", "STRING", responsable),
            bigquery.ScalarQueryParameter("obs", "STRING", observaciones),
            bigquery.ScalarQueryParameter("id", "INT64", mie_id),
        ]
    )

    bq_client.query(query, cfg).result()


# ---------------------------------------------------------
# 9.5) Actualizar MIA completo (para el botón "Editar")
# ---------------------------------------------------------
def actualizar_mie_completo(
    mie_id: int,
    creado_por=None,
    fecha_hora_evento=None,

    observador_apellido=None,
    observador_nombre=None,
    responsable_inst_apellido=None,
    responsable_inst_nombre=None,

    yacimiento=None,
    zona=None,
    nombre_instalacion=None,
    latitud=None,
    longitud=None,

    tipo_afectacion=None,
    tipo_derrame=None,
    tipo_instalacion=None,
    causa_inmediata=None,

    volumen_bruto_m3=None,
    volumen_gas_m3=None,
    ppm_agua=None,
    volumen_crudo_m3=None,
    area_afectada_m2=None,

    recursos_afectados=None,
    causa_probable=None,
    responsable=None,
    observaciones=None,
    medidas_inmediatas=None,

    aprobador_apellido=None,
    aprobador_nombre=None,
    fecha_hora_aprobacion=None,
):
    """
    Actualiza campos editables del MIA sin tocar:
    - mie_id / codigo_mie / drm
    - estado / fecha_creacion_registro
    - remediación
    """
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        SET
            creado_por = @creado_por,
            fecha_hora_evento = @fecha_hora_evento,

            observador_apellido = @obs_apellido,
            observador_nombre = @obs_nombre,
            responsable_inst_apellido = @res_inst_ape,
            responsable_inst_nombre = @res_inst_nom,

            yacimiento = @yacimiento,
            zona = @zona,
            nombre_instalacion = @nombre_inst,
            latitud = @latitud,
            longitud = @longitud,

            tipo_afectacion = @tipo_afectacion,
            tipo_derrame = @tipo_derrame,
            tipo_instalacion = @tipo_instalacion,
            causa_inmediata = @causa_inmediata,

            volumen_bruto_m3 = @vol_bruto,
            volumen_gas_m3 = @vol_gas,
            ppm_agua = @ppm_agua,
            volumen_crudo_m3 = @vol_crudo,
            area_afectada_m2 = @area_afectada_m2,

            recursos_afectados = @recursos_afectados,
            causa_probable = @causa_probable,
            responsable = @responsable,
            observaciones = @observaciones,
            medidas_inmediatas = @medidas_inmediatas,

            aprobador_apellido = @aprob_apellido,
            aprobador_nombre = @aprob_nombre,
            fecha_hora_aprobacion = @fh_aprob

        WHERE mie_id = @id
    """

    cfg = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("creado_por", "STRING", creado_por),
            bigquery.ScalarQueryParameter(
                "fecha_hora_evento", "TIMESTAMP",
                fecha_hora_evento.isoformat() if fecha_hora_evento else None
            ),

            bigquery.ScalarQueryParameter("obs_apellido", "STRING", observador_apellido),
            bigquery.ScalarQueryParameter("obs_nombre", "STRING", observador_nombre),
            bigquery.ScalarQueryParameter("res_inst_ape", "STRING", responsable_inst_apellido),
            bigquery.ScalarQueryParameter("res_inst_nom", "STRING", responsable_inst_nombre),

            bigquery.ScalarQueryParameter("yacimiento", "STRING", yacimiento),
            bigquery.ScalarQueryParameter("zona", "STRING", zona),
            bigquery.ScalarQueryParameter("nombre_inst", "STRING", nombre_instalacion),
            bigquery.ScalarQueryParameter("latitud", "STRING", latitud),
            bigquery.ScalarQueryParameter("longitud", "STRING", longitud),

            bigquery.ScalarQueryParameter("tipo_afectacion", "STRING", tipo_afectacion),
            bigquery.ScalarQueryParameter("tipo_derrame", "STRING", tipo_derrame),
            bigquery.ScalarQueryParameter("tipo_instalacion", "STRING", tipo_instalacion),
            bigquery.ScalarQueryParameter("causa_inmediata", "STRING", causa_inmediata),

            bigquery.ScalarQueryParameter("vol_bruto", "FLOAT64", float(volumen_bruto_m3) if volumen_bruto_m3 is not None else None),
            bigquery.ScalarQueryParameter("vol_gas", "FLOAT64", float(volumen_gas_m3) if volumen_gas_m3 is not None else None),
            # Tu esquema actual guarda ppm_agua como STRING:
            bigquery.ScalarQueryParameter("ppm_agua", "STRING", str(ppm_agua) if ppm_agua is not None else None),
            bigquery.ScalarQueryParameter("vol_crudo", "FLOAT64", float(volumen_crudo_m3) if volumen_crudo_m3 is not None else None),
            bigquery.ScalarQueryParameter("area_afectada_m2", "FLOAT64", float(area_afectada_m2) if area_afectada_m2 is not None else None),

            bigquery.ScalarQueryParameter("recursos_afectados", "STRING", recursos_afectados),
            bigquery.ScalarQueryParameter("causa_probable", "STRING", causa_probable),
            bigquery.ScalarQueryParameter("responsable", "STRING", responsable),
            bigquery.ScalarQueryParameter("observaciones", "STRING", observaciones),
            bigquery.ScalarQueryParameter("medidas_inmediatas", "STRING", medidas_inmediatas),

            bigquery.ScalarQueryParameter("aprob_apellido", "STRING", aprobador_apellido),
            bigquery.ScalarQueryParameter("aprob_nombre", "STRING", aprobador_nombre),
            bigquery.ScalarQueryParameter(
                "fh_aprob", "TIMESTAMP",
                fecha_hora_aprobacion.isoformat() if fecha_hora_aprobacion else None
            ),

            bigquery.ScalarQueryParameter("id", "INT64", mie_id),
        ]
    )

    bq_client.query(query, cfg).result()


# ---------------------------------------------------------
# 10) Cerrar IADE con remediación
# ---------------------------------------------------------
def cerrar_mie_con_remediacion(
    mie_id,
    fecha_fin_saneamiento,
    volumen_tierra_levantada,
    destino_tierra_impactada,
    volumen_liquido_recuperado,
    comentarios,
    aprob_apellido,
    aprob_nombre,
):

    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        SET
            estado = "CERRADO",
            rem_fecha_fin_saneamiento = @fh,
            rem_volumen_tierra_levantada = @vol_tierra,
            rem_destino_tierra_impactada = @destino,
            rem_volumen_liquido_recuperado = @vol_liq,
            rem_comentarios = @coment,
            rem_aprobador_apellido = @ap_ape,
            rem_aprobador_nombre = @ap_nom,

            -- Campos antiguos (compatibilidad)
            rem_fecha = @fh,
            rem_responsable = CONCAT(
                COALESCE(@ap_ape, ''), " ", COALESCE(@ap_nom, '')
            ),
            rem_detalle = @coment

        WHERE mie_id = @id
    """

    cfg = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("fh", "TIMESTAMP", fecha_fin_saneamiento.isoformat()),
            bigquery.ScalarQueryParameter("vol_tierra", "FLOAT64",
                float(volumen_tierra_levantada) if volumen_tierra_levantada else None),
            bigquery.ScalarQueryParameter("destino", "STRING", destino_tierra_impactada),
            bigquery.ScalarQueryParameter("vol_liq", "FLOAT64",
                float(volumen_liquido_recuperado) if volumen_liquido_recuperado else None),
            bigquery.ScalarQueryParameter("coment", "STRING", comentarios),
            bigquery.ScalarQueryParameter("ap_ape", "STRING", aprob_apellido),
            bigquery.ScalarQueryParameter("ap_nom", "STRING", aprob_nombre),
            bigquery.ScalarQueryParameter("id", "INT64", mie_id),
        ]
    )

    bq_client.query(query, cfg).result()


# ---------------------------------------------------------
# 11) Obtener todos los IADE (para exportar a Excel)
# ---------------------------------------------------------
def obtener_todos_mie():
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        ORDER BY fecha_creacion_registro
    """
    return list(bq_client.query(query).result())










