# mie_backend.py
from datetime import datetime
from io import BytesIO

from google.cloud import bigquery, storage
from config import PROJECT_ID, DATASET_ID, BUCKET_NAME

# Clientes globales
bq_client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)


# ---------------------------------------------------------
# 1) Obtener el próximo ID para una tabla
# ---------------------------------------------------------
def obtener_siguiente_id(tabla: str, campo: str) -> int:
    query = f"""
        SELECT MAX({campo}) AS max_id
        FROM `{PROJECT_ID}.{DATASET_ID}.{tabla}`
    """
    result = bq_client.query(query).result()
    for row in result:
        if row.max_id is None:
            return 1
        return row.max_id + 1
    return 1


# ---------------------------------------------------------
# 2) Generar código MIE tipo: MIE-2025-0001
# ---------------------------------------------------------
def generar_codigo_mie(mie_id: int) -> str:
    year = datetime.now().year
    return f"MIE-{year}-{mie_id:04d}"


# ---------------------------------------------------------
# 3) Subir foto al bucket y devolver NOMBRE DE OBJETO (no URL)
# ---------------------------------------------------------
def subir_foto_a_bucket(file_obj, nombre_destino: str) -> str:
    """
    Sube la foto al bucket y devuelve el nombre del objeto (blob_name),
    no una URL pública.
    """
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(nombre_destino)

    data = file_obj.read()
    blob.upload_from_file(BytesIO(data), content_type=file_obj.type)

    # Devolvemos solo el path interno del objeto
    return nombre_destino


# ---------------------------------------------------------
# 4) Insertar un nuevo MIE en BigQuery
# ---------------------------------------------------------
def insertar_mie(
    drm: str,
    pozo: str,
    locacion: str,
    fluido: str,
    volumen_estimado_m3: float | None,
    causa_probable: str,
    responsable: str,
    observaciones: str,
    creado_por: str,
    fecha_hora_evento: datetime | None = None,
) -> tuple[int, str]:

    tabla = f"{PROJECT_ID}.{DATASET_ID}.mie_eventos"

    mie_id = obtener_siguiente_id("mie_eventos", "mie_id")
    codigo = generar_codigo_mie(mie_id)
    ahora = datetime.utcnow()

    rows = [{
        "mie_id": mie_id,
        "codigo_mie": codigo,
        "drm": drm,
        "pozo": pozo,
        "locacion": locacion,
        "fluido": fluido,
        "volumen_estimado_m3": float(volumen_estimado_m3) if volumen_estimado_m3 else None,
        "causa_probable": causa_probable,
        "responsable": responsable,
        "observaciones": observaciones,
        "estado": "ABIERTO",
        "creado_por": creado_por,
        "fecha_hora_evento": (fecha_hora_evento or ahora).isoformat(),
        "fecha_creacion_registro": ahora.isoformat(),
    }]

    errors = bq_client.insert_rows_json(tabla, rows)
    if errors:
        raise RuntimeError(errors)

    return mie_id, codigo


# ---------------------------------------------------------
# 5) Insertar registro de foto en tabla mie_fotos
#     (guardamos blob_name, no URL)
# ---------------------------------------------------------
def insertar_foto(mie_id: int, tipo: str, blob_name: str):
    tabla = f"{PROJECT_ID}.{DATASET_ID}.mie_fotos"
    foto_id = obtener_siguiente_id("mie_fotos", "id")
    ahora = datetime.utcnow()

    rows = [{
        "id": foto_id,
        "mie_id": mie_id,
        "tipo": tipo,           # ANTES o DESPUES
        "url_foto": blob_name,  # acá guardamos el nombre del objeto
        "fecha_hora": ahora.isoformat(),
    }]

    errors = bq_client.insert_rows_json(tabla, rows)
    if errors:
        raise RuntimeError(errors)


# ---------------------------------------------------------
# 6) Listar los últimos MIE (para historial)
# ---------------------------------------------------------
def listar_mie():
    query = f"""
        SELECT mie_id, codigo_mie, pozo, estado, fecha_creacion_registro
        FROM `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        ORDER BY fecha_creacion_registro DESC
        LIMIT 300
    """
    return list(bq_client.query(query).result())


# ---------------------------------------------------------
# 7) Traer detalle de un MIE específico
# ---------------------------------------------------------
def obtener_mie_detalle(mie_id: int):
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        WHERE mie_id = @mie_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("mie_id", "INT64", mie_id)]
    )
    rows = list(bq_client.query(query, job_config=job_config).result())
    return rows[0] if rows else None


# ---------------------------------------------------------
# 8) Fotos asociadas a un MIE (descargamos bytes)
# ---------------------------------------------------------
def obtener_fotos_mie(mie_id: int):
    """
    Devuelve una lista de dicts:
    {
      "tipo": ...,
      "fecha_hora": ...,
      "data": bytes_de_la_imagen
    }
    """
    query = f"""
        SELECT tipo, url_foto, fecha_hora
        FROM `{PROJECT_ID}.{DATASET_ID}.mie_fotos`
        WHERE mie_id = @mie_id
        ORDER BY fecha_hora
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("mie_id", "INT64", mie_id)]
    )
    rows = bq_client.query(query, job_config=job_config).result()

    bucket = storage_client.bucket(BUCKET_NAME)
    fotos = []

    for row in rows:
        blob_name = row.url_foto
        if not blob_name:
            continue

        blob = bucket.blob(blob_name)
        data = blob.download_as_bytes()   # leemos la imagen

        fotos.append({
            "tipo": row.tipo,
            "fecha_hora": row.fecha_hora,
            "data": data,
        })

    return fotos


# ---------------------------------------------------------
# 9) Actualizar datos básicos de un MIE (editar)
# ---------------------------------------------------------
def actualizar_mie_basico(
    mie_id: int,
    drm: str,
    pozo: str,
    locacion: str,
    fluido: str,
    volumen_estimado_m3: float | None,
    causa_probable: str,
    responsable: str,
    observaciones: str,
):
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        SET
          drm = @drm,
          pozo = @pozo,
          locacion = @locacion,
          fluido = @fluido,
          volumen_estimado_m3 = @volumen,
          causa_probable = @causa_probable,
          responsable = @responsable,
          observaciones = @observaciones
        WHERE mie_id = @mie_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("drm", "STRING", drm),
            bigquery.ScalarQueryParameter("pozo", "STRING", pozo),
            bigquery.ScalarQueryParameter("locacion", "STRING", locacion),
            bigquery.ScalarQueryParameter("fluido", "STRING", fluido),
            bigquery.ScalarQueryParameter(
                "volumen",
                "FLOAT64",
                float(volumen_estimado_m3) if volumen_estimado_m3 is not None else None,
            ),
            bigquery.ScalarQueryParameter("causa_probable", "STRING", causa_probable),
            bigquery.ScalarQueryParameter("responsable", "STRING", responsable),
            bigquery.ScalarQueryParameter("observaciones", "STRING", observaciones),
            bigquery.ScalarQueryParameter("mie_id", "INT64", mie_id),
        ]
    )

    bq_client.query(query, job_config=job_config).result()


# ---------------------------------------------------------
# 10) Cerrar MIE con datos de remediación
# ---------------------------------------------------------
def cerrar_mie_con_remediacion(
    mie_id: int,
    rem_fecha: datetime,
    rem_responsable: str,
    rem_detalle: str,
):
    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.mie_eventos`
        SET
          rem_fecha = @rem_fecha,
          rem_responsable = @rem_responsable,
          rem_detalle = @rem_detalle,
          estado = "CERRADO"
        WHERE mie_id = @mie_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "rem_fecha", "TIMESTAMP", rem_fecha.isoformat()
            ),
            bigquery.ScalarQueryParameter(
                "rem_responsable", "STRING", rem_responsable
            ),
            bigquery.ScalarQueryParameter("rem_detalle", "STRING", rem_detalle),
            bigquery.ScalarQueryParameter("mie_id", "INT64", mie_id),
        ]
    )

    bq_client.query(query, job_config=job_config).result()







