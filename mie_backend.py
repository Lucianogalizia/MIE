# ============================================================
# mie_backend.py — backend oficial MIA / MIE
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
# Utils
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


def generar_codigo_mie(num: int) -> str:
    year = datetime.now().year
    return f"MIE-{year}-{num:04d}"


# ---------------------------------------------------------
# Bucket / Fotos
# ---------------------------------------------------------
def subir_foto_a_bucket(file_obj, nombre_destino: str) -> str:
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(nombre_destino)

    data = file_obj.read()
    blob.upload_from_file(BytesIO(data), content_type=file_obj.type)

    return nombre_destino


def insertar_foto(mie_id: int, tipo: str, blob_name: str):
    tabla = f"{PROJECT_ID}.{DATASET_ID}.mie_fotos"
    foto_id = obtener_siguiente_id("mie_fotos", "id")
    ahora = datetime.utcnow()

    row = [{
        "id": foto_id,
        "mie_id": mie_id,
        "tipo": tipo,               # ANTES / DESPUES
        "url_foto": blob_name,
        "fecha_hora": ahora.isoformat(),
    }]

    errors = bq_client.insert_rows_json(tabla, row)
    if errors:
        raise RuntimeError(errors)


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
# MIA - Insertar
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
            medidas_inmediatas,
            aprobador_apellido, aprobador_nombre, fecha_hora_aprobacion
        )
        VALUES (
            @mie_id, @codigo, @drm, @pozo, @locacion, @fluido,
            @vol_est, @causa_prob, @resp, @obs,
            "ABIERTO", @creado_por, @fh_evento, @fh_creacion,

            @obs_ap, @obs_no,
            @res_inst_ap, @res_inst_no,
            @yacimiento, @zona, @nombre_inst,
            @lat, @lon, @tipo_af, @tipo_der, @tipo_inst,
            @causa_inm, @vol_bruto, @vol_gas, @ppm,
            @vol_crudo, @area_af, @rec_af,
            @med_inm,
            @ap_ap, @ap_no, @fh_ap
        )
    """

    params = [
        ("mie_id", "INT64", mie_id),
        ("codigo", "STRING", codigo),
        ("drm", "STRING", drm),
        ("pozo", "STRING", pozo),
        ("locacion", "STRING", locacion),
        ("fluido", "STRING", fluido),
        ("vol_est", "FLOAT64", volumen_estimado_m3),
        ("causa_prob", "STRING", causa_probable),
        ("resp", "STRING", responsable),
        ("obs", "STRING", observaciones),
        ("creado_por", "STRING", creado_por),
        ("fh_evento", "TIMESTAMP", fecha_evento.isoformat()),
        ("fh_creacion", "TIMESTAMP", ahora.isoformat()),

        ("obs_ap", "STRING", observador_apellido),
        ("obs_no", "STRING", observador_nombre),
        ("res_inst_ap", "STRING", responsable_inst_apellido),
        ("res_inst_no", "STRING", responsable_inst_nombre),
        ("yacimiento", "STRING", yacimiento),
        ("zona", "STRING", zona),
        ("nombre_inst", "STRING", nombre_instalacion),
        ("lat", "STRING", latitud),
        ("lon", "STRING", longitud),
        ("tipo_af", "STRING", tipo_afectacion),
        ("tipo_der", "STRING", tipo_derrame),
        ("tipo_inst", "STRING", tipo_instalacion),
        ("causa_inm", "STRING", causa_inmediata),
        ("vol_bruto", "FLOAT64", volumen_bruto_m3),
        ("vol_gas", "FLOAT64", volumen_gas_m3),
        ("ppm", "STRING", str(ppm_agua) if ppm_agua is not None else None),
        ("vol_crudo", "FLOAT64", volumen_crudo_m3),
        ("area_af", "FLOAT64", area_afectada_m2),
        ("rec_af", "STRING", recursos_afectados),
        ("med_inm", "STRING", medidas_inmediatas),
        ("ap_ap", "STRING", aprobador_apellido),
        ("ap_no", "STRING", aprobador_nombre),
        ("fh_ap", "TIMESTAMP", fecha_hora_aprobacion.isoformat() if fecha_hora_aprobacion else None),
    ]

    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter(n, t, v) for n, t, v in params]
    )

    bq_client.query(query, cfg).result()
    return mie_id, codigo


# ---------------------------------------------------------
# Listados / Detalle
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


def obtener_mie_detalle(mie_id: int):
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        WHERE mie_id = @id
    """
    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("id", "INT64", mie_id)]
    )
    rows = list(bq_client.query(query, cfg).result())
    return rows[0] if rows else None


# ---------------------------------------------------------
# ACTUALIZAR MIA (SOLO CARGA – botón Editar)
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
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        SET
            creado_por=@creado_por,
            fecha_hora_evento=@fh_evento,

            observador_apellido=@obs_ap,
            observador_nombre=@obs_no,
            responsable_inst_apellido=@res_inst_ap,
            responsable_inst_nombre=@res_inst_no,

            yacimiento=@yac,
            zona=@zona,
            nombre_instalacion=@nombre_inst,
            latitud=@lat,
            longitud=@lon,

            tipo_afectacion=@tipo_af,
            tipo_derrame=@tipo_der,
            tipo_instalacion=@tipo_inst,
            causa_inmediata=@causa_inm,

            volumen_bruto_m3=@vol_bruto,
            volumen_gas_m3=@vol_gas,
            ppm_agua=@ppm,
            volumen_crudo_m3=@vol_crudo,
            area_afectada_m2=@area_af,

            recursos_afectados=@rec_af,
            causa_probable=@causa_prob,
            responsable=@resp,
            observaciones=@obs,
            medidas_inmediatas=@med_inm,

            aprobador_apellido=@ap_ap,
            aprobador_nombre=@ap_no,
            fecha_hora_aprobacion=@fh_ap

        WHERE mie_id=@id
    """

    params = [
        ("creado_por", "STRING", creado_por),
        ("fh_evento", "TIMESTAMP", fecha_hora_evento.isoformat() if fecha_hora_evento else None),
        ("obs_ap", "STRING", observador_apellido),
        ("obs_no", "STRING", observador_nombre),
        ("res_inst_ap", "STRING", responsable_inst_apellido),
        ("res_inst_no", "STRING", responsable_inst_nombre),
        ("yac", "STRING", yacimiento),
        ("zona", "STRING", zona),
        ("nombre_inst", "STRING", nombre_instalacion),
        ("lat", "STRING", latitud),
        ("lon", "STRING", longitud),
        ("tipo_af", "STRING", tipo_afectacion),
        ("tipo_der", "STRING", tipo_derrame),
        ("tipo_inst", "STRING", tipo_instalacion),
        ("causa_inm", "STRING", causa_inmediata),
        ("vol_bruto", "FLOAT64", volumen_bruto_m3),
        ("vol_gas", "FLOAT64", volumen_gas_m3),
        ("ppm", "STRING", str(ppm_agua) if ppm_agua is not None else None),
        ("vol_crudo", "FLOAT64", volumen_crudo_m3),
        ("area_af", "FLOAT64", area_afectada_m2),
        ("rec_af", "STRING", recursos_afectados),
        ("causa_prob", "STRING", causa_probable),
        ("resp", "STRING", responsable),
        ("obs", "STRING", observaciones),
        ("med_inm", "STRING", medidas_inmediatas),
        ("ap_ap", "STRING", aprobador_apellido),
        ("ap_no", "STRING", aprobador_nombre),
        ("fh_ap", "TIMESTAMP", fecha_hora_aprobacion.isoformat() if fecha_hora_aprobacion else None),
        ("id", "INT64", mie_id),
    ]

    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter(n, t, v) for n, t, v in params]
    )
    bq_client.query(query, cfg).result()


# ---------------------------------------------------------
# CIERRE / REMEDIACIÓN (NO SE USA EN EDITAR)
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
            estado="CERRADO",
            rem_fecha_fin_saneamiento=@fh,
            rem_volumen_tierra_levantada=@vol_tierra,
            rem_destino_tierra_impactada=@destino,
            rem_volumen_liquido_recuperado=@vol_liq,
            rem_comentarios=@coment,
            rem_aprobador_apellido=@ap_ap,
            rem_aprobador_nombre=@ap_no,
            rem_fecha=@fh,
            rem_responsable=CONCAT(COALESCE(@ap_ap,''),' ',COALESCE(@ap_no,'')),
            rem_detalle=@coment
        WHERE mie_id=@id
    """

    cfg = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("fh", "TIMESTAMP", fecha_fin_saneamiento.isoformat()),
            bigquery.ScalarQueryParameter("vol_tierra", "FLOAT64", volumen_tierra_levantada),
            bigquery.ScalarQueryParameter("destino", "STRING", destino_tierra_impactada),
            bigquery.ScalarQueryParameter("vol_liq", "FLOAT64", volumen_liquido_recuperado),
            bigquery.ScalarQueryParameter("coment", "STRING", comentarios),
            bigquery.ScalarQueryParameter("ap_ap", "STRING", aprob_apellido),
            bigquery.ScalarQueryParameter("ap_no", "STRING", aprob_nombre),
            bigquery.ScalarQueryParameter("id", "INT64", mie_id),
        ]
    )
    bq_client.query(query, cfg).result()


# ---------------------------------------------------------
# Exportar
# ---------------------------------------------------------
def obtener_todos_mie():
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        ORDER BY fecha_creacion_registro
    """
    return list(bq_client.query(query).result())
