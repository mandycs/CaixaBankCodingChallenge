# Usamos una imagen base ligera de Python 3.10
FROM python:3.10-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos el cliente MySQL y otras dependencias necesarias
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el archivo de dependencias al contenedor
COPY requirements.txt .

# Instalamos las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de la aplicación al contenedor
COPY . .

# Copiamos el script de espera
COPY wait-for-mysql.sh /wait-for-mysql.sh
RUN chmod +x /wait-for-mysql.sh

# Establecemos variables de entorno necesarias para Flask
ENV FLASK_APP=app
ENV FLASK_ENV=production

# Exponemos el puerto en el que correrá la aplicación
EXPOSE 3000

# Comando para ejecutar la aplicación
CMD ["/wait-for-mysql.sh", "gunicorn", "--bind", "0.0.0.0:3000", "app:create_app()"]