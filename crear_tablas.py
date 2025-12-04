# crear_tablas.py
from google.cloud import bigquery
from config import PROJECT_ID, DATASET_ID, REGION

client = bigquery.Client(project=PROJECT_ID)


def crear_dataset_y_tablas():
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"

    # 1) Dataset
    try:
        client.get_dataset(dataset_ref)
        print(f"✅ Dataset ya existe: {dataset_ref}")
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = REGION
        client.create_dataset(dataset)
        print(f"✅ Dataset creado: {dataset_ref}")

    # 2) Tabla mie_eventos (eventos de derrame)
    tabla_eventos_ref = f"{dataset_ref}.mie_eventos"
    try:
        client.get_table(tabla_eventos_ref)
        print("✅ Tabla mie_eventos ya existe")
    except Exception:
        schema_eventos = [
            bigquery.SchemaField("mie_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("codigo_mie", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("drm", "STRING"),
            bigquery.SchemaField("pozo", "STRING"),
            bigquery.SchemaField("locacion", "STRING"),
            bigquery.SchemaField("fluido", "STRING"),
            bigquery.SchemaField("volumen_estimado_m3", "FLOAT64"),
            bigquery.SchemaField("causa_probable", "STRING"),
            bigquery.SchemaField("responsable", "STRING"),
            bigquery.SchemaField("observaciones", "STRING"),
            bigquery.SchemaField("estado", "STRING"),
            bigquery.SchemaField("creado_por", "STRING"),
            bigquery.SchemaField("fecha_hora_evento", "TIMESTAMP"),
            bigquery.SchemaField("fecha_creacion_registro", "TIMESTAMP"),

            # 🔹 NUEVOS CAMPOS
            bigquery.SchemaField("observador_apellido", "STRING"),
            bigquery.SchemaField("observador_nombre", "STRING"),
            bigquery.SchemaField("responsable_inst_apellido", "STRING"),
            bigquery.SchemaField("responsable_inst_nombre", "STRING"),
            bigquery.SchemaField("yacimiento", "STRING"),
            bigquery.SchemaField("zona", "STRING"),
            bigquery.SchemaField("nombre_instalacion", "STRING"),
            bigquery.SchemaField("latitud", "STRING"),
            bigquery.SchemaField("longitud", "STRING"),

            bigquery.SchemaField("tipo_afectacion", "STRING"),
            bigquery.SchemaField("tipo_derrame", "STRING"),
            bigquery.SchemaField("tipo_instalacion", "STRING"),
            bigquery.SchemaField("causa_inmediata", "STRING"),

            bigquery.SchemaField("volumen_bruto_m3", "FLOAT64"),
            bigquery.SchemaField("volumen_gas_m3", "FLOAT64"),
            bigquery.SchemaField("ppm_agua", "STRING"),
            bigquery.SchemaField("volumen_crudo_m3", "FLOAT64"),
            bigquery.SchemaField("area_afectada_m2", "FLOAT64"),

            bigquery.SchemaField("recursos_afectados", "STRING"),
            bigquery.SchemaField("magnitud", "STRING"),

            bigquery.SchemaField("aviso_sen", "STRING"),
            bigquery.SchemaField("difusion_mediatica", "STRING"),

            bigquery.SchemaField("aviso_autoridad", "STRING"),
            bigquery.SchemaField("aviso_autoridad_fecha_hora", "TIMESTAMP"),
            bigquery.SchemaField("aviso_autoridad_emisor", "STRING"),
            bigquery.SchemaField("aviso_autoridad_medio", "STRING"),
            bigquery.SchemaField("aviso_autoridad_organismo", "STRING"),
            bigquery.SchemaField("aviso_autoridad_contacto", "STRING"),

            bigquery.SchemaField("aviso_superficiario", "STRING"),
            bigquery.SchemaField("aviso_superficiario_fecha_hora", "TIMESTAMP"),
            bigquery.SchemaField("aviso_superficiario_emisor", "STRING"),
            bigquery.SchemaField("aviso_superficiario_medio", "STRING"),
            bigquery.SchemaField("aviso_superficiario_organismo", "STRING"),
            bigquery.SchemaField("aviso_superficiario_contacto", "STRING"),

            bigquery.SchemaField("medidas_inmediatas", "STRING"),

            bigquery.SchemaField("aprobador_apellido", "STRING"),
            bigquery.SchemaField("aprobador_nombre", "STRING"),
            bigquery.SchemaField("fecha_hora_aprobacion", "TIMESTAMP"),
        ]
        tabla_eventos = bigquery.Table(tabla_eventos_ref, schema=schema_eventos)
        client.create_table(tabla_eventos)
        print("✅ Tabla mie_eventos creada")

    # 3) Tabla mie_fotos (igual que antes)
    tabla_fotos_ref = f"{dataset_ref}.mie_fotos"
    try:
        client.get_table(tabla_fotos_ref)
        print("✅ Tabla mie_fotos ya existe")
    except Exception:
        schema_fotos = [
            bigquery.SchemaField("id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("mie_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("tipo", "STRING"),
            bigquery.SchemaField("url_foto", "STRING"),
            bigquery.SchemaField("fecha_hora", "TIMESTAMP"),
        ]
        tabla_fotos = bigquery.Table(tabla_fotos_ref, schema=schema_fotos)
        client.create_table(tabla_fotos)
        print("✅ Tabla mie_fotos creada")


if __name__ == "__main__":
    crear_dataset_y_tablas()


