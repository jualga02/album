# =====================================================
# BACKEND - FastAPI + Gunicorn + SQLite
# Arquitectura: BBDD en disco local, medios en RAID 5
# =====================================================

# ===== ETAPA 1: Base con Python =====
FROM debian:bookworm-slim AS base

ENV DEBIAN_FRONTEND=noninteractive

# Instalar Python y herramientas básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd -m -r -u 1000 appuser

# ===== ETAPA 2: Dependencias de Python =====
FROM base AS dependencies

WORKDIR /app

# Copiar solo requirements.txt para aprovechar la caché de Docker
COPY requirements.txt .

# Crear entorno virtual e instalar dependencias
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# ===== ETAPA 3: Imagen final =====
FROM base AS final

# Copiar el entorno virtual
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# ====== RUTAS POR DEFECTO (se sobrescriben con variables de entorno) ======
# En desarrollo local: /app/data/db y /app/data/media
# En producción: /app/data/db (disco local) y /mnt/raid5/Album (RAID 5)
ENV DATABASE_PATH=/app/data/db/album.db \
    MEDIA_PATH=/app/data/media

WORKDIR /app

# Crear directorios internos (se sobrescribirán con volúmenes)
RUN mkdir -p /app/data/db /app/data/media /app/templates

# Copiar el código de la aplicación
COPY --chown=appuser:appuser . .

# Permisos para el usuario no-root
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Gunicorn con 1 worker (SQLite no soporta múltiples writers)
CMD ["gunicorn", "main:app", \
     "--workers", "1", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]