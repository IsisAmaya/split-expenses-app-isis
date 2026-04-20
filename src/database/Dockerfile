FROM postgres:16-alpine

# Scripts de inicialización se ejecutan al crear el volumen por primera vez
COPY init/ /docker-entrypoint-initdb.d/

EXPOSE 5432
