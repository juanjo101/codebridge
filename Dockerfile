FROM python:3.10-slim

# Evitar prompts interactivos durante apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Instalar paquetes del sistema requeridos
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv para gestionar dependencias
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

WORKDIR /app

# Copiar archivos de dependencias y readme
COPY pyproject.toml uv.lock* README.md README_EN.md ./

# Sincronizar dependencias
RUN uv sync --frozen || uv sync

# Copiar el resto del código
COPY . /app

# Exponer el puerto
EXPOSE 8787

# Comando para ejecutar la aplicación
CMD ["uv", "run", "codebridge", "serve"]
