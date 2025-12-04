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
# 4) Insertar un nuevo MIE en BigQuery (versión extendida)
# ---------------------------------------------------------
def insertar_mie(
    drm: str | None,
    pozo: str | None,
    locacion: str | None,
    fluido: str,
    volumen_estimado_m3: float | None,
    causa_probable: str,
    responsable: str,
    observaciones: str,
    creado_por: str,
    fecha_hora_evento: datetime | None = None,

    # 🔹 NUEVOS CAMPOS
    observador_apellido: str | None = None,
    observador_nombre: str | None = None,
    responsable_inst_apellido: str | None = None,
    responsable_inst_nombre: str | None = None,
    yacimiento: str | None = None,
    zona: str | None = None,
    nombre_instalacion: str | None = None,
    latitud: str | None = None,
    longitud: str | None = None,
    tipo_afectacion: str | None = None,
    tipo_derrame: str | None = None,
    tipo_instalacion: str | None = None,
    causa_inmediata: str | None = None,
    volumen_bruto_m3: float | None = None,
    volumen_gas_m3: float | None = None,
    ppm_agua: str | None = None,
    volumen_crudo_m3: float | None = None,
    area_afectada_m2: float | None = None,
    recursos_afectados: str | None = None,
    magnitud: str | None = None,
    aviso_sen: str | None = None,
    difusion_mediatica: str | None = None,
    aviso_autoridad: str | None = None,
    aviso_autoridad_fecha_hora: datetime | None = None,
    aviso_autoridad_emisor: str | None = None,
    aviso_autoridad_medio: str | None = None,
    aviso_autoridad_organismo: str | None = None,
    aviso_autoridad_contacto: str | None = None,
    aviso_superficiario: str | None = None,
    aviso_superficiario_fecha_hora: datetime | None = None,
    aviso_superficiario_emisor: str | None = None,
    aviso_superficiario_medio: str | None = None,
    aviso_superficiario_organismo: str | None = None,
    aviso_superficiario_contacto: str | None = None,
    medidas_inmediatas: str | None = None,
    aprobador_apellido: str | None = None,
    aprobador_nombre: str | None = None,
    fecha_hora_aprobacion: datetime | None = None,
) -> tuple[int, str]:

    tabla = f"{PROJECT_ID}.{DATASET_ID}.mie_eventos"

    mie_id = obtener_siguiente_id("mie_eventos", "mie_id")
    codigo = generar_codigo_mie(mie_id)

    # Si el usuario no cargó DRM, lo generamos igual que el código MIE
    if not drm:
        drm = codigo

    ahora = datetime.utcnow()
    fecha_evento = fecha_hora_evento or ahora

    query = f"""
        INSERT INTO `{tabla}` (
            mie_id,
            codigo_mie,
            drm,
            pozo,
            locacion,
            fluido,
            volumen_estimado_m3,
            causa_probable,
            responsable,
            observaciones,
            estado,
            creado_por,
            fecha_hora_evento,
            fecha_creacion_registro,

            observador_apellido,
            observador_nombre,
            responsable_inst_apellido,
            responsable_inst_nombre,
            yacimiento,
            zona,
            nombre_instalacion,
            latitud,
            longitud,
            tipo_afectacion,
            tipo_derrame,
            tipo_instalacion,
            causa_inmediata,
            volumen_bruto_m3,
            volumen_gas_m3,
            ppm_agua,
            volumen_crudo_m3,
            area_afectada_m2,
            recursos_afectados,
            magnitud,
            aviso_sen,
            difusion_mediatica,
            aviso_autoridad,
            aviso_autoridad_fecha_hora,
            aviso_autoridad_emisor,
            aviso_autoridad_medio,
            aviso_autoridad_organismo,
            aviso_autoridad_contacto,
            aviso_superficiario,
            aviso_superficiario_fecha_hora,
            aviso_superficiario_emisor,
            aviso_superficiario_medio,
            aviso_superficiario_organismo,
            aviso_superficiario_contacto,
            medidas_inmediatas,
            aprobador_apellido,
            aprobador_nombre,
            fecha_hora_aprobacion
        )
        VALUES (
            @mie_id,
            @codigo_mie,
            @drm,
            @pozo,
            @locacion,
            @fluido,
            @volumen,
            @causa_probable,
            @responsable,
            @observaciones,
            @estado,
            @creado_por,
            @fecha_evento,
            @fecha_creacion,

            @observador_apellido,
            @observador_nombre,
            @responsable_inst_apellido,
            @responsable_inst_nombre,
            @yacimiento,
            @zona,
            @nombre_instalacion,
            @latitud,
            @longitud,
            @tipo_afectacion,
            @tipo_derrame,
            @tipo_instalacion,
            @causa_inmediata,
            @volumen_bruto_m3,
            @volumen_gas_m3,
            @ppm_agua,
            @volumen_crudo_m3,
            @area_afectada_m2,
            @recursos_afectados,
            @magnitud,
            @aviso_sen,
            @difusion_mediatica,
            @aviso_autoridad,
            @aviso_autoridad_fecha_hora,
            @aviso_autoridad_emisor,
            @aviso_autoridad_medio,
            @aviso_autoridad_organismo,
            @aviso_autoridad_contacto,
            @aviso_superficiario,
            @aviso_superficiario_fecha_hora,
            @aviso_superficiario_emisor,
            @aviso_superficiario_medio,
            @aviso_superficiario_organismo,
            @aviso_superficiario_contacto,
            @medidas_inmediatas,
            @aprobador_apellido,
            @aprobador_nombre,
            @fecha_hora_aprobacion
        )
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("mie_id", "INT64", mie_id),
            bigquery.ScalarQueryParameter("codigo_mie", "STRING", codigo),
            bigquery.ScalarQueryParameter("drm", "STRING", drm),
            bigquery.ScalarQueryParameter("pozo", "STRING", pozo),
            bigquery.ScalarQueryParameter("locacion", "STRING", locacion),
            bigquery.ScalarQueryParameter("fluido", "STRING", fluido),
            bigquery.ScalarQueryParameter(
                "volumen", "FLOAT64",
                float(volumen_estimado_m3) if volumen_estimado_m3 is not None else None,
            ),
            bigquery.ScalarQueryParameter("causa_probable", "STRING", causa_probable),
            bigquery.ScalarQueryParameter("responsable", "STRING", responsable),
            bigquery.ScalarQueryParameter("observaciones", "STRING", observaciones),
            bigquery.ScalarQueryParameter("estado", "STRING", "ABIERTO"),
            bigquery.ScalarQueryParameter("creado_por", "STRING", creado_por),
            bigquery.ScalarQueryParameter(
                "fecha_evento", "TIMESTAMP", fecha_evento.isoformat()
            ),
            bigquery.ScalarQueryParameter(
                "fecha_creacion", "TIMESTAMP", ahora.isoformat()
            ),

            bigquery.ScalarQueryParameter("observador_apellido", "STRING", observador_apellido),
            bigquery.ScalarQueryParameter("observador_nombre", "STRING", observador_nombre),
            bigquery.ScalarQueryParameter("responsable_inst_apellido", "STRING", responsable_inst_apellido),
            bigquery.ScalarQueryParameter("responsable_inst_nombre", "STRING", responsable_inst_nombre),
            bigquery.ScalarQueryParameter("yacimiento", "STRING", yacimiento),
            bigquery.ScalarQueryParameter("zona", "STRING", zona),
            bigquery.ScalarQueryParameter("nombre_instalacion", "STRING", nombre_instalacion),
            bigquery.ScalarQueryParameter("latitud", "STRING", latitud),
            bigquery.ScalarQueryParameter("longitud", "STRING", longitud),
            bigquery.ScalarQueryParameter("tipo_afectacion", "STRING", tipo_afectacion),
            bigquery.ScalarQueryParameter("tipo_derrame", "STRING", tipo_derrame),
            bigquery.ScalarQueryParameter("tipo_instalacion", "STRING", tipo_instalacion),
            bigquery.ScalarQueryParameter("causa_inmediata", "STRING", causa_inmediata),
            bigquery.ScalarQueryParameter(
                "volumen_bruto_m3", "FLOAT64",
                float(volumen_bruto_m3) if volumen_bruto_m3 is not None else None,
            ),
            bigquery.ScalarQueryParameter(
                "volumen_gas_m3", "FLOAT64",
                float(volumen_gas_m3) if volumen_gas_m3 is not None else None,
            ),
            bigquery.ScalarQueryParameter("ppm_agua", "STRING", ppm_agua),
            bigquery.ScalarQueryParameter(
                "volumen_crudo_m3", "FLOAT64",
                float(volumen_crudo_m3) if volumen_crudo_m3 is not None else None,
            ),
            bigquery.ScalarQueryParameter(
                "area_afectada_m2", "FLOAT64",
                float(area_afectada_m2) if area_afectada_m2 is not None else None,
            ),
            bigquery.ScalarQueryParameter("recursos_afectados", "STRING", recursos_afectados),
            bigquery.ScalarQueryParameter("magnitud", "STRING", magnitud),
            bigquery.ScalarQueryParameter("aviso_sen", "STRING", aviso_sen),
            bigquery.ScalarQueryParameter("difusion_mediatica", "STRING", difusion_mediatica),
            bigquery.ScalarQueryParameter("aviso_autoridad", "STRING", aviso_autoridad),
            bigquery.ScalarQueryParameter(
                "aviso_autoridad_fecha_hora", "TIMESTAMP",
                aviso_autoridad_fecha_hora.isoformat() if aviso_autoridad_fecha_hora else None,
            ),
            bigquery.ScalarQueryParameter("aviso_autoridad_emisor", "STRING", aviso_autoridad_emisor),
            bigquery.ScalarQueryParameter("aviso_autoridad_medio", "STRING", aviso_autoridad_medio),
            bigquery.ScalarQueryParameter("aviso_autoridad_organismo", "STRING", aviso_autoridad_organismo),
            bigquery.ScalarQueryParameter("aviso_autoridad_contacto", "STRING", aviso_autoridad_contacto),
            bigquery.ScalarQueryParameter("aviso_superficiario", "STRING", aviso_superficiario),
            bigquery.ScalarQueryParameter(
                "aviso_superficiario_fecha_hora", "TIMESTAMP",
                aviso_superficiario_fecha_hora.isoformat() if aviso_superficiario_fecha_hora else None,
            ),
            bigquery.ScalarQueryParameter("aviso_superficiario_emisor", "STRING", aviso_superficiario_emisor),
            bigquery.ScalarQueryParameter("aviso_superficiario_medio", "STRING", aviso_superficiario_medio),
            bigquery.ScalarQueryParameter("aviso_superficiario_organismo", "STRING", aviso_superficiario_organismo),
            bigquery.ScalarQueryParameter("aviso_superficiario_contacto", "STRING", aviso_superficiario_contacto),
            bigquery.ScalarQueryParameter("medidas_inmediatas", "STRING", medidas_inmediatas),
            bigquery.ScalarQueryParameter("aprobador_apellido", "STRING", aprobador_apellido),
            bigquery.ScalarQueryParameter("aprobador_nombre", "STRING", aprobador_nombre),
            bigquery.ScalarQueryParameter(
                "fecha_hora_aprobacion", "TIMESTAMP",
                fecha_hora_aprobacion.isoformat() if fecha_hora_aprobacion else None,
            ),
        ]
    )

    bq_client.query(query, job_config=job_config).result()
    return mie_id, codigo


# ---------------------------------------------------------
# 5) Insertar registro de foto en tabla mie_fotos
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
        SELECT
            mie_id,
            codigo_mie,
            pozo,
            nombre_instalacion,
            estado,
            fecha_creacion_registro
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
                "volumen", "FLOAT64",
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
    fecha_fin_saneamiento: datetime,
    volumen_tierra_levantada: float | None,
    destino_tierra_impactada: str | None,
    volumen_liquido_recuperado: float | None,
    comentarios: str | None,
    aprobador_final_apellido: str | None,
    aprobador_final_nombre: str | None,
):
    tabla = f"{PROJECT_ID}.{DATASET_ID}.mie_eventos"

    query = f"""
        UPDATE `{tabla}`
        SET
          -- columnas nuevas
          rem_fecha_fin_saneamiento      = @fecha_fin,
          rem_volumen_tierra_levantada   = @vol_tierra,
          rem_destino_tierra_impactada   = @destino_tierra,
          rem_volumen_liquido_recuperado = @vol_liquido,
          rem_comentarios                = @comentarios,
          rem_aprobador_apellido         = @aprob_apellido,
          rem_aprobador_nombre           = @aprob_nombre,
          -- compatibilidad con columnas viejas (si existen)
          rem_fecha      = @fecha_fin,
          rem_responsable = CONCAT(
              COALESCE(@aprob_apellido, ''), ' ', COALESCE(@aprob_nombre, '')
          ),
          rem_detalle    = @comentarios,
          estado         = "CERRADO"
        WHERE mie_id = @mie_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "fecha_fin", "TIMESTAMP", fecha_fin_saneamiento.isoformat()
            ),
            bigquery.ScalarQueryParameter(
                "vol_tierra",
                "FLOAT64",
                float(volumen_tierra_levantada) if volumen_tierra_levantada is not None else None,
            ),
            bigquery.ScalarQueryParameter(
                "destino_tierra", "STRING", destino_tierra_impactada
            ),
            bigquery.ScalarQueryParameter(
                "vol_liquido",
                "FLOAT64",
                float(volumen_liquido_recuperado) if volumen_liquido_recuperado is not None else None,
            ),
            bigquery.ScalarQueryParameter(
                "comentarios", "STRING", comentarios
            ),
            bigquery.ScalarQueryParameter(
                "aprob_apellido", "STRING", aprobador_final_apellido
            ),
            bigquery.ScalarQueryParameter(
                "aprob_nombre", "STRING", aprobador_final_nombre
            ),
            bigquery.ScalarQueryParameter("mie_id", "INT64", mie_id),
        ]
    )

    bq_client.query(query, job_config=job_config).result()










