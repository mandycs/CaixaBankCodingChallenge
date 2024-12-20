# Dockerfile
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo requirements.txt
COPY requirements.txt ./

# Instala los paquetes necesarios para mysqlclient y otras dependencias
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc pkg-config default-libmysqlclient-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copia los archivos de la aplicación
COPY . .

# Copia el script wait-for-it.sh y le da permisos de ejecución
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Define el comando CMD con wait-for-it para asegurarse de que MySQL esté listo antes de ejecutar Django
CMD ["sh", "-c", "/wait-for-it.sh mysql:3306 -t 30 -- python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
