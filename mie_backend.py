# mie_backend.py
from datetime import datetime
from io import BytesIO

from google.cloud import bigquery, storage
from config import PROJECT_ID, DATASET_ID, BUCKET_NAME

# Clientes de BigQuery y Storage
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
# 3) Subir foto al bucket y devolver URL pública
# ---------------------------------------------------------
def subir_foto_a_bucket(file_obj, nombre_destino: str) -> str:
    """
    Sube la foto al bucket y devuelve la URL.
    file_obj = archivo recibido de st.file_uploader
    """
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(nombre_destino)

    data = file_obj.read()
    blob.upload_from_file(BytesIO(data), content_type=file_obj.type)

    # URL accesible
    return f"https://storage.googleapis.com/{BUCKET_NAME}/{nombre_destino}"


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
# ---------------------------------------------------------
def insertar_foto(mie_id: int, tipo: str, url_foto: str):
    tabla = f"{PROJECT_ID}.{DATASET_ID}.mie_fotos"
    foto_id = obtener_siguiente_id("mie_fotos", "id")
    ahora = datetime.utcnow()

    rows = [{
        "id": foto_id,
        "mie_id": mie_id,
        "tipo": tipo,       # ANTES o DESPUES
        "url_foto": url_foto,
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
# 8) Fotos asociadas a un MIE (todas)
# ---------------------------------------------------------
def obtener_fotos_mie(mie_id: int):
    query = f"""
        SELECT tipo, url_foto, fecha_hora
        FROM `{PROJECT_ID}.{DATASET_ID}.mie_fotos`
        WHERE mie_id = @mie_id
        ORDER BY fecha_hora
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("mie_id", "INT64", mie_id)]
    )
    return list(bq_client.query(query, job_config=job_config).result())
