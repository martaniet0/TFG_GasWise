# Usar una imagen base de Python 3.9
FROM python:3.9-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /

RUN apt-get update && apt-get install -y \
    libpq-dev gcc

# Copiar los archivos de requisitos y el proyecto al contenedor
COPY requirements.txt ./
COPY app ./app

# Instalar las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 4000
EXPOSE 4000

# Establecer el comando para iniciar la aplicación
CMD ["python", "./app/routes.py"]

