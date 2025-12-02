# Imagen base oficial de Python
FROM python:3.11-slim

# Evitar archivos pyc e incrementar buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Carpeta dentro del contenedor donde vivirá la app
WORKDIR /app

# Copiamos primero las dependencias
COPY requirements.txt .

# Instalamos dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

# Streamlit: desactivar estadísticas y setear puerto
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV PORT=8080

# Comando que ejecuta la app en Cloud Run
CMD ["bash", "-c", "streamlit run app_mie.py --server.port $PORT --server.address 0.0.0.0"]
