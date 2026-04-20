FROM nginx:1.27-alpine

# Eliminar config default
RUN rm /etc/nginx/conf.d/default.conf

# Copiar nuestra config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos estáticos
COPY index.html /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

EXPOSE 80
