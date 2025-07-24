FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./

# Generar requirements.txt a partir del pyproject.toml
RUN uv pip compile pyproject.toml -o requirements.txt

# Instalar dependencias usando uv y el requirements.txt generado
RUN uv pip install --system --no-cache -r requirements.txt

# Instalar y configurar Playwright
RUN playwright install chromium --with-deps

# Copiar el código de la aplicación
COPY . .

# Instalar el paquete en modo desarrollo
RUN uv pip install --system -e .

# Exponer el puerto
EXPOSE 8080

# Configurar variable de entorno para el puerto
ENV PORT=8080

CMD ["python", "server.py"]