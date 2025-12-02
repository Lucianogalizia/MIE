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
            bigquery.SchemaField("volumen_estimado_m3", "FLOAT"),
            bigquery.SchemaField("causa_probable", "STRING"),
            bigquery.SchemaField("responsable", "STRING"),
            bigquery.SchemaField("observaciones", "STRING"),
            bigquery.SchemaField("estado", "STRING"),
            bigquery.SchemaField("creado_por", "STRING"),
            bigquery.SchemaField("fecha_hora_evento", "TIMESTAMP"),
            bigquery.SchemaField("fecha_creacion_registro", "TIMESTAMP"),
        ]
        tabla_eventos = bigquery.Table(tabla_eventos_ref, schema=schema_eventos)
        client.create_table(tabla_eventos)
        print("✅ Tabla mie_eventos creada")

    # 3) Tabla mie_fotos (fotos asociadas al MIE)
    tabla_fotos_ref = f"{dataset_ref}.mie_fotos"
    try:
        client.get_table(tabla_fotos_ref)
        print("✅ Tabla mie_fotos ya existe")
    except Exception:
        schema_fotos = [
            bigquery.SchemaField("id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("mie_id", "INT64", mode="REQUIRED"),
            bigquery.SchemaField("tipo", "STRING"),      # ANTES / DESPUES
            bigquery.SchemaField("url_foto", "STRING"),  # URL en el bucket
            bigquery.SchemaField("fecha_hora", "TIMESTAMP"),
        ]
        tabla_fotos = bigquery.Table(tabla_fotos_ref, schema=schema_fotos)
        client.create_table(tabla_fotos)
        print("✅ Tabla mie_fotos creada")


if __name__ == "__main__":
    crear_dataset_y_tablas()
